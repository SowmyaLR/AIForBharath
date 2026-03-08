# ── Read ALB DNS from infra_be automatically ──────────────────────────────

data "terraform_remote_state" "be" {
  backend = "local"
  config  = { path = "../infra_be/terraform.tfstate" }
}

locals {
  # Use the secure HTTPS Proxy URL for the backend
  api_url = try(
    data.terraform_remote_state.be.outputs.api_gateway_proxy_url,
    var.backend_api_url
  )
}

# ── Amplify App ───────────────────────────────────────────────────────────

resource "aws_amplify_app" "vaidya" {
  name         = "${var.project}-${var.environment}-frontend"
  repository   = var.github_repo_url
  access_token = var.github_token
  
  # WEB_COMPUTE is REQUIRED for Next.js SSR apps
  platform     = "WEB_COMPUTE"

  build_spec = <<-EOT
    version: 1
    applications:
      - frontend:
          phases:
            preBuild:
              commands:
                - npm ci
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: .next
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
        appRoot: client
  EOT

  environment_variables = {
    NEXT_PUBLIC_API_URL         = local.api_url
    ENV                         = var.environment
    AMPLIFY_MONOREPO_APP_ROOT   = "client"
    AMPLIFY_DIFF_DEPLOY         = "false"
  }

  # Only keep the SPA fallback rule for Next.js routing
  custom_rule {
    source = "/<*>"
    target = "/index.html"
    status = "404-200"
  }

  tags = {
    Name        = "${var.project}-frontend"
    Environment = var.environment
  }
}

resource "aws_amplify_branch" "infra_setup" {
  app_id      = aws_amplify_app.vaidya.id
  branch_name = "infra_setup"

  enable_auto_build = true
  framework         = "Next.js - SSR"
}
