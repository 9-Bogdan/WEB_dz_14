from typing import List,Optional
from libgravatar import Gravatar
from sqlalchemy.orm import Session
from datetime import date,timedelta
from database.models import User,UserAuth
from schemas import UserSchema, UserModel

async def get_user_by_email(email: str, db: Session) -> User:
    """
    This function takes an email and a db session and returns a user object from the database if it exists with that email address.

    :param email: User email
    :type email: str
    :param db: The database session
    :type db: Session
    :return: A user object from the database if one exists with this email address.
    :rtype: User|None
    """
    return db.query(UserAuth).filter(UserAuth.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Creates a new user in the database

    :param body: A parameter that has already been validated by the user model UserModel from the request body.
    :type body: UserModel
    :param db: The database session
    :type db: Session
    :return: The newly created User object
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = UserAuth(**body.dict(),avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def update_avatar(email, url: str, db: Session) -> User:
    """
    Updates the user's avatar in the database.

    :param email: User email
    :type email: str
    :param url: URL of the image
    :type url: str
    :param db: The database session
    :type db: Session
    :return: the user, with an updated avatar
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def update_token(user: UserAuth, token: str | None, db: Session) -> None:
    """
    Updates the user's refresh_token field and commits the changes to the database.
    
    :param user: User object
    :type user: UserAuth
    :param token: Refresh token
    :type token: str|None
    :param db: The database session
    :type db: Session
    :return: None
    :rtype: None

    """
    user.refresh_token = token
    db.commit()

async def get_users(skip: int, limit: int,user: UserAuth, db: Session) -> List[User]:
    """
    Retrieves a list of users for a specific user with specified pagination parameters.

    :param skip: The number of notes to skip.
    :type skip: int
    :param limit: The maximum number of notes to return.
    :type limit: int
    :param user: The user to retrieve users for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: A list of users.
    :rtype: List[User]
    """
    return db.query(User).offset(skip).limit(limit).all()


async def get_user(user_id: int,user: UserAuth, db: Session) -> User:
    """
    Retrieves a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to retrieve.
    :type note_id: int
    :param user: The user to retrieve the user for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: The user with the specified ID, or None if it does not exist.
    :rtype: User | None
    """
    return db.query(User).filter(User.id == user_id).first()

async def get_birthday(today, end_date,user: UserAuth,db: Session):
    """
    Retrieves the start date and end date.

    :param today: The start date.
    :type today: date
    :param end_date: The end date.
    :type end_date: date
    :param user: The user to retrieve the user for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: A list of users, or None if if there are none.
    :rtype: List[User] | None
    """
    users =  db.query(User).all()
    result = []
    for user in users:
        if (user.birthday_date.month >= today.month and user.birthday_date.day >= today.day and user.birthday_date.month <= end_date.month and user.birthday_date.day <= end_date.day):
            result.append(user)
    return result

async def search_users(first_name:str|None, last_name: str|None,email:str|None,user: UserAuth, db: Session):
    """
    Retrieves the user's first or last name or email, to search for the user by these parameters.

    :param first_name: User first_name
    :type first_name: str|None
    :param last_name: User last_name
    :type last_name: str|None
    :param email: User email
    :type email: str|None
    :param user: The user to retrieve the user for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: A list of users, or None if if there are none.
    :rtype: List[User] | None
    """
    result = []
    users =  db.query(User).all()
    for user in users:
        if first_name != None:
            if  user.first_name == first_name:
                result.append(user)
        if last_name != None:
            if user.last_name == last_name:
                result.append(user)
        if email != None:
            if user.email == email:
                result.append(user)
    return result

async def create_users(body: UserSchema,user: UserAuth, db: Session) -> User:
    """
    Creates a new user for a specific user.

    :param body: The data for the user to create.
    :type body: UserSchema
    :param user: The user to retrieve the user for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: The newly created user.
    :rtype: User
    """
    user_ = User(first_name=body.first_name,last_name=body.last_name,birthday_date = body.birthday_date,email=body.email,phone_numbers=body.phone_numbers,other_description = body.other_description)
    db.add(user_)
    db.commit()
    db.refresh(user_)
    return user_


async def update_user(user_id: int, body: UserSchema,user: UserAuth, db: Session) -> User | None:
    """
    Updates a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to update.
    :type user_id: int
    :param body: The updated data for the user.
    :type body: UserSchema
    :param user: The user to update the user for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: The updated user, or None if it does not exist.
    :rtype: User | None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.first_name = body.first_name
        user.last_name = body.last_name
        user.phone_numbers = body.phone_numbers
        user.email = body.email
        user.other_description = body.other_description
        db.commit()
    return user

async def remove_user(user_id: int,user: UserAuth, db: Session) -> User | None:
    """
    Removes a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to remove.
    :type user_id: int
    :param user: The user to remove the user for.
    :type user: UserAuth
    :param db: The database session.
    :type db: Session
    :return: The removed user, or None if it does not exist.
    :rtype: User | None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user

async def confirmed_email(email: str, db: Session) -> None:
    """
    Sets the user's confirmed attribute to True in the database.

    :param email: User email
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: None
    :rtype: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()
