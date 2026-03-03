variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "vaidyasaarathi"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "demo"
}

variable "instance_type" {
  description = "EC2 instance type for the backend server"
  type        = string
  default     = "g4dn.xlarge" # Or m5.2xlarge if you want CPU only
}

variable "key_name" {
  description = "SSH key pair name for EC2 access (must exist in AWS)"
  type        = string
  default     = ""
}

variable "hf_token" {
  description = "HuggingFace token"
  type        = string
  sensitive   = true
}

variable "sagemaker_medgemma_endpoint" {
  description = "The SageMaker endpoint name from the infra deployment"
  type        = string
}
