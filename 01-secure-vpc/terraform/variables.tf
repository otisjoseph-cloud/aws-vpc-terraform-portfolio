variable "aws_region" {
  description = "AWS Region in which to create the network foundation."
  type        = string
  default     = "us-east-1"
}

variable "availability_zones" {
  description = "Optional ordered list of exactly two Availability Zone names. An empty list selects the first two available zones alphabetically."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.availability_zones) == 0 || length(var.availability_zones) == 2
    error_message = "availability_zones must be empty or contain exactly two Availability Zone names."
  }

  validation {
    condition     = length(var.availability_zones) == length(distinct(var.availability_zones))
    error_message = "availability_zones must not contain duplicate values."
  }
}

variable "enable_nat_gateways" {
  description = "Create one NAT Gateway per Availability Zone and same-AZ application default routes. NAT Gateways incur hourly and data-processing charges."
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Public-safe project name used in resource names and tags."
  type        = string
  default     = "secure-vpc-lab"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "project_name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Public-safe environment label used in resource names and tags."
  type        = string
  default     = "lab"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must contain only lowercase letters, numbers, and hyphens."
  }
}
