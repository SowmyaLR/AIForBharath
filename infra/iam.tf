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

resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "cw_logs" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}
