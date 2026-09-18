from fastapi import FastAPI, Request
import random
import time
import asyncio

app = FastAPI(title="Mock Game Server")


@app.post("/player/action")
async def player_action(request: Request):
    payload = await request.json()
    await asyncio.sleep(0.01)
    return {
        "status": "ok",
        "action": payload.get("action"),
        "server_tick": int(time.time() * 1000),
    }


@app.get("/player/state")
async def player_state():
    return {
        "hp": random.randint(50, 100),
        "position": {"x": random.uniform(0, 100), "y": random.uniform(0, 100)},
    }
