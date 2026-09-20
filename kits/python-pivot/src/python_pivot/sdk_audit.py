"""Compare statically identified boto3 calls with explicit botocore service models.

No SDK client is constructed. Removed APIs are reported only when present in a
supplied baseline and absent from the target; otherwise they are unavailable.
"""

from __future__ import annotations

import ast
import gzip
import json
import re
from pathlib import Path

from .compat import MAX_INPUT, emit, finding, read_bytes, report

SOURCE = "https://docs.aws.amazon.com/botocore/latest/reference/loaders.html"
MAX_FILES = 1000
MAX_SOURCE = 1024 * 1024


def snake(value: str) -> str:
    return re.sub(
        r"([a-z0-9])([A-Z])", r"\1_\2", re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    ).lower()


class Models:
    def __init__(self, root: Path):
        if root.is_symlink() or not root.is_dir():
            raise ValueError("model root must be a non-symlink directory")
        self.root = root.resolve()
        self.cache: dict[tuple[str, str | None], dict | None] = {}

    def load(self, service: str, version: str | None) -> dict | None:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,79}", service):
            raise ValueError("service name must be an AWS SDK service identifier")
        if version is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", version):
            raise ValueError("api_version must be a literal YYYY-MM-DD")
        key = (service, version)
        if key in self.cache:
            return self.cache[key]
        folder = self.root / service
        if folder.is_symlink():
            raise ValueError("model directories must not be symlinks")
        if not folder.is_dir():
            self.cache[key] = None
            return None
        versions = sorted(
            item.name
            for item in folder.iterdir()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", item.name) and item.is_dir()
        )
        chosen = version or (versions[-1] if versions else None)
        if chosen not in versions:
            self.cache[key] = None
            return None
        directory = folder / str(chosen)
        if directory.is_symlink():
            raise ValueError("model version directory must not be a symlink")
        path = directory / "service-2.json"
        if not path.exists():
            path = directory / "service-2.json.gz"
        raw = read_bytes(path)
        if path.suffix == ".gz":
            import io

            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                raw = stream.read(MAX_INPUT + 1)
            if len(raw) > MAX_INPUT:
                raise ValueError("expanded service model exceeds input limit")
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("operations"), dict)
            or not isinstance(value.get("shapes"), dict)
            or not isinstance(value.get("metadata"), dict)
            or value["metadata"].get("apiVersion") != chosen
        ):
            raise ValueError(
                "model must contain operations, shapes and matching metadata.apiVersion"
            )
        if any(not isinstance(item, dict) for item in value["operations"].values()) or any(
            not isinstance(item, dict) for item in value["shapes"].values()
        ):
            raise ValueError("model operations and shapes must be objects")
        self.cache[key] = value
        return value


def _operation(model: dict | None, name: str) -> dict | None:
    if model is None:
        return None
    return next((op for api, op in model["operations"].items() if snake(api) == name), None)


def _members(model: dict | None, operation: dict | None) -> dict:
    if not model or not operation:
        return {}
    shape = operation.get("input", {}).get("shape")
    value = model["shapes"].get(shape, {}).get("members", {})
    if not isinstance(value, dict) or any(
        not isinstance(member, dict) for member in value.values()
    ):
        raise ValueError("operation input members must be objects")
    return value


def bound_names(node: ast.AST) -> set[str]:
    """Conservative binding inventory, including aliases and exception targets."""
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
            names.add(child.id)
        elif isinstance(child, ast.Import):
            names.update(item.asname or item.name.split(".")[0] for item in child.names)
        elif isinstance(child, ast.ImportFrom):
            names.update(item.asname or item.name for item in child.names)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            names.add(child.name)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(child.name)
    return names


class Calls(ast.NodeVisitor):
    def __init__(self, path: str, target: Models, baseline: Models | None):
        self.path = path
        self.target = target
        self.baseline = baseline
        self.bindings: dict[str, tuple] = {}
        self.findings: list[dict] = []
        self.clients = 0
        self.calls = 0

    def add(self, code: str, node: ast.AST, message: str, review: bool = False) -> None:
        self.findings.append(
            finding(
                code,
                f"{self.path}:{getattr(node, 'lineno', 1)}",
                message,
                SOURCE,
                "review" if review else "high",
            )
        )

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            name = item.asname or item.name.split(".")[0]
            self.bindings.pop(name, None)
            if item.name == "boto3":
                self.bindings[name] = ("module",)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for item in node.names:
            name = item.asname or item.name
            self.bindings.pop(name, None)
            if (
                node.level == 0
                and node.module in ("boto3", "boto3.session")
                and item.name in ("client", "Session", "resource")
            ):
                self.bindings[name] = (item.name,)

    def binding(self, node: ast.AST) -> tuple | None:
        if isinstance(node, ast.Name):
            return self.bindings.get(node.id)
        if isinstance(node, ast.Attribute):
            parent = self.binding(node.value)
            if parent and parent[0] == "module" and node.attr in ("client", "Session"):
                return (node.attr,)
            if parent and parent[0] == "session" and node.attr == "client":
                return ("client",)
        if isinstance(node, ast.Call):
            constructor = self.binding(node.func)
            if constructor == ("Session",):
                return ("session",)
            if constructor == ("client",):
                service = (
                    node.args[0]
                    if node.args
                    else next((kw.value for kw in node.keywords if kw.arg == "service_name"), None)
                )
                version = (
                    node.args[2]
                    if len(node.args) > 2
                    else next((kw.value for kw in node.keywords if kw.arg == "api_version"), None)
                )
                if not isinstance(service, ast.Constant) or not isinstance(service.value, str):
                    return ("dynamic-client",)
                if version is not None and not (
                    isinstance(version, ast.Constant)
                    and isinstance(version.value, (str, type(None)))
                ):
                    return ("dynamic-client",)
                return (
                    "bound-client",
                    service.value,
                    version.value if isinstance(version, ast.Constant) else None,
                )
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        value = self.binding(node.value)
        self.visit(node.value)
        for target in node.targets:
            for child in ast.walk(target):
                if isinstance(child, ast.Name):
                    self.bindings.pop(child.id, None)
                    if isinstance(target, ast.Name) and value:
                        self.bindings[child.id] = value

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        value = self.binding(node.value) if node.value else None
        if node.value:
            self.visit(node.value)
        if isinstance(node.target, ast.Name):
            self.bindings.pop(node.target.id, None)
            if value:
                self.bindings[node.target.id] = value

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        outer = self.bindings
        self.bindings = outer.copy()
        # Python locals shadow module bindings throughout a function, including
        # before an assignment. Avoid confusing independent clients/scopes.
        for name in bound_names(node):
            self.bindings.pop(name, None)
        for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            self.bindings.pop(arg.arg, None)
        for variadic in (node.args.vararg, node.args.kwarg):
            if variadic:
                self.bindings.pop(variadic.arg, None)
        for statement in node.body:
            self.visit(statement)
        self.bindings = outer
        self.bindings.pop(node.name, None)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        outer = self.bindings
        self.bindings = outer.copy()
        for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            self.bindings.pop(arg.arg, None)
        for variadic in (node.args.vararg, node.args.kwarg):
            if variadic:
                self.bindings.pop(variadic.arg, None)
        self.visit(node.body)
        self.bindings = outer

    def visit_ListComp(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
    ) -> None:
        outer = self.bindings
        changed = {name for generator in node.generators for name in bound_names(generator.target)}
        if changed & outer.keys():
            self.add(
                "sdk-binding-control-flow",
                node,
                "A comprehension target shadows an SDK binding; its ambiguous uses require manual review.",
                True,
            )
        self.bindings = {name: value for name, value in outer.items() if name not in changed}
        for generator in node.generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)
        self.bindings = outer

    visit_SetComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp
    visit_DictComp = visit_ListComp

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        value = self.binding(node.value)
        self.visit(node.value)
        self.bindings.pop(node.target.id, None)
        if value:
            self.bindings[node.target.id] = value

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        outer = self.bindings
        self.bindings = outer.copy()
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                namespace = self.bindings
                self.bindings = outer.copy()
                self.visit(statement)
                self.bindings = namespace
            else:
                self.visit(statement)
        self.bindings = outer
        self.bindings.pop(node.name, None)

    def visit_If(self, node: ast.If) -> None:
        outer = self.bindings.copy()
        self.visit(node.test)
        for statements in (node.body, node.orelse):
            self.bindings = outer.copy()
            for statement in statements:
                self.visit(statement)
        self.bindings = outer
        changed = bound_names(node)
        if changed & outer.keys():
            self.add(
                "sdk-binding-control-flow",
                node,
                "Conditional assignment changes an SDK binding; uses after this block require manual review.",
                True,
            )
        for name in changed:
            self.bindings.pop(name, None)

    def control_flow(self, node: ast.AST, branches: list[list[ast.stmt]]) -> None:
        changed = bound_names(node)
        outer = self.bindings.copy()
        if changed & outer.keys():
            self.add(
                "sdk-binding-control-flow",
                node,
                "Control flow or a context target can replace an SDK binding; ambiguous uses are not treated as AWS operations.",
                True,
            )
        safe = {name: value for name, value in outer.items() if name not in changed}
        for branch in branches:
            self.bindings = safe.copy()
            for statement in branch:
                self.visit(statement)
        self.bindings = safe

    def visit_For(self, node: ast.For | ast.AsyncFor) -> None:
        self.visit(node.iter)
        self.control_flow(node, [node.body, node.orelse])

    visit_AsyncFor = visit_For

    def visit_While(self, node: ast.While) -> None:
        self.visit(node.test)
        self.control_flow(node, [node.body, node.orelse])

    def visit_With(self, node: ast.With | ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
        self.control_flow(node, [node.body])

    visit_AsyncWith = visit_With

    def visit_Try(self, node: ast.Try) -> None:
        self.control_flow(
            node,
            [node.body, *(handler.body for handler in node.handlers), node.orelse, node.finalbody],
        )

    def visit_Delete(self, node: ast.Delete) -> None:
        for name in bound_names(node):
            self.bindings.pop(name, None)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.value)
        for name in bound_names(node.target):
            self.bindings.pop(name, None)

    def visit_Call(self, node: ast.Call) -> None:
        if self.binding(node.func) == ("resource",):
            self.add(
                "sdk-resource-unresolved",
                node,
                "Boto3 resource actions are not direct service-model operations; review them separately.",
                True,
            )
        constructed = self.binding(node)
        if constructed and constructed[0] in ("bound-client", "dynamic-client"):
            self.clients += 1
            if constructed[0] == "dynamic-client":
                self.add(
                    "dynamic-sdk-client",
                    node,
                    "Dynamic service name or api_version requires manual review.",
                    True,
                )
            elif self.target.load(constructed[1], constructed[2]) is None:
                baseline = (
                    self.baseline.load(constructed[1], constructed[2]) if self.baseline else None
                )
                self.add(
                    "api-version-removed" if baseline else "api-version-unavailable",
                    node,
                    f"{constructed[1]} api_version={constructed[2] or 'latest'} is absent from the target model set."
                    + (
                        " It exists in the supplied baseline."
                        if baseline
                        else " Absence alone does not prove AWS retired the service."
                    ),
                )
        if isinstance(node.func, ast.Attribute):
            client = self.binding(node.func.value)
            if client and client[0] == "bound-client":
                self.inspect_call(node, client)
            elif client and client[0] in ("module", "session") and node.func.attr == "resource":
                self.add(
                    "sdk-resource-unresolved",
                    node,
                    "Boto3 resource actions are not direct service-model operations; review them separately.",
                    True,
                )
        self.generic_visit(node)

    def inspect_call(self, node: ast.Call, client: tuple) -> None:
        self.calls += 1
        model = self.target.load(client[1], client[2])
        if model is None:
            return
        assert isinstance(node.func, ast.Attribute)
        name = node.func.attr
        baseline = self.baseline.load(client[1], client[2]) if self.baseline else None
        before = _operation(baseline, name)
        operation = _operation(model, name)
        if operation is None:
            self.add(
                "operation-removed" if before is not None else "operation-unmodeled",
                node,
                f"{client[1]}.{name} is not an operation in the target model."
                + (
                    " It exists in the baseline."
                    if before is not None
                    else " SDK helpers, paginators and customizations need manual review."
                ),
                before is None,
            )
            return
        if operation.get("deprecated"):
            self.add(
                "operation-deprecated", node, f"Target model marks {client[1]}.{name} deprecated."
            )
        members = _members(model, operation)
        previous = _members(baseline, before)
        if node.args:
            self.add(
                "positional-sdk-arguments",
                node,
                "Operation positional arguments are outside this scanner's supported keyword-call form.",
                True,
            )
        for keyword in node.keywords:
            if keyword.arg is None:
                self.add(
                    "dynamic-sdk-parameters",
                    node,
                    "Expanded **kwargs cannot be checked statically.",
                    True,
                )
                continue
            key = keyword.arg
            member = members.get(key)
            if member is None:
                self.add(
                    "parameter-removed" if key in previous else "parameter-unavailable",
                    keyword,
                    f"Parameter {key} is absent from {client[1]}.{name} target input."
                    + (
                        " It exists in the baseline."
                        if key in previous
                        else " Check custom SDK behavior and spelling."
                    ),
                )
            elif member.get("deprecated") or model["shapes"].get(member.get("shape"), {}).get(
                "deprecated"
            ):
                self.add(
                    "parameter-deprecated",
                    keyword,
                    f"Target model marks {client[1]}.{name} parameter {key} deprecated.",
                )


def scan(path: Path, target: Models, baseline: Models | None = None) -> dict:
    if path.is_symlink() or not path.exists():
        raise ValueError("source path must exist and must not be a symlink")
    files = [path] if path.is_file() else sorted(path.rglob("*.py"))
    if not files or len(files) > MAX_FILES:
        raise ValueError(f"source input must contain 1..{MAX_FILES} Python files")
    root = path.parent.resolve() if path.is_file() else path.resolve()
    findings = []
    clients = calls = 0
    for source in files:
        if source.suffix != ".py" or not source.resolve().is_relative_to(root):
            raise ValueError("source must be Python files within the selected directory")
        text = read_bytes(source, MAX_SOURCE).decode("utf-8-sig")
        label = source.relative_to(path).as_posix() if path.is_dir() else path.name
        tree = ast.parse(text, filename=label)
        visitor = Calls(label, target, baseline)
        visitor.visit(tree)
        findings.extend(visitor.findings)
        clients += visitor.clients
        calls += visitor.calls
    return report(
        "boto3",
        findings,
        files=len(files),
        clients=clients,
        calls=calls,
        baseline_supplied=baseline is not None,
        limitations="Literal boto3.client/Session client bindings and direct keyword operation calls. No code executes and no AWS requests occur. Dynamic bindings, resources, nested parameter dictionaries, paginators, SDK customizations and runtime values are not resolved. Model absence means SDK availability, not proof AWS retired a service.",
    )


def run(args) -> int:
    if args.installed_models:
        try:
            import botocore
        except ImportError as exc:
            raise ValueError("--installed-models requires python-pivot[aws]") from exc
        root = Path(botocore.__file__).parent / "data"
    else:
        root = Path(args.models)
    result = scan(
        Path(args.path),
        Models(root),
        Models(Path(args.baseline_models)) if args.baseline_models else None,
    )
    return emit(result, args)
