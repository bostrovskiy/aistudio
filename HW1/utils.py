import os
import json

def get_openai_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    return key

def get_serper_api_key():
    key = os.getenv("SERPER_API_KEY")
    if not key:
        raise ValueError("SERPER_API_KEY not found in environment variables.")
    return key

def pretty_print_result(result):
    import json
    print(json.dumps(result, indent=2))