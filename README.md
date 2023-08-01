# CDK Lab - AI-powered Search Solution with PostgreSQL & pgvector<!-- omit from toc -->

When we talk about NLP techniques and Large Language Models (LLM), a common way to build a search engine application is transforming the text data into vector embeddings, then calculate the similarity between the embeddings. 

Dedicated vector database like [Pinecone](https://www.pinecone.io) and [Faiss](https://github.com/facebookresearch/faiss) are good choices for storing and making search, but we still want to use regular relational databases because they are more common to be used. With [pgvector](https://github.com/pgvector/pgvector), this extension gives PostgreSQL the power to easily store vector data and make search with them.

This project refers to a [solution delivered by AWS: "Building AI-powered search in PostgreSQL using Amazon SageMaker and pgvector"](https://aws.amazon.com/blogs/database/building-ai-powered-search-in-postgresql-using-amazon-sagemaker-and-pgvector/) ([GitHub Repo](https://github.com/aws-samples/rds-postgresql-pgvector)), and makes some improvements to make it more efficient, including:

* Use CDK to deploy the whole stack instead of deployed with CloudFormation template
* Provide a sample dataset with [IDGB's data](https://www.igdb.com), and use a Lambda function to import them into PostgreSQL database when initializing the database instance which saves a lot of time
  * And it's easy to replace the data so you can import your own
  * If you're interested in the way to produce the sample dataset, it's put in [another repo](https://github.com/VioletVivirand/igdb-data-demo)
* Change the model endpoint to a Serverless one to lower the inferencing cost
* Add a little inference application built with [Gradio](https://www.gradio.app)

<!-- TODO: Architeture Chart -->

- [Components to be deployed](#components-to-be-deployed)
- [File Structure](#file-structure)
- [Usage](#usage)
  - [Step 0: Prepare the credentials](#step-0-prepare-the-credentials)
  - [Step 1: Fill in the necessary information into CDK runtime context](#step-1-fill-in-the-necessary-information-into-cdk-runtime-context)
  - [Step 2: Archive the model, and download the sample dataset files](#step-2-archive-the-model-and-download-the-sample-dataset-files)
  - [Step 3: Deploy with CDK toolkit (`cdk` command)](#step-3-deploy-with-cdk-toolkit-cdk-command)
  - [Step 4: Make inferences](#step-4-make-inferences)
  - [(Optional) Step 5: Clean all resources](#optional-step-5-clean-all-resources)
- [Future Improvement Suggestions](#future-improvement-suggestions)
  - [Security](#security)
  - [The Performance of the Search Function is not good enough](#the-performance-of-the-search-function-is-not-good-enough)


## Components to be deployed

* A **VPC** with 2 Available Zone, and each az contains 2 subnets (1 public and 1 private)
* A **RDS for PostgreSQL database instance** which is compitable for pgvector extension
* A **Lambda function** that can import database automatically after the database is initialized compleleted
* A **Serverless SageMaker Model Endpoint** with the "[all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)" pre-trained SentenceTransformers model, which is balanced in performance and speed
* A **SageMaker Notebook instance** to make inference or interact with the model endpoint

## File Structure

```
├── README.md
├── app.py                                       ## Entrypoint
├── assets
│   ├── nintendo_switch_games.csv                ## The source dataset
│   ├── nintendo_switch_games_cls_pooling.json   ## Dataset with embeddings processed with only CLS pooling
│   └── nintendo_switch_games_mean_pooling.json  ## Dataset with embeddings processed with Mean pooling
├── cdk.context.json.example                     ## Example CDK runtime context file
├── lambda
│   ├── __init__.py
│   └── index.py                                 ## Lambda funciton to import sample dataset into database
├── model
│   └── code                                     ## Custom inference script for HuggingFace model
├── notebooks
│   ├── 1-get-embeddings-and-import.ipynb        ## Example notebook to create and import embeddings
│   ├── 2-1-inference-in-notebook.ipynb          ## Example notebook to make inferences inline
│   └── 2-2-inference-with-gradio.ipynb          ## Example notebook to make inference with Gradio app
├── poetry.lock
├── pyproject.toml
├── requirements-layer.txt                       ## Lambda function's Python dependencies list
├── requirements.txt
├── scripts
│   └── get_assets.sh                            ## Script to archive model into a single file and download sample datasets
└── stacks
    ├── __init__.py
    ├── lambda_stack.py
    ├── rds_stack.py
    ├── s3_stack.py
    ├── sagemaker_stack.py
    ├── top_stack.py
    └── vpc_stack.py
```

## Usage

### Step 0: Prepare the credentials

Create the config file by executing:

```bash
aws configure
```

### Step 1: Fill in the necessary information into CDK runtime context

Copy the example CDK runtime context file `cdk.context.json.example` to `cdk.context.json`, fill in the **Region** and **Stack Prefix** information, for example:

```
{
  "region": "us-east-1",
  "prefix": "yet-another-cdk-project"
}
```

### Step 2: Archive the model, and download the sample dataset files

Execute the script at the root directory of this project:

```bash
./scripts/get_assets.sh
```

This script will download

1. [The "all-MiniLM-L6-v2" pre-trained SentenceTransformers model artifact from HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
2. [Example IGDB Dataset](https://github.com/VioletVivirand/igdb-data-examples)

All of them are saved in `./assets` directory.

### Step 3: Deploy with CDK toolkit (`cdk` command)

[Install the CDK toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) then deploy by executing:

```bash
cdk deploy --all --require-approval=never
```

### Step 4: Make inferences

After all stacks deployed, visit SageMaker Notebook service page, find the launched Notebook instance with a `pgvectorNotebook` postfix in its name, click "Open Jupyter Lab" link to open Jupyter Lab.

The notebook will automatically clone this repo, get into the `notebooks` directory, choose a notebook that fits your usage:

* `1-get-embeddings-and-import.ipynb`: Create and import embeddings into database
* `*2-1-inference-in-notebook.ipynb`: Make inferences inside the notebook
* `2-2-inference-with-gradio.ipynb`: Make inference with Gradio app

### (Optional) Step 5: Clean all resources

Not going to use these anymore? Remove them with:

```bash
cdk destroy --all
```

## Future Improvement Suggestions

### Security

The default service role for SageMaker might be too large, follow the Least authrorities principle and narrow it down.

### The Performance of the Search Function is not good enough

If we try to search the game with question like "One of the main characters is a man with a red hat" or "A platform game with a pink character" and imagine the answer will be something with [Mario](https://en.wikipedia.org/wiki/Mario) and [Kirby](https://en.wikipedia.org/wiki/Kirby_(character)), the result will let you down.

"[all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)" is a good model, but if we look into the datasets used to train this model...... I'm not sure that if they contain enough gaming data or not. Also, the reasoning ability is definitely not the main feature of it compared to LLMs like GPT-3, GPT-4..., etc.

Maybe improve the results by implementing a Large Language Model in the future.
