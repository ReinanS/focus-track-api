from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from focus_track_api.routers import (
    auth,
    daily_summary,
    study_session,
    user_settings,
    users,
)
from focus_track_api.schemas.shared import Message

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(user_settings.router)
app.include_router(study_session.router)
app.include_router(daily_summary.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá Mundo!'}
