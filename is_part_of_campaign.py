'''
NOTE - this is the code for the first lambda function simple_checks_indexing. There are additonal setting ex. S3 trigger that are not captured in this code. These are captured in the CloudFormation stack gotmilk_twelvelabs.yaml. I a copy of the Lambda code here for easier viewing
'''

import json
import boto3
import os

from twelvelabs import TwelveLabs

def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")

    print("=== FULL DynamoDB EVENT ===")
    print(json.dumps(event))

    client = TwelveLabs(api_key=os.environ["API_KEY"])

    for record in event.get("Records", []):

        # Skip anything that is NOT an INSERT
        if record["eventName"] != "INSERT":
            print(f"Skipping event {record['eventName']}")
            continue

        video_id = record["dynamodb"]["NewImage"]["video_id"]["S"]

        print("Processing INSERT for video_id:", video_id)

        yes_count = 0

        print("=== Is drinking milk depicted in the video? ===")
        res1 = client.analyze(
            video_id=video_id,
            prompt="Is drinking milk depicted in the video? Answer Yes or No.",
            temperature=0
        )
        answer1 = res1.data.strip().lower()
        print("Answer1:", answer1)

        if "yes" in answer1:
            yes_count += 1

        print("=== Does the text 'got milk?' appear in the video? ===")
        res2 = client.analyze(
            video_id=video_id,
            prompt="Does the text got milk? appear in the video? Answer Yes or No.",
            temperature=0
        )
        answer2 = res2.data.strip().lower()
        print("Answer2:", answer2)

        if "yes" in answer2:
            yes_count += 1

        print("=== Are the words 'milk' or the phrase 'got milk' spoken in the audio? ===")
        res3 = client.analyze(
            video_id=video_id,
            prompt="Are the words 'milk' or the phrase 'got milk' spoken in the audio? Answer Yes or No.",
            temperature=0
        )
        answer3 = res3.data.strip().lower()
        print("Answer3:", answer3)

        if "yes" in answer3:
            yes_count += 1

        # Final Decision
        if yes_count >= 2:
            print("At least 2/3 answers are YES")
            table = dynamodb.Table("is_part_of_campaign")

            # Insert a brand new document
            table.put_item(
                Item={
                    "video_id": video_id,
                    "s3_path": record["dynamodb"]["NewImage"]["s3_path"]["S"],
                    "bucket": record["dynamodb"]["NewImage"]["bucket"]["S"],
                    "metadata": record["dynamodb"]["NewImage"]["metadata"]["M"],
                    "index_id": record["dynamodb"]["NewImage"]["index_id"]["S"],
                    "is_part_of_campaign": True,
                    "analyze_yes_count": yes_count,
                    "s3_prefix": record["dynamodb"]["NewImage"]["s3_prefix"]["S"]
                }
            )
            print(f"Inserted into is_part_of_campaign for video_id={video_id}")

        else:
            print("Less than 2/3 answers are YES")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Lambda execution complete')
    }
