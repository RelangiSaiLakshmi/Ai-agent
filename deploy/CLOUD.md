# Cloud Deployment Notes (Milestone 4)

The platform ships as a single container image (`Dockerfile`) that can run either
the **REST API** (`uvicorn api.app:app`) or the **dashboard**
(`streamlit run frontend/dashboard.py`). `docker-compose.yml` runs both over a
shared SQLite volume for a self-contained local/VM deployment.

```bash
docker compose up --build
# API  → http://localhost:8000/docs
# Dash → http://localhost:8501
```

## Production considerations

- **Database.** The default is offline-first SQLite (`DB_PATH`), which is fine
  for a single node / demo. For multi-replica cloud deployments, point the app
  at managed Postgres — the schema in `database/schema.sql` uses
  Postgres-compatible shapes, and `database/db.py` is the only module to swap.
- **Model provider.** Set `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` (store
  the key in the cloud secret manager, never in the image).
- **Statelessness.** The API is stateless apart from the database, so it scales
  horizontally behind a load balancer. Human-in-the-loop state lives in the DB
  (`AWAITING_MANAGER`), so any replica can serve the resume call.

## Provider quick-starts

### Azure (Container Apps)
```bash
az acr build -r <registry> -t ai-coordination:latest .
az containerapp create -n ai-coord-api -g <rg> --environment <env> \
  --image <registry>.azurecr.io/ai-coordination:latest \
  --target-port 8000 --ingress external \
  --secrets anthropic-key=<KEY> --env-vars LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=secretref:anthropic-key
```

### AWS (App Runner or ECS/Fargate)
```bash
aws ecr create-repository --repository-name ai-coordination
docker build -t <acct>.dkr.ecr.<region>.amazonaws.com/ai-coordination:latest .
docker push <acct>.dkr.ecr.<region>.amazonaws.com/ai-coordination:latest
# Then create an App Runner service (port 8000) or an ECS/Fargate task from the image.
```

### GCP (Cloud Run)
```bash
gcloud builds submit --tag gcr.io/<project>/ai-coordination
gcloud run deploy ai-coord-api --image gcr.io/<project>/ai-coordination \
  --port 8000 --allow-unauthenticated \
  --set-env-vars LLM_PROVIDER=anthropic --set-secrets ANTHROPIC_API_KEY=anthropic-key:latest
```

## Monitoring / observability

- `GET /health` is a liveness/readiness probe.
- Every run records a structured, per-agent trace on `LeaveState.logs` (returned
  by `POST /requests` as `agent_trace`) — ship these to the platform log sink.
  A LangSmith exporter can attach behind the LangGraph runner without touching
  agent code.
