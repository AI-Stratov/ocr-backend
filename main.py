import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.app:app", log_level="info")
    #host="157.230.23.195"