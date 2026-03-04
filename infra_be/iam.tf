# ════════════════════════════════════════════
#  VaidyaSaarathi — Backend IAM
#  ECS Execution Role + ECS Task Role (scoped)
# ════════════════════════════════════════════

# ── ECS Execution Role ───────────────────────────────────────────────────────
# Used by ECS control plane to pull images from ECR and write logs to CloudWatch.

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow execution role to read the HF_TOKEN SSM parameter (for secrets: in task def)
resource "aws_iam_role_policy" "ecs_execution_ssm" {
  name = "ssm-secret-access"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameters", "secretsmanager:GetSecretValue"]
      Resource = [var.hf_token_ssm_param_arn]
    }]
  })
}

# ── ECS Task Role ────────────────────────────────────────────────────────────
# Used by the running FastAPI container to access AWS services.
# All policies are scoped to specific resource ARNs — no full-access managed policies.

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name_prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

# S3: read/write audio and FHIR buckets only
resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "s3-audio-fhir-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AudioBucketAccess"
        Effect = "Allow"
        Action = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
        Resource = [
          "${data.terraform_remote_state.storage.outputs.audio_bucket_arn}/*"
        ]
      },
      {
        Sid    = "FhirBucketAccess"
        Effect = "Allow"
        Action = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
        Resource = [
          data.terraform_remote_state.storage.outputs.fhir_bucket_arn,
          "${data.terraform_remote_state.storage.outputs.fhir_bucket_arn}/*"
        ]
      }
    ]
  })
}

# DynamoDB: triage + patients tables only, all required operations
resource "aws_iam_role_policy" "ecs_task_dynamodb" {
  name = "dynamodb-triage-patients-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "TriageAndPatientsAccess"
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan" # kept for dev fallback; remove post-demo
      ]
      Resource = [
        data.terraform_remote_state.storage.outputs.triage_table_arn,
        "${data.terraform_remote_state.storage.outputs.triage_table_arn}/index/*",
        data.terraform_remote_state.storage.outputs.patients_table_arn,
      ]
    }]
  })
}

# SageMaker: invoke MedGemma endpoint only
resource "aws_iam_role_policy" "ecs_task_sagemaker" {
  name = "sagemaker-medgemma-invoke"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeMedGemma"
        Effect = "Allow"
        Action = ["sagemaker:InvokeEndpoint"]
        Resource = [
          "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.medgemma_endpoint_name}"
        ]
      },
      {
        Sid    = "DescribeEndpointForHealth"
        Effect = "Allow"
        Action = ["sagemaker:DescribeEndpoint"]
        Resource = [
          "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.medgemma_endpoint_name}"
        ]
      }
    ]
  })
}

# CloudWatch Logs: write structured logs
resource "aws_iam_role_policy" "ecs_task_logs" {
  name = "cloudwatch-logs-write"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "WriteECSLogs"
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = ["${aws_cloudwatch_log_group.ecs_api.arn}:*"]
    }]
  })
}
