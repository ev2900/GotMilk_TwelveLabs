'''
NOTE - this is the code for the first lambda function simple_checks_indexing. There are additonal setting ex. S3 trigger that are not captured in this code. These are captured in the CloudFormation stack gotmilk_twelvelabs.yaml. I a copy of the Lambda code here for easier viewing
''' 

import json
import urllib.parse
import boto3
import os

from twelvelabs import TwelveLabs
from twelvelabs.tasks import TasksRetrieveResponse

def lambda_handler(event, context):  
    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")
    
    print("=== FULL S3 EVENT ===")
    print(json.dumps(event))

    # Process all S3 records (in case multiple files are uploaded at once)
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        print(f"Bucket: {bucket}")
        print(f"Key: {key}")

        print("=== Check metadata (json file) ===")
        json_key = key.rsplit('.', 1)[0] + ".json"   # replace .mp4 with .json

        print(f"Looking for JSON metadata file: {json_key}")
            
        json_obj = s3.get_object(Bucket=bucket, Key=json_key)
        json_data = json_obj['Body'].read().decode('utf-8')
        metadata = json.loads(json_data)

        print("=== JSON Metadata ===")
        print(json.dumps(metadata))

        # Check for required tags
        tags = metadata.get("tags", [])
        tags_lower = [t.lower() for t in tags]
        has_tag = ("#gotmilk?" in tags_lower) or ("#milkmob" in tags_lower)
        
        if not has_tag:
            print(f"Skipping {key}: missing required tag")
            continue

        # Check for excluded accounts
        account = metadata.get("account", "")
        excluded_accounts = ["BadAccount1", "BadAccount2"]

        if account in excluded_accounts:
            print(f"Skipping {key}: excluded account {account}")
            continue

        print("=== GET S3 PRESIGNED URL ===")
        # Generate 15-minute presigned URL
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=900  # 900 seconds = 15 minutes
        )

        print("Generated Presigned URL:")
        print(url)

        print("=== INDEXING ===")
        # Initialize the clien
        client = TwelveLabs(api_key=os.environ["API_KEY"])

        # Upload a video
        task = client.tasks.create(
            index_id=os.environ["INDEX_ID"],
            video_url=url
        )
        print(f"Created task: id={task.id}")
    
        # Monitor the indexing process
        def on_task_update(task: TasksRetrieveResponse):
            print(f"Status={task.status}")

        task = client.tasks.wait_for_done(task_id=task.id, callback=on_task_update)

        if task.status != "ready":
            raise RuntimeError(f"Indexing failed with status {task.status}")
    
        print(f"Upload complete. The unique identifier of your video is {task.video_id}.")
    
        print("=== WRITE TO DYNAMODB ===")
        table = dynamodb.Table("simple_checks_indexing")
    
        item = {
            "s3_path": key,
            "video_id": task.video_id,
            "index_id": os.environ["INDEX_ID"],
            "bucket": bucket,                 
            "metadata": metadata,
            "s3_prefix": key
        }

        table.put_item(Item=item)
        print("Wrote item to DynamoDB")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda execution complete')
    }
