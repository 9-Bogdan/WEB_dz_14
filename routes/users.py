from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query,UploadFile, File
from sqlalchemy.orm import Session
from datetime import date,timedelta,datetime
from database.connect_db import get_db
from schemas import UserSchema, UserResponse, UserDb
from repository import users as repository_users
from database.models import User,UserAuth
from services.auth import auth_service
from fastapi_limiter.depends import RateLimiter
import cloudinary
import cloudinary.uploader
from conf.config import settings
router = APIRouter(prefix='/users', tags=["users"])


@router.get("/", response_model=List[UserResponse],description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_users(skip: int = 0, limit: int = 100,db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user)):
    """
    Retrieve a list of users with rate limiting.

    :param skip: Number of records to skip.
    :type skip: int
    :param limit: Maximum number of records to retrieve.
    :type limit: int
    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :return: List of users.
    :rtype: List[UserResponse]
    """
    users = await repository_users.get_users(skip, limit,current_user, db)
    return users

@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve the current user's profile.

    :param current_user: Current user information.
    :type current_user: User
    :return: Current user's profile.
    :rtype: UserDb
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
    Update the user's avatar.

    :param file: The image file for the new avatar.
    :type file: UploadFile
    :param current_user: Current user information.
    :type current_user: User
    :param db: Database session.
    :type db: Session
    :return: Updated user profile.
    :rtype: UserDb
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user


@router.get("/birthdays", response_model=List[UserResponse],description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_birthdays(db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user)):
    """
    Retrieve upcoming birthdays of users.

    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :return: List of users with upcoming birthdays.
    :rtype: List[UserResponse]
    """
    today = date.today()
    end_date = today + timedelta(days=7)
    birthdays = await repository_users.get_birthday(today,end_date,current_user,db)
    if birthdays is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return birthdays

@router.get("/search", response_model=List[UserResponse],description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def search(db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user), first_name: str=Query(None),last_name: str=Query(None),email:str=Query(None)):
    """
    Search for users based on criteria.

    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :param first_name: First name for filtering.
    :type first_name: str
    :param last_name: Last name for filtering.
    :type last_name: str
    :param email: Email for filtering.
    :type email: str
    :return: List of users matching the search criteria.
    :rtype: List[UserResponse]
    """
    users = await repository_users.search_users(first_name,last_name,email,current_user,db)
    if users is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return users
                 

@router.get("/{user_id}", response_model=UserResponse,description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_user(user_id: int, db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user)):
    """
    Retrieve a user's profile by ID.

    :param user_id: ID of the user to retrieve.
    :type user_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :return: User profile.
    :rtype: UserResponse
    """
    users = await repository_users.get_user(user_id,current_user, db)
    if users is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return users



@router.post("/", response_model=UserResponse,status_code=status.HTTP_201_CREATED,description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_users(body: UserSchema, db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user)):
    """
    Create a new user.

    :param body: User data for creation.
    :type body: UserSchema
    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :return: Created user's profile.
    :rtype: UserResponse
    """
    return await repository_users.create_users(body,current_user, db)


@router.put("/{user_id}", response_model=UserResponse,description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_user(body: UserSchema, user_id: int, db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user)):
    """
    Update a user's profile by ID.

    :param body: User data for updating.
    :type body: UserSchema
    :param user_id: ID of the user to update.
    :type user_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :return: Updated user's profile.
    :rtype: UserResponse
    """
    user = await repository_users.update_user(user_id, body,current_user, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", response_model=UserResponse,description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def remove_user(user_id: int, db: Session = Depends(get_db),current_user: UserAuth = Depends(auth_service.get_current_user)):
    """
    Remove a user's profile by ID.

    :param user_id: ID of the user to remove.
    :type user_id: int
    :param db: Database session.
    :type db: Session
    :param current_user: Current user information.
    :type current_user: UserAuth
    :return: Removed user's profile.
    :rtype: UserResponse
    """
    user = await repository_users.remove_user(user_id,current_user, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user