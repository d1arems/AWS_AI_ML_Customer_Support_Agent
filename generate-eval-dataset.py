import argparse
import json
import boto3
import os

def run_eval_dataset():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests-json", required=True)
    parser.add_argument("--out-jsonl", default="output_eval_dataset.jsonl")
    args, _ = parser.parse_known_args()

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)

    with open("harness_config.json", "r") as f:
        config = json.load(f)

    system_prompt = config["system_prompt"]
    model_id = config.get("model_id", "us.amazon.nova-pro-v1:0")

    with open(args.tests_json, "r") as f:
        tests_data = json.load(f)

    test_cases = tests_data.get("tests", []) if isinstance(tests_data, dict) else tests_data

    out_file = args.out_jsonl
    with open(out_file, "w") as f_out:
        for item in test_cases:
            prompt = item["prompt"]
            expected = item.get("expected", "")

            response = bedrock_runtime.converse(
                modelId=model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": prompt}]}]
            )

            actual_text = ""
            for content_block in response['output']['message']['content']:
                if 'text' in content_block:
                    actual_text += content_block['text']

            eval_record = {
                "prompt": prompt,
                "referenceResponse": expected,
                "modelResponses": [
                    {
                        "response": actual_text,
                        "modelIdentifier": "my-support-chatbot"
                    }
                ]
            }
            f_out.write(json.dumps(eval_record) + "\n")
            print(f"wrote eval line for test ID: {item.get('id', 'test')}")

    print(f"\nDataset successfully written to {out_file}")

if __name__ == "__main__":
    run_eval_dataset()
