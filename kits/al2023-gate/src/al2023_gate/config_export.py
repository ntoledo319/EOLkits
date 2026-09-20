"""Read-only AWS Config aggregator inventory and rule-evaluation export."""

from __future__ import annotations

import json
import re

from .artifacts import emit_report, read_json
from .state import ami_platform, catalog_entries

EXPRESSION = (
    "SELECT resourceId, resourceType, accountId, awsRegion, configuration.imageId "
    "WHERE resourceType = 'AWS::EC2::Instance'"
)
REFERENCE = (
    "https://docs.aws.amazon.com/config/latest/APIReference/API_SelectAggregateResourceConfig.html"
)


def pages(client, method, key, **arguments):
    """Bound pagination and fail if an upstream repeats a continuation token."""
    seen = set()
    for _ in range(10000):
        response = getattr(client, method)(**arguments)
        values = response.get(key)
        if not isinstance(values, list):
            raise ValueError("Malformed AWS Config response: missing result list")
        yield from values
        token = response.get("NextToken")
        if not token:
            return
        if token in seen:
            raise ValueError("AWS Config pagination repeated a token; refusing incomplete export")
        seen.add(token)
        arguments["NextToken"] = token
    raise ValueError("AWS Config pagination exceeded 10000 pages")


def collect(client, aggregator, rule=None):
    records = [
        json.loads(row)
        for row in pages(
            client,
            "select_aggregate_resource_config",
            "Results",
            ConfigurationAggregatorName=aggregator,
            Expression=EXPRESSION,
            Limit=100,
        )
    ]
    evaluations = []
    if rule:
        summaries = pages(
            client,
            "describe_aggregate_compliance_by_config_rules",
            "AggregateComplianceByConfigRules",
            ConfigurationAggregatorName=aggregator,
            Filters={"ConfigRuleName": rule},
            Limit=100,
        )
        for summary in summaries:
            for evaluation in pages(
                client,
                "get_aggregate_compliance_details_by_config_rule",
                "AggregateEvaluationResults",
                ConfigurationAggregatorName=aggregator,
                ConfigRuleName=summary["ConfigRuleName"],
                AccountId=summary["AccountId"],
                AwsRegion=summary["AwsRegion"],
                ComplianceType="NON_COMPLIANT",
                Limit=100,
            ):
                qualifier = evaluation["EvaluationResultIdentifier"]["EvaluationResultQualifier"]
                evaluations.append(
                    {
                        "rule": summary["ConfigRuleName"],
                        "account_id": summary["AccountId"],
                        "region": summary["AwsRegion"],
                        "resource_id": qualifier["ResourceId"],
                        "resource_type": qualifier["ResourceType"],
                        "compliance": evaluation["ComplianceType"],
                    }
                )
    return {"resources": records, "evaluations": evaluations}


def report_export(export, catalog=None):
    if (
        not isinstance(export, dict)
        or not isinstance(export.get("resources"), list)
        or not isinstance(export.get("evaluations", []), list)
    ):
        raise ValueError("Config fixture requires resources and optional evaluations lists")
    findings = []
    for record in export["resources"]:
        if not isinstance(record, dict) or not all(
            isinstance(record.get(key), str) and record[key]
            for key in ("resourceId", "resourceType", "accountId", "awsRegion")
        ):
            raise ValueError(
                "Config resource requires resourceId, resourceType, accountId and awsRegion strings"
            )
        if record.get("resourceType") != "AWS::EC2::Instance":
            raise ValueError("Config resource export supports AWS::EC2::Instance only")
        configuration = record.get("configuration", {})
        if not isinstance(configuration, dict):
            raise ValueError("Config resource configuration must be an object")
        ami = configuration.get("imageId") or record.get("configuration.imageId") or ""
        if not isinstance(ami, str):
            raise ValueError("Config imageId must be a string")
        region = record["awsRegion"]
        platform, evidence = ami_platform(ami, region, catalog or {})
        findings.append(
            {
                "resource_id": record["resourceId"],
                "resource_type": record["resourceType"],
                "account_id": record["accountId"],
                "region": region,
                "ami_id": ami,
                "platform": platform,
                "evidence": evidence,
            }
        )
    evaluations = []
    for item in export.get("evaluations", []):
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), str) and item[key]
            for key in (
                "rule",
                "account_id",
                "region",
                "resource_id",
                "resource_type",
                "compliance",
            )
        ):
            raise ValueError("Config evaluation requires nonempty identity and compliance strings")
        if item["compliance"] != "NON_COMPLIANT":
            raise ValueError("Only NON_COMPLIANT rule evaluations belong in this export")
        # Exclude raw annotations and arbitrary service fields from public reports.
        evaluations.append(
            {
                key: item[key]
                for key in (
                    "rule",
                    "account_id",
                    "region",
                    "resource_id",
                    "resource_type",
                    "compliance",
                )
            }
        )
    return {
        "schema_version": 1,
        "source": "aws-config-aggregator",
        "read_only": True,
        "findings": sorted(
            findings, key=lambda item: (item["account_id"], item["region"], item["resource_id"])
        ),
        "noncompliant_rule_evaluations": sorted(
            evaluations, key=lambda item: tuple(str(item[k]) for k in sorted(item))
        ),
        "limitations": [
            "Coverage is limited to recorded EC2 instances visible in the existing aggregator; missing or stale records are not proof of compliance.",
            "AMI IDs require an explicit region-scoped catalog to identify AL2. Rule noncompliance alone does not establish an OS.",
            "No Config recorder, aggregator, rule, or resource is created or changed.",
        ],
        "reference": REFERENCE,
    }


def run(args):
    if args.fixture:
        export = read_json(args.fixture)
    else:
        if (
            not args.aggregator
            or not args.region
            or not re.fullmatch(r"[\w-]{1,256}", args.aggregator)
        ):
            raise ValueError("--live requires an existing --aggregator and its --region")
        try:
            import boto3
        except ImportError as error:
            raise ValueError(
                "Live export requires the optional aws extra: pip install 'al2023-gate[aws]'"
            ) from error
        client = boto3.Session(profile_name=args.profile).client("config", region_name=args.region)
        export = collect(client, args.aggregator, args.rule)
    catalog = catalog_entries(read_json(args.ami_catalog)) if args.ami_catalog else {}
    report = report_export(export, catalog)
    emit_report(report, args.out)
    return int(
        bool(
            args.strict
            and (
                report["noncompliant_rule_evaluations"]
                or any(item["platform"] in {"al1", "al2", "unknown"} for item in report["findings"])
            )
        )
    )
