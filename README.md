# Secure VPC network foundation on AWS

A bounded, AI-assisted **portfolio project**, not professional cloud employment
or a production platform. Terraform defines a two-AZ IPv4 network; a read-only
Python tool checks saved route-table responses. No workload or real data is used.

## Implemented

- One `10.0.0.0/16` VPC, six subnets, five managed route tables, six explicit
  associations and an Internet Gateway.
- Public, application and database tiers in two Availability Zones.
- Two same-AZ NAT gateways and Elastic IPs **only when explicitly enabled**;
  default is `enable_nat_gateways = false`.
- Database tables receive no configured non-local routes in either mode.
- Credential-free CI: Terraform formatting, locked initialization, validation,
  mocked topology tests and Python policy/CLI tests.

Subnet separation controls routing. It does **not** enforce least-privilege
traffic between tiers: the VPC local route remains, and this project defines
no workload security groups or custom NACLs. Public subnets auto-assign public
IPv4 addresses to eligible future launches; no instances are created here.

## Verify without deploying

Prerequisites: Git, Terraform **1.15.8** (the reproducibility pin), Python 3.10+,
and registry access for provider installation. AWS provider **6.64.0** is locked.
From repository root on `main`:

```sh
terraform -chdir=01-secure-vpc/terraform fmt -check -diff -recursive
terraform -chdir=01-secure-vpc/terraform init -backend=false -input=false -lockfile=readonly -no-color
terraform -chdir=01-secure-vpc/terraform validate -no-color
terraform -chdir=01-secure-vpc/terraform test -no-color
python3 -m unittest discover -s 01-secure-vpc/tools/route-checker -v
```

The committed Terraform test file uses a mocked AWS provider for every run.
Two in-memory mocked applies resolve resource relationships; three mocked plans
check input behavior. These checks do not use AWS credentials or create cloud
resources. Read future test changes before running them: `terraform test` can
apply real resources when configured differently. On Windows, use `python`
in place of `python3` if that is your interpreter command.

## Read in this order

1. [Architecture and five-minute walkthrough](01-secure-vpc/README.md)
2. [Setup, variables and Terraform testing](01-secure-vpc/terraform/README.md)
3. [Route checker, fixtures and exit codes](01-secure-vpc/tools/route-checker/README.md)
4. [Security, cost, diagnosis, recovery and cleanup](01-secure-vpc/docs/operations.md)
5. [Verification and evidence limits](01-secure-vpc/docs/verification.md)

## Scope and evidence limits

Mocked tests test configuration relationships; fixture tests test software
behavior. Neither proves packet flow, AWS permissions, quotas or live gateway
health. Live deployment, packet behavior and current AWS cleanup are unverified
for this release. See the verification record and the commit-linked Actions logs
for reproducible checks and their limits.

Compute, ALB, databases, workload IAM/security groups, Session Manager, Flow
Logs, alarms, remote state and deployment automation are intentionally deferred.
This project makes no production, compliance, workload availability or independent
owner-proficiency claim.
