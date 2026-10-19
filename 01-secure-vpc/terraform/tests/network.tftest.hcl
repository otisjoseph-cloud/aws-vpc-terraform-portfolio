# No AWS API calls: every run uses the mock provider.
# The first two use an in-memory mocked apply so dependent IDs resolve.
mock_provider "aws" {
  override_during = plan
  mock_data "aws_availability_zones" {
    defaults = { names = ["us-east-1c", "us-east-1b", "us-east-1a"] }
  }
}

run "default_network" {
  command = apply

  assert {
    condition     = aws_vpc.this.cidr_block == "10.0.0.0/16" && aws_vpc.this.enable_dns_support && aws_vpc.this.enable_dns_hostnames
    error_message = "The fixed VPC CIDR and DNS settings must be retained."
  }
  assert {
    condition     = output.availability_zones == { az_a = "us-east-1a", az_b = "us-east-1b" }
    error_message = "Default AZ selection must be sorted and use two zones."
  }
  assert {
    condition = (
      length(aws_subnet.public) == 2 && length(aws_subnet.application) == 2 && length(aws_subnet.database) == 2 &&
      toset([for s in aws_subnet.public : s.cidr_block]) == toset(["10.0.1.0/24", "10.0.2.0/24"]) &&
      toset([for s in aws_subnet.application : s.cidr_block]) == toset(["10.0.11.0/24", "10.0.12.0/24"]) &&
      toset([for s in aws_subnet.database : s.cidr_block]) == toset(["10.0.21.0/24", "10.0.22.0/24"])
    )
    error_message = "All six expected subnet CIDRs must be present."
  }
  assert {
    condition = (
      alltrue([for s in aws_subnet.public : s.map_public_ip_on_launch && s.vpc_id == aws_vpc.this.id]) &&
      alltrue([for s in aws_subnet.application : !s.map_public_ip_on_launch && s.vpc_id == aws_vpc.this.id]) &&
      alltrue([for s in aws_subnet.database : !s.map_public_ip_on_launch && s.vpc_id == aws_vpc.this.id])
    )
    error_message = "Only public subnets may auto-assign public IPv4 addresses; all subnets belong to this VPC."
  }
  assert {
    condition = (
      length(aws_route_table_association.public) == 2 &&
      length(aws_route_table_association.application) == 2 &&
      length(aws_route_table_association.database) == 2 &&
      alltrue([for k, a in aws_route_table_association.public : a.subnet_id == aws_subnet.public[k].id && a.route_table_id == aws_route_table.public.id]) &&
      alltrue([for k, a in aws_route_table_association.application : a.subnet_id == aws_subnet.application[k].id && a.route_table_id == aws_route_table.application[k].id]) &&
      alltrue([for k, a in aws_route_table_association.database : a.subnet_id == aws_subnet.database[k].id && a.route_table_id == aws_route_table.database[k].id])
    )
    error_message = "All six subnets need explicit associations to the correct tier/AZ table."
  }
  assert {
    condition = (
      aws_route.public_internet.destination_cidr_block == "0.0.0.0/0" &&
      aws_route.public_internet.gateway_id == aws_internet_gateway.this.id &&
      aws_route.public_internet.route_table_id == aws_route_table.public.id &&
      aws_internet_gateway.this.vpc_id == aws_vpc.this.id
    )
    error_message = "Only the public default route uses this VPC's IGW."
  }
  assert {
    condition     = length(aws_eip.nat) == 0 && length(aws_nat_gateway.this) == 0 && length(aws_route.application_nat) == 0
    error_message = "Default settings must create no EIPs, NAT gateways or app default routes."
  }
}

run "nat_enabled" {
  command = apply
  variables { enable_nat_gateways = true }

  assert {
    condition     = length(aws_nat_gateway.this) == 2 && length(aws_eip.nat) == 2 && length(aws_route.application_nat) == 2
    error_message = "NAT is an explicit opt-in for two gateways, EIPs and application defaults."
  }
  assert {
    condition = alltrue([for k, n in aws_nat_gateway.this :
      n.subnet_id == aws_subnet.public[k].id && n.allocation_id == aws_eip.nat[k].id &&
      aws_subnet.public[k].availability_zone == aws_subnet.application[k].availability_zone &&
      aws_route.application_nat[k].nat_gateway_id == n.id &&
      aws_route.application_nat[k].route_table_id == aws_route_table.application[k].id &&
      aws_route.application_nat[k].destination_cidr_block == "0.0.0.0/0"
    ])
    error_message = "Application routes must use the corresponding same-AZ public NAT and EIP."
  }
  assert {
    condition = alltrue([for k, a in aws_route_table_association.database :
      a.route_table_id == aws_route_table.database[k].id &&
      a.route_table_id != aws_route_table.application[k].id &&
      a.route_table_id != aws_route_table.public.id
    ])
    error_message = "Database associations must remain separate when NAT is enabled."
  }
}

run "explicit_zone_order" {
  command = plan
  variables { availability_zones = ["us-east-1c", "us-east-1a"] }
  assert {
    condition     = output.availability_zones == { az_a = "us-east-1c", az_b = "us-east-1a" }
    error_message = "Explicit AZ order must be retained, not sorted or silently changed."
  }
}

run "reject_duplicate_zones" {
  command = plan
  variables { availability_zones = ["us-east-1a", "us-east-1a"] }
  expect_failures = [var.availability_zones]
}

run "reject_single_zone" {
  command = plan
  variables { availability_zones = ["us-east-1a"] }
  expect_failures = [var.availability_zones]
}
