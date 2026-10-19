output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.this.id
}

output "availability_zones" {
  description = "Availability Zones used by the network, keyed by logical AZ name."
  value       = local.azs
}

output "public_subnet_ids" {
  description = "Public subnet IDs keyed by logical AZ name."
  value       = { for key, subnet in aws_subnet.public : key => subnet.id }
}

output "application_subnet_ids" {
  description = "Private application subnet IDs keyed by logical AZ name."
  value       = { for key, subnet in aws_subnet.application : key => subnet.id }
}

output "database_subnet_ids" {
  description = "Private database subnet IDs keyed by logical AZ name."
  value       = { for key, subnet in aws_subnet.database : key => subnet.id }
}

output "public_route_table_id" {
  description = "ID of the shared public route table."
  value       = aws_route_table.public.id
}

output "application_route_table_ids" {
  description = "Application route-table IDs keyed by logical AZ name."
  value       = { for key, route_table in aws_route_table.application : key => route_table.id }
}

output "database_route_table_ids" {
  description = "Database route-table IDs keyed by logical AZ name."
  value       = { for key, route_table in aws_route_table.database : key => route_table.id }
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs keyed by logical AZ name; empty when enable_nat_gateways is false."
  value       = { for key, nat_gateway in aws_nat_gateway.this : key => nat_gateway.id }
}
