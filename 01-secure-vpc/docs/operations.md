# Security and operation of the bounded network lab

## Implemented boundaries

Routing and public-IP assignment are configured, but no application access policy
is enforced. Every tier retains a VPC-local route. AWS-created default NACLs
initially allow traffic; no custom NACL or workload security group is defined.
Do not attach real workloads or sensitive data and call them protected by these
subnets alone. The default security group is not a designed tier policy.

Public subnet auto-assignment is intentionally retained from the existing design.
An eligible future launch could receive a public IPv4 address, incur address cost
and become reachable if its other controls allow it. Private tiers disable that
setting. An IGW route alone does not provide a private-addressed instance an
internet path. NAT allows suitable outbound connections and their responses;
a database NAT route is a policy failure, not proof of public inbound exposure.
IPv6, peering, transit gateways and endpoint routes are outside this fixed policy.

## Least privilege and sensitive data

- CI needs only GitHub `contents: read`; action versions are pinned, checkout
  credentials are not persisted, and AWS credentials/OIDC are absent.
- The checker itself needs **no IAM permission**. It reads a file and has no
  network client or mutation operation.
- Optional snapshot collection needs `ec2:DescribeRouteTables`. That describe
  action requires wildcard resource scope; scope the role/session by permitted
  region and account context where supported. Do not grant write actions for
  collection. Inventory may additionally require `DescribeVpcs`,
  `DescribeSubnets`, `DescribeNatGateways`, `DescribeInternetGateways` and
  `DescribeAddresses`, only as needed.
- No deployer IAM policy is supplied or certified as least privilege. A future
  deployment needs reviewed EC2/VPC create/delete/tag permissions and read
  permissions for planning. Prefer a temporary role session and a sandbox
  account. Avoid root credentials, access keys in tfvars, or broad CI admin roles.
- State, plan JSON, raw AWS exports, logs and account identities stay private.
  Use ignored `.private/` for exports, outside the committed fixtures. `.gitignore`
  is a guardrail, not encryption or a guarantee against force-add or past leaks.

## State, reproducibility and recovery

Local state is the current backend. It maps Terraform addresses to AWS objects;
Git tracks desired configuration, not that mapping. Keep a protected encrypted
backup outside Git, restrict local permissions, and serialize lab operations.
Local locking does not coordinate independent machines with separate copies.
Team use would require reviewed remote storage, encryption, versioning, locking
and access controls; that infrastructure is deferred here.

Before real changes, verify account, region, workspace, selected AZs and state
ownership. Review the whole plan, especially replacements and NAT opt-in. Saved
plans may contain secrets and can become stale; regenerate after configuration,
state, credentials or remote resources change.

If execution is interrupted, first establish whether an operation is still
running. Inspect state and AWS read-only, then plan against the actual state.
Do not assume “failed” means “nothing was created.” Restore a verified state
backup or perform carefully reviewed imports if mapping is lost; do not blindly
apply with empty state, force-unlock a live operation, or delete state to hide
resources. Code rollback is not infrastructure rollback: inspect the resulting
plan before any approved remediation.

## Detection, diagnosis and recovery

| Failure | Detection and impact | Recovery | Evidence level |
|---|---|---|---|
| Database has a NAT default | Checker exits 1 with table-specific non-local/default-route diagnostics; violates database egress policy | Correct desired configuration or drift through a reviewed plan, obtain approval for AWS mutation, collect a fresh snapshot, rerun | Offline bad fixture exercised; no live route changed |
| Route points to a deleted target | Checker reports non-active/blackhole route; matching traffic cannot use that path | Inspect target existence/state and association, then review route/target correction | Synthetic blackhole test exercised |
| Missing or incorrect subnet association | Terraform mocked assertions detect source wiring regressions; live checker cannot see whether the snapshot tables serve intended subnets | Compare all six subnet IDs and associations against outputs; correct only after plan review | Source-level test exercised; live association check unverified |
| Dependency checksum/init failure | Init/validate errors before useful configuration result; may reflect package/cache/download/environment issues | Keep lock intact; verify official packages and clean cache in a disposable copy; use clean CI runner to distinguish environment failure | Local cached-package error recorded; official lock check unchanged |
| Wrong account, region or missing state | Empty/unexpected inventory or replacement/create-heavy plan | Stop; confirm identity/region/workspace, restore verified mapping; never approve solely from resource count | Procedure only |
| AZ failure with NAT enabled | Future app egress in failed AZ may be lost; the other AZ has its own NAT path | Diagnose AZ/target state; workload recovery requires an actual workload design | Design-only; no outage test or HA claim |

Monitoring implemented here is **on-demand configuration checking and CI**, not
continuous cloud monitoring. A fresh export is needed to detect live route drift.
The checker cannot prove snapshot freshness, gateway health, subnet associations,
SG/NACL policy, reachability, availability or cleanup. The CI has no cloud access.

Flow Logs, CloudWatch alarms and scheduled checks are not installed. Before a
future active lab, inspect available gateway state/metrics, set an approved budget
alert, and define an owner and teardown deadline. Alerts are detection aids, not
hard spending caps. Paid log ingestion/storage and additional services stay deferred.

## Cost

NAT is disabled by default. There is no NAT/EIP resource in the default Terraform
configuration and no compute, ALB, database or endpoint. This is not a claim that
the AWS account has no charges or that every possible network use is free.

NAT-on adds two continuously billed gateways, two public IPv4 allocations, and
usage-dependent processing/transfer charges. Estimate using region-specific
prices at the time of deployment:

`2 × gateway-hours × hourly-rate + processed-GB × processing-rate + public-IPv4-hours × address-rate + applicable transfer`

Traffic distribution, region and duration matter; no fixed monthly quote or
free-tier assumption is embedded. Same-AZ NAT avoids intentional cross-AZ routing
for that path, not every transfer charge. Tags support inventory/accounting but
do not cap spending. [AWS VPC pricing](https://aws.amazon.com/vpc/pricing/).

## Cleanup acceptance (not executed in this session)

Destruction needs explicit approval. Before it, confirm account, region, state
ownership, current commit and an approved list of lab resources; save a protected
state backup and the pre-destroy IDs, including NAT allocation IDs. A tag filter
alone can miss untagged or renamed resources.

After approval, from the Terraform directory:

```sh
terraform plan -destroy -out=cleanup.tfplan
# Review the exact saved plan; only after approval:
terraform apply cleanup.tfplan
terraform state list
```

The last command's empty output is only one check. Record the completed apply
summary and check AWS using the preserved IDs: VPC, subnets, route tables, IGW,
NAT gateways (wait for deletion) and EIP allocations (verify released). Confirm
no dependencies or resources were skipped after errors. Compare both known IDs
and project-tagged inventory; check the correct region and account. Delete the
private plan export after required evidence is retained securely. Billing may lag.

This release does not establish live deployment or completed teardown. Current
account cleanup and charges remain unverified until a fresh authorized inspection.
