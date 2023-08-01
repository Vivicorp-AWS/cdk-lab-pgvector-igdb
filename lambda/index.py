# Blank Lambda function ref: https://github.com/awsdocs/aws-lambda-developer-guide/blob/main/sample-apps/blank-python/function/lambda_function.py
import logging
import os
import boto3  # type: ignore
import jsonpickle  # type: ignore
import json
import psycopg  # type: ignore
from pgvector.psycopg import register_vector  # type: ignore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secretsmanager = boto3.client('secretsmanager')
s3 = boto3.client('s3')

# Load Environment Variables
DB_SECRET_ARN = os.environ['DB_SECRET_ARN']
BUCKET_NAME = os.environ['BUCKET_NAME']

def handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES\r' + jsonpickle.encode(dict(**os.environ)))
    logger.info('## EVENT\r' + jsonpickle.encode(event))
    logger.info('## CONTEXT\r' + jsonpickle.encode(context))

    # Get Database Credentials
    logger.info('## Getting Database Credentials')
    db_secret = secretsmanager.get_secret_value(
        SecretId=DB_SECRET_ARN,
    )
    db_secret_string = json.loads(db_secret['SecretString'])
    db_secret_string
    db_host = db_secret_string['host']
    db_port = db_secret_string['port']
    db_user = db_secret_string['username']
    db_pass = db_secret_string['password']

    # Download Data Files
    logger.info('## Downloading Data Files')
    s3.download_file(BUCKET_NAME, 'nintendo_switch_games_mean_pooling.json', '/tmp/nintendo_switch_games_mean_pooling.json')

    # Load JSON Data into Dict
    logger.info('## Importing Data Files')
    with open('/tmp/nintendo_switch_games_mean_pooling.json') as file:
        games = json.loads(file.read())

    # Import Dict Data into Database
    logger.info('## Importing Data into Database')
    with psycopg.connect(host=db_host, user=db_user, password=db_pass, port=db_port, connect_timeout=10, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            register_vector(conn)

            # Create IGDB table
            cur.execute("DROP TABLE IF EXISTS igdb")
            cur.execute("""CREATE TABLE IF NOT EXISTS igdb(
                        igdb_id bigserial primary key, 
                        name text,
                        summary text,
                        description text,
                        url text,
                        artwork_hash text,
                        screenshot_hash text,
                        description_embeddings vector(384));""")

            # Insert data into IGDB table
            for row in games:
                igdb_id, name, summary, description, url, artwork_hash, screenshot_hash, description_embeddings = row
                cur.execute("""INSERT INTO igdb
                                (igdb_id, name, summary, description, url, artwork_hash, screenshot_hash, description_embeddings) 
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s);""", 
                            (igdb_id, name, summary, description, url, artwork_hash, screenshot_hash, description_embeddings,))
            
            # # Create L2 distance index
            # cur.execute("""CREATE INDEX ON igdb 
            #        USING ivfflat (description_embeddings vector_l2_ops) WITH (lists = 100);""")  # Index name: igdb_description_embeddings_idx
            # cur.execute("VACUUM ANALYZE igdb;")
            
            # Create Cosine distance index
            cur.execute("""CREATE INDEX ON igdb 
                USING ivfflat (description_embeddings vector_cosine_ops) WITH (lists = 100);""")  # Index name: igdb_description_embeddings_idx
            cur.execute("VACUUM ANALYZE igdb;")
    
    logger.info('## Process Finished.')