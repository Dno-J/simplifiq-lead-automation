import uvicorn


def main() -> None:
    """
    Local development entry point.

    This allows the app to be started with:
        python run.py

    For production, use a proper ASGI server command such as:
        uvicorn app.main:app --host 0.0.0.0 --port $PORT
    """

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()