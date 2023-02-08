from fastapi import FastAPI, HTTPException, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from PIL import Image
import time
from jinja2 import Environment, FileSystemLoader
import os
import imghdr
import motor.motor_asyncio
from beanie import PydanticObjectId, init_beanie
from fastapi_users.db import BeanieBaseUser, BeanieUserDatabase
from fastapi_users.authentication import BearerTransport
from fastapi_users_db_beanie.access_token import (
    BeanieAccessTokenDatabase,
    BeanieBaseAccessToken,
)
from fastapi_users.authentication.strategy.db import AccessTokenDatabase, DatabaseStrategy

async def get_access_token_db():  
    yield BeanieAccessTokenDatabase(AccessToken)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db)


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,  
        document_models=[
            User,  
        ],
    )


@app.get("/profile/{user_id}")
def get_user(user_id: int):
    return [user for user in fake_db if user.get('id') == user_id]


@app.post("/image/")
async def image(file: UploadFile, x: int, y: int, width: int, height: int):
    global start_time
    start_time = time.time()
    if not is_valid_image(file.file):
        return JSONResponse(content={"error": "The file you uploaded is not an image"})
    image_bytes = await file.read()
    file.seek(0)
    file_size = len(image_bytes)
    if file_size > 5 * 1024 * 1024:
        return JSONResponse(content={"error": "The file you uploaded is too big"})
    image_path = "saved_data\image.jpg"
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    text = process_images(x, y, width, height, image_path)
    return {"text": text}

def process_images(x: int, y: int, width: int, height: int, image_path: str) -> str:
    crop_image(image_path, "prepared_data\image.jpg", x, y, width, height)
    text = reader.readtext(f"prepared_data\image.jpg", detail=0)
    os.remove("prepared_data\image.jpg")
    os.remove("saved_data\image.jpg")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Elapsed time: ", elapsed_time)
    return text

def crop_image(image_path, new_file_path, x, y, width, height):
    with Image.open(image_path) as image:
        cropped_image = image.crop((x, y, x + width, y + height))
        cropped_image.save(new_file_path)

def is_valid_image(file):
    return imghdr.what(file) in ["jpeg", "png", "bmp", "webp"]

@app.get("/")
async def main():
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("main.html")
    content = template.render()
    return HTMLResponse(content=content)