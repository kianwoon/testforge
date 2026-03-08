import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NanoClow Agent")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
