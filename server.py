from typing import Any
from collections.abc import MutableMapping, Awaitable, Callable, Mapping

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

total_connections = 0


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    global total_connections
    total_connections += 1
    current_connection = total_connections
    print(f"Beginning Connection: {current_connection}. Scope: {scope}")
    print(f"Ending Connection {current_connection}")


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
