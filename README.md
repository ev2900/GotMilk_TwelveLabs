# GotMilk? TwelveLabs

<img width="275" alt="map-user" src="https://img.shields.io/badge/cloudformation template deployments-000-blue"> <img width="85" alt="map-user" src="https://img.shields.io/badge/views-000-green"> <img width="125" alt="map-user" src="https://img.shields.io/badge/unique visits-011-green">

# Overview

I wanted to explore [TwelveLabs](https://www.twelvelabs.io/) capabilities to work with videos. 

I built a solution that solves a fictitious scenario. The scenario:
* A Brand Partnership division is partnering with a brand to re-create a modern version of the iconic got milk? Campaign.
* The team wants to ability to validate if social media posts (.mp4 files) are actually part of their campaign.
* If the social media posts are part of the campaign they want to be able to group posts / understand similiarities on a variety of topics ex. activity, location etc.

# Architecture

The diagram below depicts the technical architecture.

<img width="100%" alt="quick_setup" src="https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/README/architecture.png">

The architecture has 3 major sections which can be conceptualized via. the lambda functions that power the solution.
1. The first lambda function is [simple_checks_indexing](https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/Lambda_Functions/simple_checks_indexing.py)
   * The lambda trigger when a new .mp4 file is upload to /milk folder in the S3 bucket
   * When the lambda triggers it will first open the associated .json file and check the metadata for either the #gotmilk? or #milkmob hashtag
   * IF the #gotmilk? or #milkmob hashtags are present a presigned URL is generated for the .mp4
   * The presigned URL is then used to send a TwelveLabs API call to index the video on an existing TweveLabs video index
   * After the video is successfully indexed a record is added to DynamoDB table simple_checks_indexing. The DynamoDB table includes the videoID from the TweveLabs index 
 
2. The second lambda function is [is_part_of_campaign](https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/Lambda_Functions/is_part_of_campaign.py)
   * The lambda function is trigger by a record being inserted into the DynamoDB table simple_checks_indexing
   * When the lambda triggers it will use the TweveLabs API to prompt the video with 3 question "Is drinking milk depicted in the video? Answer Yes or No.", "Does the text got milk? appear in the video? Answer Yes or No.", "Are the words 'milk' or the phrase 'got milk' spoken in the audio? Answer Yes or No." 
   * If 2/3 prompts return Yes a recorded is added to the DynamoDB table is_part_of_campaign

3. The third lambda function is [title_topic_hastags_embeddings](https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/Lambda_Functions/title_topic_hastags_embeddings.py)  
    * The lambda function is trigger by a record being inserted into the DynamoDB table is_part_of_campaign
    * When the lambda triggers it will call the TwelveLabs API to generate titles, topics, hashtags and write this output to the DynamoDB table milk_mob
    * The Lambda will also trigger an API call to get an embedding of the .mp4 and load the visual-video embedding to an S3 vector index  

There is a user interface that will let you easily see the content of the DynamoDB tables and run vector search agains the S3 vector bucket index. This is hosted via. Streamlite on your localhost. The code for this UI is [HERE[(https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/Streamlit_UI/app.py). Instructions to host the UI are at the end of the [Deploying the Solution](https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/Streamlit_UI/app.py). 

# Deploying the Solution

Click the button below to deploy the [gotmilk_twelvelabs.yaml](https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/gotmilk_twelvelabs.yaml) CloudFormation. This will deploy all of the components pictured in the architecture.

> [!WARNING]
> The CloudFormation stack creates IAM role(s) that have ADMIN permissions. This is not appropriate for production deployments. Scope these roles down before using this CloudFormation in productio

[![Launch CloudFormation Stack](https://sharkech-public.s3.amazonaws.com/misc-public/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=gotmilk-twelvelabs&templateURL=https://sharkech-public.s3.amazonaws.com/misc-public/gotmilk_twelvelabs.yaml)


