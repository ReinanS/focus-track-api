from http import HTTPStatus
from fastapi import APIRouter, HTTPException

from focus_track_api.schemas import Message, UserDB, UserList, UserPublic, UserSchema

router = APIRouter(
    prefix='/users',
    tags=['users'],
    responses={HTTPStatus.NOT_FOUND: {'description': 'Not found'}},
)

database = []

@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema):
    user_with_id = UserDB(**user.model_dump(), id=len(database) + 1)  
    database.append(user_with_id)

    return user_with_id

@router.get('/', response_model=UserList)
def read_users():
    return {'users': database}

@router.put('/{user_id}', response_model=UserPublic)
def update_user(user_id: int, user: UserSchema):
    if user_id > len(database) or user_id < 1: 
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    
    user_with_id = UserDB(**user.model_dump(), id=user_id)
    database[user_id - 1] = user_with_id
    return user_with_id

@router.delete('/{user_id}', response_model=Message)
def delete_user(user_id: int):
    if user_id > len(database) or user_id < 1: 
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    
    del database[user_id - 1]
    return {'message': 'User deleted'}