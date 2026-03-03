# ECR Repositories for Backend and Frontend
resource "aws_ecr_repository" "api" {
  name                 = "${var.project}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_ecr_repository" "client" {
  name                 = "${var.project}-client"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

# VPC, Subnet, Security Group
data "aws_vpc" "default" {
  default = true
}

data "aws_caller_identity" "current" {}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "backend_sg" {
  name        = "${var.project}-${var.environment}-backend-sg"
  description = "Security group for VaidyaSaarathi backend"
  vpc_id      = data.aws_vpc.default.id

  # SSH Access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI Backend Port
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Next.js Client Port
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role for EC2
resource "aws_iam_role" "backend_role" {
  name = "${var.project}-${var.environment}-backend-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Grant SageMaker Invoke Permissions to the EC2 Backend
resource "aws_iam_role_policy_attachment" "sagemaker_access" {
  role       = aws_iam_role.backend_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# Grant S3 Access for Audio storage
resource "aws_iam_role_policy_attachment" "s3_access" {
  role       = aws_iam_role.backend_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Grant SSM Access for shell session
resource "aws_iam_role_policy_attachment" "ssm_access" {
  role       = aws_iam_role.backend_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "backend_profile" {
  name = "${var.project}-${var.environment}-backend-profile"
  role = aws_iam_role.backend_role.name
}

# Find latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "backend_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.backend_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.backend_profile.name
  key_name                    = var.key_name != "" ? var.key_name : null
  associate_public_ip_address = true

  root_block_device {
    volume_size = 100 # Important: Need storage for local Whisper/HeAR models
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update
              sudo apt-get install -y docker.io docker-compose git awscli
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -aG docker ubuntu

              # Create app directory workspace
              mkdir -p /home/ubuntu/vaidyasaarathi
              cd /home/ubuntu/vaidyasaarathi

              # Login to ECR
              aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com

              # Environment config for docker-compose
              cat << 'ENV' > .env.demo
              APP_ENV=demo
              AWS_REGION=${var.aws_region}
              HF_TOKEN=${var.hf_token}
              SAGEMAKER_MEDGEMMA_ENDPOINT=${var.sagemaker_medgemma_endpoint}
              NEXT_PUBLIC_API_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000
              ENV
              
              # Pull and Start (Assuming images are pushed to ECR)
              # For hackathon demo, we can also git clone and build locally if preferred
              # but ECR is more 'production' style.
              
              chown -R ubuntu:ubuntu /home/ubuntu/vaidyasaarathi
              EOF

  tags = {
    Name = "${var.project}-${var.environment}-backend"
  }
}
