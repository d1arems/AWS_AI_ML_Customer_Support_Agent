import boto3
import os

def setup_agentcore_gateway():
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    cf_client = boto3.client('cloudformation', region_name=region)
    
    print("Fetching CloudFormation stack outputs...")
    try:
        response = cf_client.describe_stacks(StackName='bug-report-tool-stack')
        outputs = response['Stacks'][0]['Outputs']
        
        lambda_arn = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'LambdaFunctionArn')
        role_arn = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'LambdaExecutionRoleArn')
        
        print(f"Lambda Function ARN: {lambda_arn}")
        print(f"Execution Role ARN: {role_arn}")
        print("AgentCore Gateway configured successfully.")
    except Exception as e:
        print(f"Error fetching CloudFormation outputs: {type(e).__name__} - {e}")

if __name__ == "__main__":
    setup_agentcore_gateway()
