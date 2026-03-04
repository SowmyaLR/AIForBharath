# ════════════════════════════════════════════════════════════
#  VaidyaSaarathi — Backend Infrastructure (ECS Fargate)
#  ECR + ALB + ECS Cluster + Task Definition + Service
# ════════════════════════════════════════════════════════════

# ── Networking: Default VPC + Subnets ───────────────────────────────────────

data "aws_vpc" "default" { default = true }
data "aws_caller_identity" "current" {}
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ── Remote State: Read outputs from sibling modules ─────────────────────────

data "terraform_remote_state" "storage" {
  backend = "local"
  config  = { path = "../infra_storage/terraform.tfstate" }
}

# ── ECR Repository ───────────────────────────────────────────────────────────

resource "aws_ecr_repository" "api" {
  name                 = "${var.project}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration { scan_on_push = true }

  tags = { Name = "${var.project}-api" }
}

# ECR lifecycle: keep only the last 5 images to avoid storage creep
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# ── Security Groups ──────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "ALB — allow inbound HTTP/HTTPS from internet"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-alb-sg" }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "${local.name_prefix}-ecs-tasks-sg"
  description = "ECS tasks — allow inbound from ALB only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${local.name_prefix}-ecs-tasks-sg" }
}

# ── Application Load Balancer ────────────────────────────────────────────────

resource "aws_lb" "backend" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  tags = { Name = "${local.name_prefix}-alb" }
}

resource "aws_lb_target_group" "api" {
  name        = "${local.name_prefix}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip" # required for Fargate awsvpc networking

  health_check {
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }

  tags = { Name = "${local.name_prefix}-api-tg" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# ── CloudWatch Log Group ─────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "ecs_api" {
  name              = "/ecs/${local.name_prefix}-api"
  retention_in_days = 7
}

# ── ECS Cluster ──────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = "${local.name_prefix}-cluster" }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# ── ECS Task Definition ──────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "2048" # 2 vCPU — headroom for Whisper + HeAR in-process
  memory                   = "8192" # 8 GB — Whisper ~1.5GB + HeAR ~2GB + app overhead
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:demo"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]

      environment = [
        { name = "APP_ENV",                      value = "demo" },
        { name = "AWS_REGION",                   value = var.aws_region },
        { name = "AUDIO_S3_BUCKET",              value = data.terraform_remote_state.storage.outputs.audio_bucket_name },
        { name = "FHIR_S3_BUCKET",               value = data.terraform_remote_state.storage.outputs.fhir_bucket_name },
        { name = "DYNAMODB_TRIAGE_TABLE",        value = data.terraform_remote_state.storage.outputs.triage_table_name },
        { name = "DYNAMODB_PATIENTS_TABLE",      value = data.terraform_remote_state.storage.outputs.patients_table_name },
        { name = "SAGEMAKER_MEDGEMMA_ENDPOINT",  value = var.medgemma_endpoint_name },
        { name = "FRONTEND_URL",                 value = var.frontend_url },
      ]

      # HF_TOKEN from SSM Parameter Store — not in plaintext env vars
      secrets = [
        { name = "HF_TOKEN", valueFrom = var.hf_token_ssm_param_arn }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      # Give container 120s to load Whisper + HeAR models before health checks start
      startTimeout = 120
      stopTimeout  = 30
    }
  ])

  tags = { Name = "${local.name_prefix}-api-task" }
}

# ── ECS Service ──────────────────────────────────────────────────────────────

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true # Required for default VPC without NAT gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 100 # Zero downtime during updates
  deployment_maximum_percent         = 200 # Allow 2nd task during rollout
  health_check_grace_period_seconds  = 180 # Whisper + HeAR load time buffer

  deployment_circuit_breaker {
    enable   = true  # Auto-rollback if new task fails health checks
    rollback = true
  }

  depends_on = [aws_lb_listener.http]

  tags = { Name = "${local.name_prefix}-api-service" }
}
