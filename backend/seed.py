"""CLI entrypoint. From backend/: `python seed.py`."""

from app.database.seed import main

if __name__ == "__main__":
    main()
