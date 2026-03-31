from fastapi import FastAPI
from datetime import datetime
import time

app = FastAPI()
start_time = time.time()

@app.get("/health")
async def health():
    return {
        "nama": "test",
        "nrp": "5025241046",
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time
    }
