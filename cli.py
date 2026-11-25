"""项目 CLI：init-db / seed-demo / show-state。"""

from __future__ import annotations

import sys

from app import db, create_app
from app.seed import seed_demo, seed_students_only


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    app = create_app()
    with app.app_context():
        if command == "init-db":
            db.init_db()
            print("数据库已初始化。")
        elif command == "seed-students":
            db.init_db()
            result = seed_students_only()
            if result.get("skipped"):
                print("数据库已有学生，跳过。")
            else:
                print(f"已写入 {result['students']} 名学生。")
        elif command == "seed-demo":
            db.init_db()
            result = seed_demo()
            if result.get("skipped"):
                print("数据库已有数据，跳过演示数据写入。")
            else:
                print(
                    f"已写入 {result['students']} 名学生、"
                    f"{result['activities']} 个活动。"
                )
        elif command == "show-state":
            conn = db.get_db()
            for table in ("student", "activity", "registration", "message"):
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"{table}: {count}")
        else:
            print("用法：python cli.py [init-db|seed-students|seed-demo|show-state]")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
