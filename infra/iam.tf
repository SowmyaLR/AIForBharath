# ════════════════════════════════════════════
#  VaidyaSaarathi — MedGemma SageMaker IAM
#  SageMaker execution role ONLY
#  ECS, S3, DynamoDB resources are in infra_be/ and infra_storage/
# ════════════════════════════════════════════

data "aws_caller_identity" "current" {}

# ── SageMaker Execution Role ─────────────────────────────────────────────────

data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sagemaker_exec" {
  name               = "${local.name_prefix}-sagemaker-exec-role"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
}

# SageMaker needs full access to pull model weights, write logs, read ECR image
resource "aws_iam_role_policy_attachment" "sagemaker_full" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_read" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_policy" "sagemaker_s3_write" {
  name        = "${local.name_prefix}-sagemaker-s3-write"
  description = "Allow SageMaker to write async results"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.async_outputs.arn,
          "${aws_s3_bucket.async_outputs.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_s3_write_attach" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = aws_iam_policy.sagemaker_s3_write.arn
}

resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "cw_logs" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}
