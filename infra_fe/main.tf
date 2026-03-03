resource "aws_amplify_app" "vaidya" {
  name       = "${var.project}-${var.environment}-frontend"
  repository = var.github_repo_url
  
  # OAuth token for GitHub access
  access_token = var.github_token

  # Build spec for Client monorepo
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
    NEXT_PUBLIC_API_URL = var.backend_api_url
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

  framework = "Next.js - SSR"
}
