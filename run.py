from app import create_app

app = create_app()

if __name__ == "__main__":
    # Disable the reloader to avoid losing in-memory session state
    # between /auth/login and /auth/callback during local OAuth flows.
    app.run(debug=True, use_reloader=False)