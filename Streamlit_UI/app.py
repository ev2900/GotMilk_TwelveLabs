#
# streamlit run app.py
#

import streamlit as st
import boto3
from boto3.dynamodb.conditions import Key
import pandas as pd
import json
from twelvelabs import TwelveLabs

# --- AWS Session ---
session = boto3.Session(
    aws_access_key_id="<aws_access_key_id>",
    aws_secret_access_key="<aws_secret_access_key>",
    region_name="<region_name>"
)

# --- Streamlit UI setup ---
st.set_page_config(
    page_title="Blank Streamlit App",
    layout="wide"
)

st.title("Got Milk?")
st.write("A simple application to manage the #GotMilk? social media campaign")

# --- Build DynamoDB resource ---
dynamodb = session.resource("dynamodb")

# --- Scan table helper ---
def scan_table(ddb_table):
    items = []
    response = ddb_table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = ddb_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items

# ---------- simple_checks_indexing ----------
simple_checks_indexing = dynamodb.Table("simple_checks_indexing")
simple_checks_indexing_data = scan_table(simple_checks_indexing)

rows = []
for item in simple_checks_indexing_data:
    rows.append({
        "video_id": item.get("video_id", ""),
        #"index_id": item.get("index_id", ""),
        "account": item.get("metadata", {}).get("account", ""),
        "tags": ", ".join(item.get("metadata", {}).get("tags", [])),
        "bucket": item.get("bucket", ""),
        "s3_path": item.get("s3_path", ""), 
        #if isinstance(item.get("metadata", {}).get("tags", []), list) else ""
    })

df = pd.DataFrame(rows)

st.subheader("Videos that are indexed")
st.write("These are the videos that are uploaded to the S3 bucket and passed the initial metadata check for having the #gotmilk? and/or #milkmob hashtags. After passing the metadata checks these videos have been indexed for subsequent analysis.")
st.dataframe(df, width='stretch', hide_index=True)

# ---------- is_part_of_campaign ----------
is_part_of_campaign = dynamodb.Table("is_part_of_campaign")
is_part_of_campaign_data = scan_table(is_part_of_campaign)

rows = []
for item in is_part_of_campaign_data:
    rows.append({
        "video_id": item.get("video_id", ""),
        #"index_id": item.get("index_id", ""),
        "analyze_yes_count": item.get("analyze_yes_count", ""),
        "is_part_of_campaign": item.get("is_part_of_campaign", ""),
        "bucket": item.get("bucket", ""),
        "s3_path": item.get("s3_path", ""),
    })

df = pd.DataFrame(rows)

st.subheader("Videos that ARE a part of the Got Milk? campaign")
st.markdown('''To validate if the videos with the #gotmilk? and/or #milkmob hashtags are actually part of the social media campaign, we use the Twelve Labs model to ask 3 yes/no questions: \n\n
    1. Is drinking milk depicted in the video? \n
    2. Are the words 'milk' or the phrase 'got milk' spoken in the audio? \n
    3. Does the text got milk? appear in the video? \n\n

If the answer to 2/3 of these questions is Yes. It is considered part of the campaign.''')

st.dataframe(df, width='stretch', hide_index=True)

# ---------- milk_mob ----------
milk_mob = dynamodb.Table("milk_mob")
milk_mob_data = scan_table(milk_mob)

rows = []
for item in milk_mob_data:
    rows.append({
        "video_id": item.get("video_id", ""),
        "title": item.get("Title", ""),
        "Topics": item.get("Topics", ""),
        "Hashtags": item.get("Hashtag", ""),
    })

df = pd.DataFrame(rows)

st.subheader("Generated information about the Got Milk? videos")
st.write("For the videos that are part of the Got Milk? campaign, TwelveLabs is used to create a title, identify the primary topic and hashtags.")
st.write("Additionally, behind the scenes an embedding is created for each video to power the similarity search in next step.")
st.dataframe(df, width='stretch', hide_index=True)

# ---------- vector_search ----------
st.divider()
st.header("Milk Mobs! via. S3 Vector Search")
st.write("Each video has a vector representation, we can search with any of hashtags and get a list of similar videos, which can represent the milk mob for that hashtag.")

# Simple UI controls
text_query = st.text_input("Enter a text search query")
k = st.slider("Top K results", min_value=1, max_value=25, value=3)

run_search = st.button("Run Search", type="primary")

if run_search:
    # 1) TEXT -> embedding via TwelveLabs Marengo 3.0
    with st.spinner("Creating text embedding with TwelveLabs..."):
        tl_client = TwelveLabs(api_key="<api_key>")

        text_embed = tl_client.embed.create(
            model_name="marengo3.0",
            text=text_query
        )

        query_vector = text_embed.text_embedding.segments[0].float_
        st.write(f"Text embedding dimension: **{len(query_vector)}**")

    # 2) embedding -> S3 Vectors Query
    with st.spinner("Searching S3 Vector index..."):

        s3v = session.client("s3vectors")
        #s3v = boto3.client("s3vectors", region_name="us-east-1")

        resp = s3v.query_vectors(
            vectorBucketName="got-milk",
            indexName="visual-video",
            queryVector={"float32": query_vector},
            topK=k,
            returnDistance=True
        )

    results = resp.get("vectors", [])
    #print(json.dumps(resp, indent=2))

    if not results:
        st.info("No matches returned.")
    else:
        # 3) Show results in a visual table
        vectors = resp.get("vectors", [])

        df_results = pd.DataFrame(
            [{"key": v.get("key"), "distance": v.get("distance")} for v in vectors]
        ).sort_values("distance")  # cosine distance: lower = more similar

        st.subheader("#MilkMob")
        st.dataframe(df_results, width='stretch', hide_index=True)
