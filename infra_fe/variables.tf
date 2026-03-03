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

variable "github_token" {
  description = "GitHub Personal Access Token for Amplify access"
  type        = string
  sensitive   = true
}

variable "github_repo_url" {
  description = "GitHub Repository URL for the frontend"
  type        = string
  default     = "https://github.com/SowmyaLR/AIForBharath"
}

variable "backend_api_url" {
  description = "The public URL of the backend API (from EC2)"
  type        = string
}
