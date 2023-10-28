from typing import Optional
import pickle
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database.connect_db import get_db
from repository import users as repository_users
import redis
from conf.config import settings

class Auth:
    """
    Authentication utility class.

    :cvar pwd_context: Password context for hashing and verifying passwords.
    :cvar SECRET_KEY: Secret key used for encoding and decoding tokens.
    :cvar ALGORITHM: Algorithm used for token encoding.
    :cvar oauth2_scheme: OAuth2 password bearer scheme.
    :cvar r: Redis client for caching user data.
    :rtype: None
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        Verify a plain password against a hashed password.

        :param plain_password: The plain text password to verify.
        :type plain_password: str
        :param hashed_password: The hashed password to compare with.
        :type hashed_password: str
        :return: True if the passwords match, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hash a password.

        :param password: The password to hash.
        :type password: str
        :return: The hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(password)
    
    def create_email_token(self, data: dict):
        """
        Create an email verification token.

        :param data: The data to encode into the token.
        :type data: dict
        :return: The email verification token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    
    async def get_email_from_token(self, token: str):
        """
        Extract the email from an email verification token.

        :param token: The email verification token.
        :type token: str
        :return: The email address.
        :rtype: str
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail="Invalid token for email verification")

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Create an access token.

        :param data: The data to encode into the token.
        :type data: dict
        :param expires_delta: Optional time delta for token expiration.
        :type expires_delta: Optional[float]
        :return: The access token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token


    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Create a refresh token.

        :param data: The data to encode into the token.
        :type data: dict
        :param expires_delta: Optional time delta for token expiration.
        :type expires_delta: Optional[float]
        :return: The refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decode a refresh token and extract the email.

        :param refresh_token: The refresh token to decode.
        :type refresh_token: str
        :return: The email address.
        :rtype: str
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Get the current user based on an access token.

        :param token: The access token.
        :type token: str
        :param db: The database session.
        :type db: Session
        :return: The current user.
        :rtype: User
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception
        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user


auth_service = Auth()