from pydantic import BaseModel, EmailStr


class Message(BaseModel):
    message: str


class UserSchema(BaseModel):
    id: str
    username: str
    email: EmailStr
    password: str


class UserDB(UserSchema):
    int: str


class UserPublic(BaseModel):
    username: EmailStr
    email: str


class UserList(BaseModel):
    users: list[UserPublic]
