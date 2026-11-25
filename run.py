"""本地启动入口。"""

from __future__ import annotations

import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    host = os.environ.get("CAMPUSEVENT_HOST", "127.0.0.1")
    port = int(os.environ.get("CAMPUSEVENT_PORT", "5000"))
    debug = os.environ.get("CAMPUSEVENT_DEBUG", "0") == "1"
    print(f"CampusEvent 已启动：http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)
