# ════════════════════════════════════════════
#  VaidyaSaarathi - MedGemma SageMaker Infra
#  SageMaker Model + Endpoint Resources
# ════════════════════════════════════════════

# ── SageMaker Model (HuggingFace TGI + MedGemma weights) ───────────────

resource "aws_sagemaker_model" "medgemma" {
  name               = "${local.name_prefix}-medgemma-model"
  execution_role_arn = aws_iam_role.sagemaker_exec.arn

  primary_container {
    image = local.tgi_image_uri

    environment = {
      # HuggingFace TGI environment variables
      HF_MODEL_ID                = var.medgemma_model_id
      HF_TOKEN                   = var.hf_token
      SM_NUM_GPUS                = "1"
      MAX_INPUT_LENGTH           = "4096"
      MAX_TOTAL_TOKENS           = "4608"   # input + output
      MAX_BATCH_PREFILL_TOKENS   = "4096"
      # JSON output
      MESSAGES_API_ENABLED       = "true"
    }
  }

  tags = {
    Name = "${local.name_prefix}-medgemma-model"
  }
}

# ── Endpoint Configuration ──────────────────────────────────────────────

resource "aws_sagemaker_endpoint_configuration" "medgemma" {
  name = "${local.name_prefix}-medgemma-epc"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.medgemma.name
    instance_type          = var.medgemma_instance_type
    initial_instance_count = var.medgemma_initial_instance_count

    # Enable model data capture (for monitoring / audit)
    # Uncomment in production:
    # managed_instance_scaling {
    #   status         = "ENABLED"
    #   min_instance_count = 1
    #   max_instance_count = 2
    # }
  }

  # Data capture config for HIPAA audit trail (uncomment for prod)
  # data_capture_config {
  #   enable_capture             = true
  #   initial_sampling_percentage = 100
  #   destination_s3_uri         = "s3://${aws_s3_bucket.artifacts.bucket}/data-capture"
  #   capture_options {
  #     capture_mode = "Input"
  #   }
  #   capture_options {
  #     capture_mode = "Output"
  #   }
  # }

  tags = {
    Name = "${local.name_prefix}-medgemma-epc"
  }
}

# ── Real-Time Inference Endpoint ────────────────────────────────────────

resource "aws_sagemaker_endpoint" "medgemma" {
  name                 = "${local.name_prefix}-medgemma-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.medgemma.name

  tags = {
    Name = "${local.name_prefix}-medgemma-endpoint"
  }
}

# ── CloudWatch Alarms for Endpoint Health ───────────────────────────────

resource "aws_cloudwatch_metric_alarm" "endpoint_invocation_errors" {
  alarm_name          = "${local.name_prefix}-medgemma-invocation-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "InvocationModelErrors"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "MedGemma endpoint is throwing too many errors"

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.medgemma.name
    VariantName  = "primary"
  }

  treat_missing_data = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "endpoint_latency_high" {
  alarm_name          = "${local.name_prefix}-medgemma-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "p90"
  threshold           = 10000  # 10s P90 latency threshold (microseconds → ms)
  alarm_description   = "MedGemma P90 latency exceeds 10 seconds"

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.medgemma.name
    VariantName  = "primary"
  }

  treat_missing_data = "notBreaching"
}
