# api_main.py - simple orchestrator to spawn bot containers
import os, uuid, json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import docker
import redis

app = FastAPI()
client = docker.from_env()
r = redis.Redis(host=os.getenv("REDIS_HOST","redis"), port=int(os.getenv("REDIS_PORT",6379)))

class CreateReq(BaseModel):
    meet_url: str
    env: dict = {}

@app.post("/v1/session")
def create_session(req: CreateReq):
    session_id = str(uuid.uuid4())
    env = {
        "SESSION_ID": session_id,
        "MEET_URL": req.meet_url,
        **req.env
    }
    try:
        container = client.containers.run(
            image="meet-bot-image:latest",
            detach=True,
            environment=env,
            auto_remove=True,
            name=f"meet_bot_{session_id[:8]}",
            # limit resources as needed
            mem_limit="2g",
            cpus=1.0
        )
        r.hset(f"session:{session_id}", mapping={"container_id": container.id, "status": "running"})
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/session/{session_id}")
def get_session(session_id: str):
    data = r.hgetall(f"session:{session_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return {k.decode(): v.decode() for k,v in data.items()}
