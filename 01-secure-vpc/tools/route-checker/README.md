# Read-only VPC route checker

Python 3.10+, standard library only. The checker reads a saved EC2
`describe-route-tables` JSON response. It has no SDK, network calls, credentials,
resource mutations or file writes. It is an AI-assisted component of this portfolio lab.

From this directory:

```sh
python3 check_routes.py fixtures/good.json --vpc-id vpc-synthetic
python3 check_routes.py fixtures/bad-database-route.json --vpc-id vpc-synthetic
python3 -m unittest -v
```

| Result | Exit | Meaning |
|---|---:|---|
| Good fixture | 0 | Five tagged tables match the selected policy |
| Bad database fixture | 1 | Database has unexpected non-local/default route |
| Invalid JSON/schema or unreadable file | 2 | Input could not be checked reliably |

Fixture identifiers are synthetic. A database NAT route violates local-only
policy; it does not establish public inbound reachability. The correction is to
remove the unintended route from a disposable fixture, or use the reviewed IaC
workflow for an authorized real remediation, then export/recheck. Never treat a
nonzero exit as permission to mutate AWS.

## Policy

- One public table: active `10.0.0.0/16` local route and IPv4 default to an IGW.
- Two application tables: local-only by default; `--nat-enabled` requires an
  active IPv4 NAT default in each application table.
- Two database tables: local-only in both modes.
- Reject non-local routes outside that policy, including IPv6 and prefix lists,
  inactive routes, missing/duplicate managed tables and incomplete pagination.
- Reject ambiguous destinations, duplicate Tier tags and malformed input types.

Table selection trusts `Tier` tags and the specified VPC ID. Main/untagged tables
and other VPCs are ignored. Expected counts still have to match. This is a fixed
project policy, not a general-purpose VPC analyzer. The CLI accepts UTF-8 with or
without BOM for Windows exports. Tests cover NAT-on/off policy, blackholes,
missing routes, more-specific routes, malformed data and real process exit codes.

## Optional live export (not performed in this audit)

Use temporary credentials with only the required read permission
`ec2:DescribeRouteTables`. Confirm account, region and VPC first. Keep the result
in the ignored repository-root `.private/` directory or outside the repository.
From repository root in PowerShell:

```powershell
New-Item -ItemType Directory -Force .private | Out-Null
aws ec2 describe-route-tables --region YOUR_REGION --filters Name=vpc-id,Values=YOUR_VPC_ID --output json | Out-File -Encoding utf8 .private/routes-private.json
# Check the AWS CLI exit status before using the export.
python 01-secure-vpc/tools/route-checker/check_routes.py .private/routes-private.json --vpc-id YOUR_VPC_ID
```

Use the complete CLI response; do not use `--no-paginate` or a partial selection.
Add `--nat-enabled` only for an intentionally NAT-enabled deployment. A failed
export must not be mistaken for a current snapshot. Real snapshots disclose
account/topology metadata; do not commit them.

## Limits and evidence

The checker does not verify subnet associations, gateway ownership/AZ placement,
gateway health, SGs/NACLs, packet flow, availability, cleanup or snapshot freshness.
Those require separate evidence. Offline Terraform tests cover source-level
association/NAT wiring, not deployed AWS wiring. The 20-test suite and reproducible
commands are described in [verification](../../docs/verification.md).

[AWS CLI describe-route-tables](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-route-tables.html)
