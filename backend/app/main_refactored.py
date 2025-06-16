from fastapi import FastAPI

app = FastAPI(title="Refactored App")

@app.get("/")
async def root():
    return {"message": "Hello World - Refactored"} 