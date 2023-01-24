from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import easyocr
from PIL import Image
import time
from jinja2 import Environment, FileSystemLoader
import os
import imghdr

app = FastAPI()
reader = easyocr.Reader(["en"], "en")
start_time = time.time()


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
    template = env.get_template("template.html")
    content = template.render()
    return HTMLResponse(content=content)
