from fastapi import FastAPI

app = FastAPI(title="Finlens Fraud Service")


@app.get("/health")
async def health():
    return {"status": "ok"}