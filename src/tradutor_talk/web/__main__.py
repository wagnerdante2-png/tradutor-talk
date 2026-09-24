from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tradutor Talk web laboratory for GitHub Codespaces"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run(
        "tradutor_talk.web.app:app",
        host=args.host,
        port=args.port,
        reload=False,
        access_log=True,
    )


if __name__ == "__main__":
    main()
