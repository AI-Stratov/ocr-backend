import os
from beanie import init_beanie
from fastapi import Depends, FastAPI, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
import easyocr
import imghdr
from jinja2 import Environment, FileSystemLoader
from app.db import User, db
from PIL import Image
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users

app = FastAPI()
reader = easyocr.Reader(["en"], gpu=False)


app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,
        document_models=[
            User,
        ],
    )


@app.post("/image/")
async def image(file: UploadFile, x: int, y: int, width: int, height: int):
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