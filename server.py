from typing import Any
from collections.abc import MutableMapping, Awaitable, Callable, Mapping

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
