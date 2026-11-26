"""CampusEvent change-v2 本地启动入口（原 run.py 保持 baseline-v1 不变）。"""

from __future__ import annotations

import os

from app_v2 import create_app_v2

app = create_app_v2()


if __name__ == "__main__":
    host = os.environ.get("CAMPUSEVENT_HOST", "127.0.0.1")
    port = int(os.environ.get("CAMPUSEVENT_PORT", "5000"))
    debug = os.environ.get("CAMPUSEVENT_DEBUG", "0") == "1"
    print(f"CampusEvent v2 已启动：http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)
