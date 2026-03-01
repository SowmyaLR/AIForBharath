# ════════════════════════════════════════════
#  VaidyaSaarathi - MedGemma SageMaker Infra
#  Terraform Provider Configuration
# ════════════════════════════════════════════

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to store state in S3 (recommended for team/CI)
  # backend "s3" {
  #   bucket = "vaidyasaarathi-tfstate"
  #   key    = "infra/terraform.tfstate"
  #   region = "ap-south-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  
  # HuggingFace TGI Deep Learning Container image for ap-south-1
  # See: https://github.com/aws/deep-learning-containers/blob/master/available_images.md
  tgi_image_uri = "763104351884.dkr.ecr.${var.aws_region}.amazonaws.com/huggingface-pytorch-tgi-inference:2.1.1-tgi${var.tgi_image_version}-gpu-py310-cu121-ubuntu22.04"
}
