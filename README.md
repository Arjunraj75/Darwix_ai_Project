# Darwix AI Project To - Sales Call Analytics Microservice
A Python microservice to ingest and analyze sales call transcripts and built as a technical assignment.

## Developements 

- **Backend:** ![Python](https://img.shields.io/badge/Python-3.10-blue.svg) & ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
- **Database:** ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue.svg) with ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg) & Alembic
- **AI/ML:** ![Hugging Face](https://img.shields.io/badge/🤗%20Transformers-4.x-yellow.svg), Sentence-Transformers & ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-blue)
- **Containerization:** ![Docker](https://img.shields.io/badge/Docker-20.10-blue.svg) & Docker Compose
---

## Getting Started

Getting the project up and running is pretty straightforward.
All you need is Docker and Docker Compose installed.

### 1. Clone the Repository

```bash
git clone https://github.com/Arjunraj75/Darwix_ai_Project.git
cd Darwix_ai_Project
```

### 2. Set Up Environment Variables this is important to US...

I've included a `.env.example` file. Just copy it to `.env` and you're good to go. The default values should work out of the box.

```bash
cp .env.example .env
```
Optional: If you want to use the OpenAI for coaching nudges, add your API key to the `OPENAI_API_KEY` variable in the `.env` file.

### 3. Build and Run with a Single Command!

I set up a `Makefile` to make life easier. Just run this command to build the containers, run migrations, and start the services.

```bash
make dev-up
```

**What this command does:**
- Builds the `api` Docker image.
- Starts the `database` and `api` services in the background.
- Waits for the database to be ready.
- Runs `alembic upgrade head` to create all the necessary tables.

The API will be available at `http://localhost:9000`.

---

## How to Use

Once the services are up, you can populate the database with synthetic data and run the AI processing.

### 1. Ingest Synthetic Data

Run the ingestion script. This will create 10 agents and 200 call records.

```bash
make ingest-data
```
This runs `python ingest_data.py` inside a temporary container

### 2. Run AI Analytics

Now, process the raw transcripts to generate sentiment scores, embeddings, etc.

```bash
make process-data
```
_(This runs `python process_data.py` inside a temporary container)._

### 3. API Endpoints......

The full interactive documentation is available at **[http://localhost:9000/docs](http://localhost:9000/docs)**.

Here are a few quick `curl` examples:

**Get the agent leaderboard:**
```bash
curl -X GET "http://localhost:9000/api/v1/analytics/agents"
```

**Get the first 5 calls for `agent_001`:**
```bash
curl -X GET "http://localhost:9000/api/v1/calls?agent_id=agent_001&limit=5"
```

**Get recommendations for call with DB ID `1`:**
```bash
curl -X GET "http://localhost:9000/api/v1/calls/1/recommendations"
```

---

## Tearing Down

To stop and remove all the containers, just run:
```bash
make dev-down
```

This will stop the `api` and `database` containers, but your PostgreSQL data will be preserved in a Docker volume. To completely wipe everything, run `make clean`.