#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  VaidyaSaarathi — Backend Deployment Script (ECR + ECS)
#  Usage: ./scripts/deploy.sh [IMAGE_TAG] [AWS_REGION]
# ════════════════════════════════════════════════════════════════

set -e

# Default values
IMAGE_TAG=${1:-"demo"}
AWS_REGION=${2:-"ap-south-1"}

# Configuration (Sync with infra_be/outputs.tf)
ECR_REPO_URL="798329741053.dkr.ecr.ap-south-1.amazonaws.com/vaidyasaarathi-api"
ECS_CLUSTER="vaidyasaarathi-demo-v2-cluster"
ECS_SERVICE="vaidyasaarathi-demo-v2-api-service"

echo "🚀 Starting deployment for VaidyaSaarathi Backend (Tag: $IMAGE_TAG)..."

# 1. Login to ECR
echo "🔑 Logging in to AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL

# 2. Build & Tag
echo "🏗️ Building Docker image (forcing linux/amd64 for ECS compatibility)..."
docker build --platform linux/amd64 -t $ECR_REPO_URL:$IMAGE_TAG -f Dockerfile .

# 3. Push to ECR
echo "⏫ Pushing image to ECR..."
docker push $ECR_REPO_URL:$IMAGE_TAG

# 4. Trigger ECS Update
echo "🔄 Forcing ECS Service update to deploy new stable version..."
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --region $AWS_REGION

echo "✅ SUCCESS: Deployment complete. Monitor the ECS task in the AWS console."
