#!/usr/bin/env python3
"""
AWS Secrets Manager integration for Canvas MCP Server
This script helps securely store and retrieve Canvas API credentials
"""

import boto3
import json
import os
import sys
from typing import Dict, Any

class CanvasSecretsManager:
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the Secrets Manager client."""
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self.secret_name = "canvas-mcp-credentials"
    
    def store_credentials(self, api_token: str, api_url: str, institution_name: str = "") -> bool:
        """
        Store Canvas credentials in AWS Secrets Manager.
        
        Args:
            api_token: Canvas API token
            api_url: Canvas API URL
            institution_name: Institution name (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            secret_value = {
                "api_token": api_token,
                "api_url": api_url,
                "institution_name": institution_name
            }
            
            # Try to update existing secret
            try:
                self.client.update_secret(
                    SecretId=self.secret_name,
                    SecretString=json.dumps(secret_value)
                )
                print(f"✅ Updated existing secret: {self.secret_name}")
            except self.client.exceptions.ResourceNotFoundException:
                # Create new secret
                self.client.create_secret(
                    Name=self.secret_name,
                    Description="Canvas MCP Server API credentials",
                    SecretString=json.dumps(secret_value)
                )
                print(f"✅ Created new secret: {self.secret_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error storing credentials: {e}")
            return False
    
    def retrieve_credentials(self) -> Dict[str, Any] | None:
        """
        Retrieve Canvas credentials from AWS Secrets Manager.
        
        Returns:
            dict: Credentials dictionary or None if error
        """
        try:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            credentials = json.loads(response['SecretString'])
            print(f"✅ Retrieved credentials for: {credentials.get('institution_name', 'Unknown')}")
            return credentials
            
        except self.client.exceptions.ResourceNotFoundException:
            print(f"❌ Secret not found: {self.secret_name}")
            return None
        except Exception as e:
            print(f"❌ Error retrieving credentials: {e}")
            return None
    
    def delete_credentials(self) -> bool:
        """
        Delete credentials from AWS Secrets Manager.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.delete_secret(
                SecretId=self.secret_name,
                ForceDeleteWithoutRecovery=True
            )
            print(f"✅ Deleted secret: {self.secret_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting credentials: {e}")
            return False
    
    def list_secrets(self) -> None:
        """List all secrets (for debugging)."""
        try:
            response = self.client.list_secrets()
            print("📋 Available secrets:")
            for secret in response['SecretList']:
                print(f"  - {secret['Name']} (created: {secret['CreatedDate']})")
        except Exception as e:
            print(f"❌ Error listing secrets: {e}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Canvas MCP Server AWS Secrets Manager")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--store", action="store_true", help="Store credentials")
    parser.add_argument("--retrieve", action="store_true", help="Retrieve credentials")
    parser.add_argument("--delete", action="store_true", help="Delete credentials")
    parser.add_argument("--list", action="store_true", help="List all secrets")
    parser.add_argument("--api-token", help="Canvas API token")
    parser.add_argument("--api-url", help="Canvas API URL")
    parser.add_argument("--institution", help="Institution name")
    
    args = parser.parse_args()
    
    # Initialize secrets manager
    secrets_manager = CanvasSecretsManager(args.region)
    
    if args.store:
        if not args.api_token or not args.api_url:
            print("❌ --api-token and --api-url are required for storing credentials")
            sys.exit(1)
        
        success = secrets_manager.store_credentials(
            api_token=args.api_token,
            api_url=args.api_url,
            institution_name=args.institution or ""
        )
        sys.exit(0 if success else 1)
    
    elif args.retrieve:
        credentials = secrets_manager.retrieve_credentials()
        if credentials:
            print("\n📋 Retrieved credentials:")
            print(f"  API URL: {credentials.get('api_url')}")
            print(f"  Institution: {credentials.get('institution_name', 'Not set')}")
            print(f"  Token: {'*' * 20}...{credentials.get('api_token', '')[-4:]}")
        sys.exit(0 if credentials else 1)
    
    elif args.delete:
        success = secrets_manager.delete_credentials()
        sys.exit(0 if success else 1)
    
    elif args.list:
        secrets_manager.list_secrets()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
