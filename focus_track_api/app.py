from http import HTTPStatus
from fastapi import FastAPI

from focus_track_api.routers import attention, users
from focus_track_api.schemas import Message

app = FastAPI()

app.include_router(attention.router)
app.include_router(users.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá Mundo!'}
