# ════════════════════════════════════════════
#  VaidyaSaarathi — Backend Outputs (ECS Fargate)
#  Consumed by infra_fe via terraform_remote_state
# ════════════════════════════════════════════

output "alb_dns_name" {
  description = "ALB DNS name — set as NEXT_PUBLIC_API_URL in infra_fe and Amplify env vars"
  value       = "http://${aws_lb.backend.dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL — use in push_backend.sh as image tag target"
  value       = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name — use in aws ecs update-service commands"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name — use in aws ecs update-service commands"
  value       = aws_ecs_service.api.name
}

output "ecs_task_role_arn" {
  description = "ECS task IAM role ARN"
  value       = aws_iam_role.ecs_task.arn
}

output "api_gateway_proxy_url" {
  description = "Secure HTTPS proxy for the backend ALB (Hackathon Demo ready)"
  value       = aws_apigatewayv2_api.api_proxy.api_endpoint
}
