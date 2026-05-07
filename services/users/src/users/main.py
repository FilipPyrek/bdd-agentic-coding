from fastapi import FastAPI

from users.routes import router

app = FastAPI()
app.include_router(router)
