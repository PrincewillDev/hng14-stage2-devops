from fastapi import FastAPI
import redis
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), 
                port=6379, 
                password=os.getenv("REDIS_PASSWORD"))


@app.post("/jobs")
def create_job():
    job_id = str(uuid.uuid4())
    r.lpush("job", job_id)
    r.hset(f"job:{job_id}", "status", "queued")
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    status = r.hget(f"job:{job_id}", "status")
    if not status:
        return {"error": "not found"}
    return {"job_id": job_id, "status": status.decode()}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
