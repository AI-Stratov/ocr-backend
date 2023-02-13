import imghdr
import os

import easyocr
from beanie import init_beanie
from fastapi import Depends, FastAPI, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader
from PIL import Image

from .db import User, db
from .schemas import UserCreate, UserRead
from .users import auth_backend, current_active_user, fastapi_users

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


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,
        document_models=[
            User,
        ],
    )


@app.post("/image/")
async def image(
    file: UploadFile,
    x: int,
    y: int,
    width: int,
    height: int,
    user: User = Depends(current_active_user),
):
    # Check if the file is jpg or png
    if not is_valid_image_type(file.file):
        return JSONResponse(
            content={
                """"Еrror":
            "Unsopported type of image.
            Check that your image is .jpg or .png
            """
            }
        )
    # Check if the file size is not bigger than 5 MB
    image_bytes = await file.read()
    if is_valid_size(file.file) > 5 * 1024 * 1024:
        return JSONResponse(
            content={
                """
            "error":
            "The file you uploaded is too big"
            """
            }
        )
    # If the image is .png, call the convert func
    if imghdr.what(file.file) in ["png"]:
        image_path = await image_convert(file)
        image_type = "png"
    else:
        image_path = f"saved_data/{file.filename}.jpg"
        image_type = "jpg"
        with open(image_path, "wb") as f:
            f.write(image_bytes)
    text = await process_images(x, y, width, height, image_path, image_type, file)
    return {"text": text}


async def image_convert(file: UploadFile):
    image_bytes = await file.read()
    image_path = f"saved_data/{file.filename}.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    image_path = f"saved_data/{file.filename}.png"
    return image_path


async def process_images(
    x: int, y: int, width: int, height: int, image_path: str, image_type: str, file
) -> str:
    await crop_image(
        image_path, f"prepared_data/{file.filename}.{image_type}", x, y, width, height
    )
    text = reader.readtext(f"prepared_data/{file.filename}.{image_type}", detail=0)
    os.remove(f"prepared_data/{file.filename}.{image_type}")
    os.remove(f"saved_data/{file.filename}.{image_type}")
    return text


async def crop_image(image_path, new_file_path, x, y, width, height):
    with Image.open(image_path) as image:
        cropped_image = image.crop((x, y, x + width, y + height))
        cropped_image.save(new_file_path)


def is_valid_image_type(file):
    return imghdr.what(file) in ["jpeg", "png"]


def is_valid_size(file):
    image_bytes = file.read()
    file.seek(0)
    file_size = len(image_bytes)
    return file_size


# @app.get("/")
# async def main():
#     env = Environment(loader=FileSystemLoader("templates"))
#     template = env.get_template("main.html")
#     content = template.render()
#     return HTMLResponse(content=content)

# curl -X 'POST' 'http://127.0.0.1:8000/image/?x=111&y=111&width=111&height=111' -H 'accept: application/json' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2M2U3Nzc3MTZhOWVjMmZhOTRjNTljZWEiLCJhdWQiOlsiZmFzdGFwaS11c2VyczphdXRoIl0sImV4cCI6MTY3OTg5MTk4OH0.zkWJFaUdtQfXlCNWzibG6WgjwcFwGrjMRZIkHPe6hP0' -H 'Content-Type: multipart/form-data' -F 'file=@C:/Users/Андрей/Desktop/test_data/conduct.jpg;type=image/jpeg'
