# ════════════════════════════════════════════
#  VaidyaSaarathi — Lambda Infrastructure
#  Warm-ping + Endpoint Lifecycle
# ════════════════════════════════════════════

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "lambdas"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}-v2"
}
