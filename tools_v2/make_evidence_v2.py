"""把真实响应 HTML 内联 CSS，生成可离线查看的截图页面。"""

from __future__ import annotations

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.environ.get(
    "CAMPUSEVENT_EVIDENCE_DIR", os.path.join(ROOT, "docs", "evidence")
)
SRC = os.path.join(EVIDENCE, "html")
DST = os.path.join(EVIDENCE, "screens")
CSS_PATH = os.path.join(ROOT, "app", "static", "style.css")


def main() -> int:
    with open(CSS_PATH, encoding="utf-8") as fh:
        css = fh.read()
    os.makedirs(DST, exist_ok=True)
    count = 0
    for path in sorted(glob.glob(os.path.join(SRC, "*.html"))):
        with open(path, encoding="utf-8") as fh:
            document = fh.read()
        document = re.sub(
            r'<link rel="stylesheet" href="/static/style\.css">',
            f"<style>\n{css}\n</style>",
            document,
        )
        document = re.sub(
            r'<script src="/static/app\.js" defer></script>', "", document
        )
        target = os.path.join(DST, os.path.basename(path))
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(document)
        count += 1
        print("prepared", os.path.basename(target))
    print(f"共 {count} 个页面")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
