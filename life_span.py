import enum
import traceback
from asyncio.log import logger
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI
from starlette.types import ASGIApp, Scope, Receive, Send


@asynccontextmanager
async def lifespan(the_app):
    logger.info("Starting up...")
    the_app.db = await init_db()
    the_app.s3_client = await init_boto_s3()
    the_app.redis_client = await init_redis()
    the_app.settings.dynamic = await read_dynamic_settings(the_app.db)
    the_app.sanity_check_settings()
    the_app.spawn_metrics_worker()
    yield
    logger.info("Shutting down...")
    await the_app.save_metrics(the_app.db)
    await email_devops()
    print("Shutting Down Things")


app = FastAPI(lifespan=lifespan)


class App:
    def __init__(self, *, lifespan):
        self.lifespan = lifespan

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        print(scope)
        if scope["type"] != "lifespan":
            await self.handle_lifespan(scope, receive, send)

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send):
        assert scope["type"] == "lifespan"

        message = await receive()
        assert message["type"] == "lifespan.startup"
        try:
            async with self.lifespan:
                await send({"type": "lifespan.startup.complete"})
                started = True
                message = await receive()
                assert message["type"] == "lifespan.shutdown"
        except Exception as e:
            event_type = "lifespan.shutdown.failed" if started else "lifespan.startup.failed"
            await send({"type": event_type, "message": traceback.format_exc()})
        await send({"type": "lifespan.shutdown.complete"})
        started = False


@dataclass
class Lifespan:
    app: ASGIApp

    async def __aenter__(self):
        print("Startup Things")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        print("Shutting Down Things")
        return None


class AsgiEventType(enum.StrEnum):
    LIFESPAN_STARTUP = "lifespan.startup"
    LIFESPAN_STARTUP_COMPLETE = "lifespan.startup.complete"
    LIFESPAN_STARTUP_FAILED = "lifespan.startup.failed"

    LIFESPAN_SHUTDOWN = "lifespan.shutdown"
    LIFESPAN_SHUTDOWN_COMPLETE = "lifespan.shutdown.complete"
    LIFESPAN_SHUTDOWN_FAILED = "lifespan.shutdown.failed"


async def startup_event():  # DEPRECATED
    print("Starting Up")


async def shutdown_event():  # DEPRECATED
    print("Shutting Down")


# app = App()


def main():
    import uvicorn

    uvicorn.run(app, port=5000, log_level="info", timeout_graceful_shutdown=3)


if __name__ == "__main__":
    main()
