# ════════════════════════════════════════════
#  VaidyaSaarathi — Storage Variables
# ════════════════════════════════════════════

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "vaidyasaarathi"
}

variable "environment" {
  description = "Environment name (demo, prod)"
  type        = string
  default     = "demo"
}
