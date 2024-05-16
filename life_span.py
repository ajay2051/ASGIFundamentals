from fastapi import FastAPI

app = FastAPI()


async def startup_event():
    print("Starting Up")


async def shutdown_event():
    print("Shutting Down")
