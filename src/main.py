from enum import Enum

from fastapi import FastAPI


class ModelName(str, Enum):
    chatGpt = "chatgpt"
    llama = "llama"

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World!!"}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item": item_id}

@app.get("/users/me")
async def get_current_user():
    return {"user": "current_user"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    return {"user": user_id}


@app.get("/models/{model_id}")
async def get_model(model_id: ModelName):
    if model_id == ModelName.chatGpt:
        return {"model": ModelName.chatGpt}
    if model_id == ModelName.llama:
        return {"model": ModelName.llama}
    return {"model": "unknown"}


@app.get("/fake_params/")
async def fake_params(start: int= 0, limit: int = 10):
    return {"start": start, "limit": limit}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)