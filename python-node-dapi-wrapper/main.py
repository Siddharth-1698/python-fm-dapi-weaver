from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()
app.include_router(router, prefix="/api")

@app.get("/")
async def home():
    try:
        return "Python-node-dapi-server is running"
    except Exception as e:
        return {"message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
