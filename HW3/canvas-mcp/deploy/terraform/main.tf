# Terraform configuration for Canvas MCP Server on AWS
# This creates a secure EC2 instance with proper security groups

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-lts-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security Group
resource "aws_security_group" "canvas_mcp_sg" {
  name_prefix = "canvas-mcp-"
  description = "Security group for Canvas MCP Server"

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # MCP Server port (if you want to expose it directly)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "MCP Server port"
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "canvas-mcp-security-group"
  }
}

# Key Pair (you'll need to create this manually or use existing)
resource "aws_key_pair" "canvas_mcp_key" {
  count      = var.create_key_pair ? 1 : 0
  key_name   = "canvas-mcp-key"
  public_key = var.public_key
}

# EC2 Instance
resource "aws_instance" "canvas_mcp_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.create_key_pair ? aws_key_pair.canvas_mcp_key[0].key_name : var.existing_key_name
  vpc_security_group_ids = [aws_security_group.canvas_mcp_sg.id]

  # Instance storage
  root_block_device {
    volume_type = "gp3"
    volume_size = var.volume_size
    encrypted   = true
  }

  # User data script for initial setup
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    app_name = "canvas-mcp-server"
  }))

  tags = {
    Name        = "Canvas MCP Server"
    Environment = "production"
    Project     = "canvas-mcp"
  }

  # Enable detailed monitoring
  monitoring = true
}

# Elastic IP (optional)
resource "aws_eip" "canvas_mcp_eip" {
  count    = var.allocate_eip ? 1 : 0
  instance = aws_instance.canvas_mcp_server.id
  domain   = "vpc"

  tags = {
    Name = "canvas-mcp-eip"
  }
}

# Outputs
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.canvas_mcp_server.id
}

output "public_ip" {
  description = "Public IP address of the instance"
  value       = var.allocate_eip ? aws_eip.canvas_mcp_eip[0].public_ip : aws_instance.canvas_mcp_server.public_ip
}

output "public_dns" {
  description = "Public DNS name of the instance"
  value       = aws_instance.canvas_mcp_server.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${var.create_key_pair ? "canvas-mcp-key.pem" : var.key_file} ubuntu@${var.allocate_eip ? aws_eip.canvas_mcp_eip[0].public_ip : aws_instance.canvas_mcp_server.public_ip}"
}
