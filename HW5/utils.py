import os
import json
import boto3
from botocore.exceptions import ClientError

def get_secret_from_aws(secret_name, region_name="us-east-1"):
    """Retrieve secrets from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise

def get_anthropic_api_key():
    """Get Anthropic API key from AWS Secrets Manager or environment"""
    # First try environment variable (for local development)
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    
    # Then try AWS Secrets Manager
    try:
        secrets = get_secret_from_aws("ResearchAgentSecrets")
        return secrets.get("ANTHROPIC_API_KEY")
    except Exception as e:
        raise ValueError(f"ANTHROPIC_API_KEY not found in environment variables or AWS Secrets Manager: {e}")

def get_serper_api_key():
    """Get Serper API key from AWS Secrets Manager or environment"""
    # First try environment variable (for local development)
    key = os.getenv("SERPER_API_KEY")
    if key:
        return key
    
    # Then try AWS Secrets Manager
    try:
        secrets = get_secret_from_aws("ResearchAgentSecrets")
        return secrets.get("SERPER_API_KEY")
    except Exception as e:
        raise ValueError(f"SERPER_API_KEY not found in environment variables or AWS Secrets Manager: {e}")

def get_claude_model_name():
    """Return the Claude model name"""
    return "claude-3-haiku-20240307"

def pretty_print_result(result):
    import json
    print(json.dumps(result, indent=2))