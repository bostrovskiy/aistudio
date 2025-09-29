# Variables for Canvas MCP Server Terraform configuration

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"  # Free tier eligible
}

variable "volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 20
}

variable "allocate_eip" {
  description = "Whether to allocate an Elastic IP"
  type        = bool
  default     = true
}

variable "create_key_pair" {
  description = "Whether to create a new key pair"
  type        = bool
  default     = true
}

variable "public_key" {
  description = "Public key for the key pair (if create_key_pair is true)"
  type        = string
  default     = ""
}

variable "existing_key_name" {
  description = "Name of existing key pair (if create_key_pair is false)"
  type        = string
  default     = ""
}

variable "key_file" {
  description = "Path to the private key file"
  type        = string
  default     = "canvas-mcp-key.pem"
}
