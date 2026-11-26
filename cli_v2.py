"""CampusEvent change-v2 CLI（原 cli.py 保持 baseline-v1 不变）。"""

from __future__ import annotations

import sys

from app_v2 import create_app_v2, db
from app_v2.seed import (
    seed_cr_demo_activity,
    seed_demo,
    seed_students_only,
    set_demo_grades,
)


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    app = create_app_v2()
    with app.app_context():
        if command == "init-db":
            db.init_db()
            print("v2 数据库已初始化/迁移。")
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
        elif command == "set-demo-grades":
            db.init_db()
            result = set_demo_grades()
            print(
                f"演示年级已同步：更新 {result['updated']} 人，"
                f"新增 {result['inserted']} 人。"
            )
        elif command == "seed-cr-demo":
            db.init_db()
            result = seed_cr_demo_activity()
            print(
                "已创建年级限定演示活动。"
                if result["created"]
                else "年级限定演示活动已存在，跳过。"
            )
        elif command == "show-state":
            conn = db.get_db()
            for table in (
                "student",
                "activity",
                "registration",
                "message",
                "email_outbox",
            ):
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"{table}: {count}")
        else:
            print(
                "用法：python cli_v2.py "
                "[init-db|seed-students|seed-demo|set-demo-grades|seed-cr-demo|show-state]"
            )
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
