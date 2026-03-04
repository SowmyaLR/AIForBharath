# ── Read ALB DNS from infra_be automatically ──────────────────────────────

data "terraform_remote_state" "be" {
  backend = "local"
  config  = { path = "../infra_be/terraform.tfstate" }
}

locals {
  # Prefer remote state value; fall back to var.backend_api_url if infra_be not applied yet
  api_url = try(
    data.terraform_remote_state.be.outputs.alb_dns_name,
    var.backend_api_url
  )
}

# ── Amplify App ───────────────────────────────────────────────────────────

resource "aws_amplify_app" "vaidya" {
  name         = "${var.project}-${var.environment}-frontend"
  repository   = var.github_repo_url
  access_token = var.github_token

  build_spec = <<-EOT
    version: 1
    frontend:
      phases:
        preBuild:
          commands:
            - cd client && npm ci
        build:
          commands:
            - cd client && npm run build
      artifacts:
        baseDirectory: client/.next
        files:
          - '**/*'
      cache:
        paths:
          - client/node_modules/**/*
  EOT

  environment_variables = {
    NEXT_PUBLIC_API_URL = local.api_url
    ENV                 = var.environment
  }

  tags = {
    Name        = "${var.project}-frontend"
    Environment = var.environment
  }
}

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.vaidya.id
  branch_name = "main"

  enable_auto_build = true
  framework         = "Next.js - SSR"
}
