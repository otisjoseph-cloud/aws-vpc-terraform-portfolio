# Reproduce the Terraform foundation

Use Terraform **1.15.8**, the version pinned in CI, and the committed AWS provider
**6.64.0** lock file. `versions.tf` permits Terraform >=1.10,<2 and AWS ~>6.0;
the wider constraints are compatibility intent, not evidence every version works.
No external Terraform modules or backend are configured.

## Safe local checks

Clone this repository and use `main`. From repository root, change directory to
`01-secure-vpc/terraform`, then run:

```sh
terraform fmt -check -diff -recursive
terraform init -backend=false -input=false -lockfile=readonly -no-color
terraform validate -no-color
terraform test -no-color
```

Registry access is needed to install the provider even for mocked tests.
No AWS credentials are needed for these four commands. `init -backend=false`
skips backend setup; it is not a promise that subsequent arbitrary commands
cannot contact AWS. Run only the reviewed mock tests for offline verification.

`tests/network.tftest.hcl` replaces the AWS provider with a mock, supplies
synthetic AZ discovery. Two in-memory mocked applies resolve dependent IDs;
three plan-mode runs check AZ input behavior. It tests subnet CIDRs, IP assignment,
explicit associations, public IGW routing, NAT-disabled resource absence,
NAT-enabled same-AZ wiring, explicit AZ order and invalid AZ-list rejection.
Mock results do not validate AWS APIs, region availability, quotas or packet flow.

## Inputs and outputs

| Input | Default | Consequence |
|---|---|---|
| `aws_region` | `us-east-1` | Real plan uses this account/region's available AZs |
| `availability_zones` | `[]` | Sort discovered names and select first two; optionally supply two distinct valid names |
| `enable_nat_gateways` | `false` | `true` adds two EIPs, two NAT gateways and two app routes |
| `project_name` | `secure-vpc-lab` | Public-safe names/tags; lowercase letters, digits, hyphens |
| `environment` | `lab` | Public-safe names/tags with the same character restriction |

VPC and subnet CIDRs are deliberately fixed in `main.tf` and `locals.tf`.
Name validation does not prove supplied AZs exist in the selected region; a real
plan/apply must resolve that. Pin actual AZ names before a real deployment and
review replacements if names or region change. If fewer than two AZs are
available, default selection cannot succeed.

Outputs expose the VPC, selected AZs, subnet IDs, managed route-table IDs and
NAT IDs (empty when disabled). These are topology metadata; keep real exports private.

## Optional real plan, only with authorized account access

Copy `terraform.tfvars.example` to ignored `terraform.tfvars` only if needed.
Use temporary credentials through the AWS provider's normal credential chain.
Confirm account and region before planning. From this directory:

```sh
aws sts get-caller-identity
terraform init -input=false -lockfile=readonly
terraform plan -input=false -detailed-exitcode
```

Exit 0 means no differences, 2 means differences to review, 1 means error.
A plan can read AWS and reveal identifiers. It is not an apply and does not prove
resource creation or behavior. No real plan/apply is part of the offline CI.
Resource counts expected from the inspected configuration are 20 with NAT off
and 26 with NAT on; that arithmetic is not a newly executed real AWS plan.
Do not deploy or enable NAT without approval and a cleanup window.

## CI and dependency troubleshooting

`.github/workflows/terraform-validation.yml` runs on relevant pushes and PRs.
It uses pinned action SHAs, read-only repository permission, no persisted Git
credentials, no AWS/OIDC credentials and a ten-minute timeout. It performs the
four Terraform checks and the Python suite. No paid runner is configured.

For formatting errors, inspect the diff then run `terraform fmt`. For validation
errors, correct the named expression or type. For download/provider failures,
inspect network, package verification and provider handshake separately from
configuration validity. Never remove checksum protection to obtain a pass.
For an intentional platform-lock refresh, use the official registry and review:

```sh
terraform providers lock -platform=linux_amd64 -platform=windows_amd64
```

No version upgrade is required by this project audit. Lock changes must preserve
the selected provider version and be justified by authenticated package evidence.
See [operations](../docs/operations.md) for state, recovery and cleanup, and
[verification](../docs/verification.md) for observed results and limitations.
