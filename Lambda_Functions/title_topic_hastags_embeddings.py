'''
NOTE - this is the code for the first lambda function simple_checks_indexing. There are additonal setting ex. S3 trigger that are not captured in this code. These are captured in the CloudFormation stack gotmilk_twelvelabs.yaml. I a copy of the Lambda code here for easier viewing
'''

import json
import boto3
import os

from twelvelabs import TwelveLabs
from twelvelabs.embed import TasksStatusResponse

def lambda_handler(event, context):
  dynamodb = boto3.resource("dynamodb")
  s3 = boto3.client("s3")
  s3vectors = boto3.client("s3vectors")

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
      
      print("=== Title, Topics, Hashtags ===")
      
      res1 = client.gist(
          video_id=video_id,
          types=["title", "topic", "hashtag"]
      )

      title = res1.title
      topics = res1.topics
      hashtags = res1.hashtags

      print("Title: ", title)
      print("Topic: ".join(topics))
      print("Hashtag: ".join(hashtags))

      # Insert into DynamoDB
      table = dynamodb.Table("milk_mob")

      table.put_item(
          Item={
              "s3_path": record["dynamodb"]["NewImage"]["s3_path"]["S"],
              "video_id": video_id,
              "Title": title,
              "Topics": topics,
              "Hashtag": hashtags
          }
      )
      print(f"Inserted into milk_mob for video_id={video_id}")

      print("=== GET S3 PRESIGNED URL ===")
      # Generate 15-minute presigned URL
      url = s3.generate_presigned_url(
          ClientMethod="get_object",
          Params={"Bucket": record["dynamodb"]["NewImage"]["bucket"]["S"], "Key": record["dynamodb"]["NewImage"]["s3_prefix"]["S"]},
          ExpiresIn=900  # 900 seconds = 15 minutes
      )

      print("Generated Presigned URL:")
      print(url)

      print("=== GET Embeding ===")     
      task = client.embed.tasks.create(
          model_name="marengo3.0",
          video_embedding_scope=["video", "clip"],
          video_url=url
      )
      print(f"Created video embedding task: id={task.id}")

      def on_task_update(t: TasksStatusResponse):
          print(f"Status={t.status}")

      status = client.embed.tasks.wait_for_done(
          task_id=task.id,
          sleep_interval=5,
          callback=on_task_update
      )    
      print(f"Embedding done: {status.status}")

      result = client.embed.tasks.retrieve(
          task_id=task.id,
          embedding_option=["visual", "audio", "transcription"]
      )
      #print("Embedding retrieve result:", result)

      visual_video_embedding = None
      for seg in result.video_embedding.segments:
          if seg.embedding_option == "visual" and seg.embedding_scope == "video":
              visual_video_embedding = seg.float_
              break
      print("Embedding dim:", len(visual_video_embedding))
      print(visual_video_embedding)
      
      print("=== INSERT into S3 Table ===")
      response = s3vectors.put_vectors(
          vectorBucketName="got-milk",
          indexName="visual-video",
          vectors=[
              {
                  "key": record["dynamodb"]["NewImage"]["s3_prefix"]["S"],
                  "data": {
                      "float32": visual_video_embedding
                  }
              }
          ]
      )

      print("Upload complete:")
      print(json.dumps(response))
  
  # Return lambda response
  return {
    'statusCode': 200,
      'body': json.dumps('Lambda execution complete')
  }          
