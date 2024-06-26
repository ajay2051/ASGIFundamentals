import re
from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

total_connections = 0


async def handle_lifespan(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope["type"] == "lifespan"
    while True:
        message = await receive()
        print(f"Received {message}""")
        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup"})
        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown"})
            break


async def echo_endpoint(scope: Scope, receive: Receive, send: Send):
    data = []
    while True:
        print("Waiting for message...")
        message = await receive()
        print(f"Received message:", message)

        if message["type"] == "http.disconnect":
            return

        assert message["type"] == "http.request"

        data.append(message["body"])

        if not message["more_body"]:
            break

    response_message = {
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"text/plain")],
    }
    print("Sending response start:", response_message)
    await send(response_message)

    response_message = {
        "type": "http.response.body",
        "body": b"echo: " + b"".join(data),
        "more_body": False,
    }
    print("Sending response body:", response_message)
    await send(response_message)


async def status_endpoint(scope: Scope, receive: Receive, send: Send):
    response_message = {
        "type": "http.response.start",
        "status": 204,  # http no content
    }
    print("Sending response start:", response_message)
    await send(response_message)

    response_message = {
        "type": "http.response.body",
        "body": b"",
        "more_body": False,
    }
    print("Sending response body:", response_message)
    await send(response_message)


async def error_endpoint(scope: Scope, receive: Receive, send: Send) -> None:
    response_message = {
        "type": "http.response.start",
        "status": 400,
    }
    print("Sending response start:", response_message)
    await send(response_message)
    response_message = {
        "type": "http.response.body",
        "body": b"",
        "more_body": False,
    }
    print("Sending response body:", response_message)
    await send(response_message)


async def handle_http(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope["type"] == "http"
    while True:
        print("Waiting for message....")
        message = await receive()
        print("Received {!r}".format(message))
        if message["type"] == "http.disconnect":
            return
        if not message["more_body"]:
            break
    response_message = {
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"text/plain")],
    }
    print("Sending response start:", response_message)
    await send(response_message)
    response_message = {
        "type": "http.response.body",
        "body": b"Hello, world!",
        "more_body": False,
    }
    print("Sending response body:", response_message)
    await send(response_message)


async def handle_https(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope["type"] == "https"
    if scope["path"] == "/echo" and scope["method"] == "POST":
        await echo_endpoint(scope, receive, send)
    elif scope["path"] == "/status" and scope["method"] == "GET":
        await status_endpoint(scope, receive, send)
    else:
        await error_endpoint(scope, receive, send)


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    global total_connections
    total_connections += 1
    current_connection = total_connections
    print(f"Beginning Connection: {current_connection}. Scope: {scope}")
    if scope["type"] == "lifespan":
        await handle_lifespan(scope, receive, send)
    elif scope["type"] == "http":
        await handle_http(scope, receive, send)
    print(f"Ending Connection {current_connection}")


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
