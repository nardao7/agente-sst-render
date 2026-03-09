from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Agente SST online"}

@app.get("/health")
def health():
    return {"status": "ok"}
