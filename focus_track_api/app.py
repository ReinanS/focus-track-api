from fastapi import FastAPI
from focus_track_api.routers import attention

app = FastAPI()

app.include_router(attention.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}
