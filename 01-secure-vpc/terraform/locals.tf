locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
    Purpose     = "Portfolio network lab"
  }

  selected_availability_zones = length(var.availability_zones) == 2 ? var.availability_zones : slice(
    sort(data.aws_availability_zones.available.names),
    0,
    2
  )

  azs = {
    az_a = local.selected_availability_zones[0]
    az_b = local.selected_availability_zones[1]
  }

  public_subnets = {
    az_a = "10.0.1.0/24"
    az_b = "10.0.2.0/24"
  }

  application_subnets = {
    az_a = "10.0.11.0/24"
    az_b = "10.0.12.0/24"
  }

  database_subnets = {
    az_a = "10.0.21.0/24"
    az_b = "10.0.22.0/24"
  }

  nat_azs = {
    for key, availability_zone in local.azs : key => availability_zone
    if var.enable_nat_gateways
  }
}
