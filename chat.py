import boto3
import json
import os
import re

def clean_response_text(text):
    # Remove <thinking>...</thinking> tags if present in output
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    return cleaned.strip()

def run_chat():
    if not os.path.exists("harness_config.json"):
        print("Error: harness_config.json not found. Run 'python create_harness.py' first.")
        return

    with open("harness_config.json", "r") as f:
        config = json.load(f)

    region = config["region"]
    lambda_arn = config["lambda_arn"]
    system_prompt = config["system_prompt"]
    model_id = config.get("model_id", "us.amazon.nova-pro-v1:0")

    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
    lambda_client = boto3.client('lambda', region_name=region)

    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "create_bug_report",
                    "description": "Creates a bug report ticket in DynamoDB once description, stepsToReproduce, and environment are all collected.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": "Bug description"},
                                "stepsToReproduce": {"type": "string", "description": "Steps to reproduce"},
                                "environment": {"type": "string", "description": "User environment"}
                            },
                            "required": ["description", "stepsToReproduce", "environment"]
                        }
                    }
                }
            }
        ]
    }

    messages = []
    print("=" * 60)
    print("AgentCore Chat Client Initialized (Amazon Nova Pro)")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break

            messages.append({"role": "user", "content": [{"text": user_input}]})

            response = bedrock_runtime.converse(
                modelId=model_id,
                system=[{"text": system_prompt}],
                messages=messages,
                toolConfig=tool_config
            )

            response_message = response['output']['message']
            messages.append(response_message)

            for content_block in response_message['content']:
                if 'text' in content_block:
                    text_out = clean_response_text(content_block['text'])
                    if text_out:
                        print(f"\nBot: {text_out}\n")
                elif 'toolUse' in content_block:
                    tool_use = content_block['toolUse']
                    tool_args = tool_use['input']
                    tool_use_id = tool_use['toolUseId']

                    print(f"\n[tool call] bugreports___create_bug_report: {tool_args}")

                    payload = {
                        "messageVersion": "1.0",
                        "function": "create_bug_report",
                        "actionGroup": "bug_report_tool",
                        "parameters": [
                            {"name": k, "value": v} for k, v in tool_args.items()
                        ]
                    }

                    lambda_res = lambda_client.invoke(
                        FunctionName=lambda_arn,
                        InvocationType='RequestResponse',
                        Payload=json.dumps(payload)
                    )
                    res_payload = json.loads(lambda_res['Payload'].read().decode('utf-8'))

                    tool_result_message = {
                        "role": "user",
                        "content": [
                            {
                                "toolResult": {
                                    "toolUseId": tool_use_id,
                                    "content": [{"json": res_payload}]
                                }
                            }
                        ]
                    }
                    messages.append(tool_result_message)

                    followup_res = bedrock_runtime.converse(
                        modelId=model_id,
                        system=[{"text": system_prompt}],
                        messages=messages,
                        toolConfig=tool_config
                    )
                    followup_msg = followup_res['output']['message']
                    messages.append(followup_msg)
                    for text_block in followup_msg['content']:
                        if 'text' in text_block:
                            text_out = clean_response_text(text_block['text'])
                            if text_out:
                                print(f"\nBot: {text_out}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    run_chat()
