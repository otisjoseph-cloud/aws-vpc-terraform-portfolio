# Verification and evidence limits

This AWS/Terraform portfolio lab exercises configuration and synthetic route
data; the tests do not establish live AWS deployment or independent proficiency.

## Reproduce the automated checks

Use Terraform 1.15.8, Python 3.10+ and the committed AWS 6.64.0 dependency lock.
From repository root:

```sh
terraform -chdir=01-secure-vpc/terraform fmt -check -diff -recursive
terraform -chdir=01-secure-vpc/terraform init -backend=false -input=false -lockfile=readonly -no-color
terraform -chdir=01-secure-vpc/terraform validate -no-color
terraform -chdir=01-secure-vpc/terraform test -no-color
python3 -m unittest discover -s 01-secure-vpc/tools/route-checker -v
```

Expected: formatting exit 0, successful initialization and validation, five
Terraform cases passed, and 20 Python tests passed. All Terraform cases use a
mock AWS provider: two in-memory applies check NAT-off/on relationships and three
mock plans check AZ inputs. No credentials, live plan, AWS apply or cloud teardown
are part of CI. Registry access is still needed to install the provider.

The [Network validation workflow](../../.github/workflows/terraform-validation.yml)
executes these commands. Release acceptance requires a successful run on the
published revision. Inspect [GitHub Actions](https://github.com/otisjoseph-cloud/aws-vpc-terraform-portfolio/actions)
and match the run's head SHA to the commit being reviewed; a prior green run does
not establish that later revisions passed. Run logs provide the actual commands,
test counts and outcomes without embedding a stale success badge or commit claim.

## Safe failure and correction

```sh
python3 01-secure-vpc/tools/route-checker/check_routes.py 01-secure-vpc/tools/route-checker/fixtures/good.json --vpc-id vpc-synthetic
python3 01-secure-vpc/tools/route-checker/check_routes.py 01-secure-vpc/tools/route-checker/fixtures/bad-database-route.json --vpc-id vpc-synthetic
```

The good fixture must exit 0. The deliberately incorrect fixture must exit 1,
identifying a database table with an unexpected non-local/default route. A test
that treats this expected failure as success without checking its diagnostic
would be inadequate. The CLI tests check the failure exit and message.

The injected NAT route violates database local-only policy. It would introduce
an outbound routing path if its target and other controls worked; it does not
prove inbound internet exposure. In a disposable copy, remove the database's
non-local route and rerun: expected exit 0. The committed negative fixture must
remain incorrect so future regressions can be caught. The checker never changes
AWS resources. Real correction would require reviewed IaC and separate approval.

## What each result establishes

| Check | Establishes | Does not establish |
|---|---|---|
| `fmt` | Terraform formatting | Configuration correctness |
| `init` | Dependency setup and lock acceptance in that environment | Valid resource relationships |
| `validate` | Configuration/type validity | Real AWS planning or deployment |
| Mock Terraform tests | Source topology, associations, NAT policy and selected input constraints | AWS API acceptance, quotas, permissions or packet flow |
| Python tests/fixtures | Policy logic, input handling and CLI exit behavior | Snapshot freshness, deployed associations or reachability |
| Successful Actions run | Listed checks passed for its recorded head SHA | Production readiness or independently demonstrated proficiency |
| Cleanup instructions | A reviewable procedure | Executed teardown or zero current charges |

During preparation, a local cached AWS-provider package produced a checksum
error at validation despite successful initialization. The lock file was retained;
an official platform-lock check left it unchanged. This local error is not a
validation pass. For this repository, verify the latest successful [Network validation workflow](https://github.com/otisjoseph-cloud/aws-vpc-terraform-portfolio/actions) and match its head SHA to the revision under review. A prior green run is not proof that a later revision passed.
Never disable checksum verification to make a check green.

## Remaining limitations

Live AWS planning, deployment, runtime routing, current inventory, teardown and
account charges remain unverified. Workloads, SG/NACL tier policies, continuous
monitoring, remote state, real outage recovery and availability claims are
outside this bounded release. See [operations](operations.md) for the documented
security, cost, diagnosis, recovery and cleanup procedures.
