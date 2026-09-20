"""Offline Terraform state inspection. An AMI identifier alone never proves AL2."""

from __future__ import annotations

import re

from .artifacts import emit_report, read_json
from .scan import classify_ami

AMI = re.compile(r"ami-(?:[0-9a-f]{8}|[0-9a-f]{17})\Z")
SOURCE = "https://developer.hashicorp.com/terraform/internals/json-format"


def catalog_entries(document):
    if not isinstance(document, list):
        raise ValueError("AMI catalog must be a list of region/ami_id/description objects")
    catalog = {}
    for item in document:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(k), str) and item[k] for k in ("region", "ami_id", "description")
        ):
            raise ValueError("AMI catalog entries require region, ami_id and description strings")
        if not AMI.fullmatch(item["ami_id"]):
            raise ValueError("Invalid AMI identifier in catalog")
        key = (item["region"], item["ami_id"])
        if key in catalog and catalog[key] != item["description"]:
            raise ValueError("Conflicting AMI descriptions in catalog")
        catalog[key] = item["description"]
    return catalog


def ami_platform(ami_id, region, catalog):
    description = catalog.get((region, ami_id), catalog.get(("*", ami_id)))
    return classify_ami(description), (
        "supplied-ami-description" if description else "unresolved-ami-id"
    )


def resources(document):
    if not isinstance(document, dict):
        raise ValueError("State must be a JSON object")
    format_version = document.get("format_version", "")
    if isinstance(format_version, str) and format_version.startswith("1.") and "values" in document:
        if not isinstance(document["values"], dict):
            raise ValueError("Terraform state values must be an object")
        root = document["values"].get("root_module", {})

        def modules(module, depth=0):
            if depth > 64:
                raise ValueError("Terraform module nesting exceeds the 64-level bound")
            if (
                not isinstance(module, dict)
                or not isinstance(module.get("resources", []), list)
                or not isinstance(module.get("child_modules", []), list)
            ):
                raise ValueError("Terraform module must contain resource and child-module lists")
            for resource in module.get("resources", []):
                if not isinstance(resource, dict):
                    raise ValueError("Terraform resource must be an object")
                yield resource
            for child in module.get("child_modules", []):
                yield from modules(child, depth + 1)

        for resource in modules(root):
            address, kind = resource.get("address"), resource.get("type")
            if (
                not isinstance(address, str)
                or not address
                or len(address) > 4096
                or not isinstance(kind, str)
            ):
                raise ValueError(
                    "Terraform resource requires a type and an address of at most 4096 characters"
                )
            values = resource.get("values", {})
            if not isinstance(values, dict):
                raise ValueError("Terraform resource values must be an object")
            yield address, resource.get("mode", "managed"), kind, values
    elif document.get("version") == 4 and isinstance(document.get("resources"), list):
        for resource in document["resources"]:
            if not isinstance(resource, dict) or not all(
                isinstance(resource.get(key), str) and resource[key] for key in ("type", "name")
            ):
                raise ValueError("Raw state resources require type and name strings")
            if not isinstance(resource.get("module", ""), str) or not isinstance(
                resource.get("instances", []), list
            ):
                raise ValueError(
                    "Raw state resource requires a module string and an instances list"
                )
            address = ".".join(
                filter(None, [resource.get("module"), resource["type"], resource["name"]])
            )
            if len(address) > 4096:
                raise ValueError("Terraform resource address exceeds 4096 characters")
            for instance in resource.get("instances", []):
                if not isinstance(instance, dict) or not isinstance(
                    instance.get("attributes", {}), dict
                ):
                    raise ValueError("Raw state instance and attributes must be objects")
                suffix = ""
                if "index_key" in instance:
                    from json import dumps

                    if not isinstance(instance["index_key"], (str, int)) or isinstance(
                        instance["index_key"], bool
                    ):
                        raise ValueError("Terraform instance index must be a string or integer")
                    suffix = "[" + dumps(instance["index_key"], ensure_ascii=False) + "]"
                    if len(address + suffix) > 4096:
                        raise ValueError("Indexed Terraform address exceeds 4096 characters")
                yield address + suffix, resource.get("mode", "managed"), resource[
                    "type"
                ], instance.get("attributes", {})
    else:
        raise ValueError(
            "Expected Terraform raw state version 4 or terraform show -json state format 1.x; plans are not state"
        )


PROVIDER_ATTRIBUTES = {
    "aws_instance": "ami",
    "aws_launch_template": "image_id",
    "aws_launch_configuration": "image_id",
    "aws_eks_node_group": "ami_type",
}


def scan_state(document, catalog=None, region=""):
    catalog = dict(catalog or {})
    local_metadata = set()
    inventory = list(resources(document))
    for _, mode, _, values in inventory:
        if not isinstance(mode, str) or mode not in {"managed", "data"}:
            raise ValueError("Terraform resource mode must be managed or data")
        if not isinstance(values.get("region", region), str):
            raise ValueError("Terraform resource region must be a string")
    # Explicit aws_ami data-source metadata can resolve IDs without a network call.
    for _, mode, kind, values in inventory:
        if mode == "data" and kind == "aws_ami" and AMI.fullmatch(str(values.get("id", ""))):
            if not all(isinstance(values.get(key, ""), str) for key in ("name", "description")):
                raise ValueError("AMI data-source names and descriptions must be strings")
            description = " ".join(values.get(key, "") for key in ("name", "description")).strip()
            key = (values.get("region", region), values["id"])
            if description and key[0]:
                if key in catalog and catalog[key] != description:
                    raise ValueError("State AMI metadata conflicts with supplied catalog")
                catalog[key] = description
                local_metadata.add(key)
    findings = []
    unresolved_resources = []
    examined = 0
    for address, mode, kind, values in inventory:
        if mode != "managed" or kind not in {
            "aws_instance",
            "aws_launch_template",
            "aws_launch_configuration",
            "aws_eks_node_group",
        }:
            continue
        examined += 1
        attribute = PROVIDER_ATTRIBUTES[kind]
        value = values.get(attribute)
        if value is not None and not isinstance(value, str):
            raise ValueError("Terraform AMI attributes must be strings or null")
        # Only documented provider attributes are deployment evidence. Tags,
        # user_data and arbitrary nested maps must never produce AMI findings.
        if isinstance(value, str) and (attribute == "ami_type" or AMI.fullmatch(value)):
            pointer = "/" + attribute
            resource_region = values.get("region", region)
            if pointer.endswith("/ami_type"):
                platform = (
                    "al2"
                    if value.startswith("AL2_")
                    else "al2023" if value.startswith("AL2023_") else "unknown"
                )
                evidence = "terraform-ami-type"
            else:
                platform, evidence = ami_platform(value, resource_region, catalog)
                if (resource_region, value) in local_metadata:
                    evidence = "state-ami-description"
            findings.append(
                {
                    "address": address,
                    "attribute": pointer,
                    "value": value,
                    "region": resource_region,
                    "platform": platform,
                    "evidence": evidence,
                }
            )
        else:
            unresolved_resources.append(
                {
                    "address": address,
                    "attribute": "/" + attribute,
                    "reason": "Provider attribute is absent, null or not a resolved AMI identifier",
                }
            )
    return {
        "schema_version": 1,
        "source": "terraform-state",
        "resources_examined": examined,
        "findings": sorted(
            findings, key=lambda item: (item["address"], item["attribute"], item["value"])
        ),
        "unresolved_resources": sorted(unresolved_resources, key=lambda item: item["address"]),
        "limitations": [
            "Only managed EC2 instances, launch templates/configurations and EKS node groups are examined.",
            "AMI IDs without supplied or state-local image descriptions remain unknown; no AWS APIs are called.",
            "Outputs and unrelated state values are excluded; state may contain secrets and should remain private.",
        ],
        "reference": SOURCE,
    }


def run(args):
    catalog = catalog_entries(read_json(args.ami_catalog)) if args.ami_catalog else {}
    report = scan_state(read_json(args.path), catalog, args.region)
    emit_report(report, args.out)
    return int(
        args.strict
        and bool(
            report["unresolved_resources"]
            or any(item["platform"] in {"al2", "al1", "unknown"} for item in report["findings"])
        )
    )
