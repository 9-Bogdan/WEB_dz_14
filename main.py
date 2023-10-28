from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from routes import users,auth
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio
app = FastAPI()
origins = [ 
    "http://localhost:3000"
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.on_event("startup")
async def startup():
    """
    Initialize necessary components and services during application startup.

    This function is called when the FastAPI application starts up.
    It performs the following tasks:
    1. Establishes a connection to a Redis server.
    2. Initializes the FastAPILimiter using the Redis connection for rate limiting.

    :return: None
    """
    r = await redis.asyncio.Redis(host='localhost', port=6379, db=0, encoding="utf-8",
                          decode_responses=True)
    await FastAPILimiter.init(r)

@app.get("/")
def read_root():
    """
    Handle the root endpoint and return a simple message.
    This function handles incoming GET requests to the root endpoint ("/").

    :return: A JSON response containing a greeting message.
    :rtype: dict
    """
    return {"message": "Hello World"}