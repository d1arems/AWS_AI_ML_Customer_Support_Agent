import boto3
import json
import os
import subprocess

def prepare_agentcore_harness():
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    cf_client = boto3.client('cloudformation', region_name=region)
    
    print("1. Reading system_prompt.txt and embedding online_shop_faq.md...")
    with open("system_prompt.txt", "r") as f:
        prompt_content = f.read()
    with open("online_shop_faq.md", "r") as f:
        faq_content = f.read()
        
    final_prompt = prompt_content.replace("{{FAQ}}", faq_content)
    
    print("2. Ensuring AgentCore Gateway is provisioned...")
    try:
        subprocess.run(["python3", "setup_gateway.py"], check=True)
    except Exception as e:
        print(f"Gateway setup script note: {e}")

    print("3. Fetching Lambda Function ARN from CloudFormation...")
    try:
        response = cf_client.describe_stacks(StackName='bug-report-tool-stack')
        outputs = response['Stacks'][0]['Outputs']
        lambda_arn = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'LambdaFunctionArn')
        print(f"Lambda Tool ARN: {lambda_arn}")
    except Exception as e:
        print(f"Error fetching CloudFormation outputs: {e}")
        return

    config = {
        "system_prompt": final_prompt,
        "lambda_arn": lambda_arn,
        "region": region,
        "model_id": "us.amazon.nova-pro-v1:0"
    }
    
    with open("harness_config.json", "w") as f:
        json.dump(config, f, indent=2)
        
    print("AgentCore Harness compiled successfully to harness_config.json!")

if __name__ == "__main__":
    prepare_agentcore_harness()
