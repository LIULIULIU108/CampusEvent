"""对运行中的 CampusEvent 执行 C1—C9 验收，并保存真实 HTML 证据。

前置：
  1. 服务已启动在 CAMPUSEVENT_BASE_URL（默认 http://127.0.0.1:5000）。
  2. 数据库为空或仅含演示学生（可用 python cli.py seed-students）。

用法：
  python tools/acceptance_run.py            # 执行 C1—C9
  python tools/acceptance_run.py --verify   # 服务重启后执行 C10

证据写入 docs/evidence/，不伪造；失败会保留现场并返回非零。
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BASE = os.environ.get("CAMPUSEVENT_BASE_URL", "http://127.0.0.1:5000")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(ROOT, "docs", "evidence")
HTML_DIR = os.path.join(EVIDENCE, "html")
LOG_PATH = os.path.join(EVIDENCE, "acceptance-log.json")
STATE_PATH = os.path.join(EVIDENCE, "state.json")
TZ = ZoneInfo("Asia/Shanghai")
RECORDS: list[dict] = []


class Session:
    def __init__(self) -> None:
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar)
        )

    def get(self, path: str) -> tuple[int, str]:
        return self._request(path, None)

    def post(self, path: str, data: dict[str, str]) -> tuple[int, str]:
        body = urllib.parse.urlencode(data).encode("utf-8")
        return self._request(path, body)

    def _request(self, path: str, body: bytes | None) -> tuple[int, str]:
        url = BASE + path
        req = urllib.request.Request(
            url,
            data=body,
            method="POST" if body is not None else "GET",
            headers={"User-Agent": "CampusEvent-Acceptance/1.0"},
        )
        try:
            with self.opener.open(req, timeout=20) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", "replace")


def snapshot(name: str, text: str) -> str:
    os.makedirs(HTML_DIR, exist_ok=True)
    path = os.path.join(HTML_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return f"docs/evidence/html/{name}.html"


def record(cid: str, action: str, expected: str, actual: str, passed: bool, evidence: list[str]) -> None:
    RECORDS.append(
        {
            "id": cid,
            "action": action,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "evidence": evidence,
        }
    )
    print(f"[{'PASS' if passed else 'FAIL'}] {cid} {action} -> {actual}")


def login(session: Session, account: str, password: str) -> str:
    status, text = session.post(
        "/login", {"account_id": account, "password": password}
    )
    if status != 200 or "退出" not in text:
        raise RuntimeError(f"登录失败 account={account} status={status}")
    return text


def make_activity(
    admin: Session,
    title: str,
    *,
    policy: str,
    capacity: int,
    days: int,
) -> tuple[int, str]:
    start = (datetime.now(TZ) + timedelta(days=days)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    _, dashboard = admin.post(
        "/admin/activities/new",
        {
            "title": title,
            "category": "验收测试",
            "start_at": start.strftime("%Y-%m-%dT%H:%M"),
            "location": "验收楼 A101",
            "capacity": str(capacity),
            "policy_type": policy,
        },
    )
    # 从表格的 title-cell 开始匹配，避免命中顶部 flash 中的活动名称。
    match = re.search(
        r'<td class="title-cell">\s*'
        + re.escape(title)
        + r"[\s\S]{0,3000}?/admin/activities/(\d+)/registrations",
        dashboard,
    )
    if not match:
        raise RuntimeError(f"无法在管理页定位活动：{title}")
    return int(match.group(1)), dashboard


def find_registration_id(student: Session, activity_id: int, title: str) -> int:
    _, page = student.get("/me/registrations")
    match = re.search(
        re.escape(title) + r"[\s\S]{0,3000}?/registrations/(\d+)/cancel",
        page,
    )
    if not match:
        raise RuntimeError(f"无法定位报名记录：{title}")
    return int(match.group(1))


def find_pending_registration(admin: Session, activity_id: int) -> int:
    _, page = admin.get(f"/admin/activities/{activity_id}/registrations")
    match = re.search(r"/admin/registrations/(\d+)/approve", page)
    if not match:
        raise RuntimeError(f"活动 {activity_id} 没有待审核报名")
    return int(match.group(1))


def remaining_slots(detail: str) -> int | None:
    match = re.search(
        r'num accent">(\d+)</div>\s*<div class="label">剩余名额', detail
    )
    return int(match.group(1)) if match else None


def run_initial() -> int:
    admin = Session()
    login(admin, "admin", "admin123")
    a = Session()
    login(a, "2024001", "123456")
    b = Session()
    login(b, "2024002", "123456")
    c = Session()
    login(c, "2024003", "123456")

    # C1
    c1_title = "C1 直接报名验收活动"
    c1_id, dashboard = make_activity(
        admin, c1_title, policy="DIRECT", capacity=2, days=3
    )
    c1_pass = c1_title in dashboard and c1_id > 0
    record(
        "C1",
        "管理员创建直接报名活动，容量 2",
        "创建成功，可供学生报名",
        f"活动 ID={c1_id}，管理页可见",
        c1_pass,
        [snapshot("C1-创建活动", dashboard)],
    )

    # C2
    _, detail = a.post(f"/activities/{c1_id}/registrations", {})
    c2_pass = "已通过" in detail and "取消报名" in detail
    _, messages = a.get("/me/messages")
    c2_pass = c2_pass and "报名成功" in messages
    record(
        "C2",
        "学生 A 报名直接报名活动",
        "变为已通过并产生站内通知",
        "详情显示已通过，消息含报名成功",
        c2_pass,
        [
            snapshot("C2-报名后详情", detail),
            snapshot("C2-报名成功消息", messages),
        ],
    )

    # C3
    _, duplicate = a.post(f"/activities/{c1_id}/registrations", {})
    c3_pass = "请勿重复提交" in duplicate
    record(
        "C3",
        "学生 A 再次提交相同活动报名",
        "拒绝重复有效报名",
        "页面提示请勿重复提交",
        c3_pass,
        [snapshot("C3-重复报名提示", duplicate)],
    )

    # C4
    c4_title = "C4 满额验收活动"
    c4_id, _ = make_activity(admin, c4_title, policy="DIRECT", capacity=2, days=4)
    a.post(f"/activities/{c4_id}/registrations", {})
    _, b_detail = b.post(f"/activities/{c4_id}/registrations", {})
    _, c_detail = c.post(f"/activities/{c4_id}/registrations", {})
    c4_pass = (
        "已通过" in b_detail
        and "名额已满" in c_detail
        and "立即报名" not in c_detail
    )
    record(
        "C4",
        "学生 B 填满名额后学生 C 再报名",
        "B 通过，C 因名额不足失败",
        "B 详情显示已通过，C 页面提示名额已满",
        c4_pass,
        [
            snapshot("C4-B已通过", b_detail),
            snapshot("C4-C名额已满", c_detail),
        ],
    )

    # C5
    c5_title = "C5 审核报名验收活动"
    c5_id, _ = make_activity(admin, c5_title, policy="APPROVAL", capacity=2, days=5)
    _, c5_detail = a.post(f"/activities/{c5_id}/registrations", {})
    c5_pass = "我的报名" in c5_detail and "badge-pending" in c5_detail
    record(
        "C5",
        "学生 A 申请审核型活动",
        "状态为待审核",
        "详情显示待审核",
        c5_pass,
        [snapshot("C5-待审核详情", c5_detail)],
    )

    # C6
    c6_title = "C6 审核批准验收活动"
    c6_id, _ = make_activity(admin, c6_title, policy="APPROVAL", capacity=2, days=6)
    a.post(f"/activities/{c6_id}/registrations", {})
    c6_rid = find_pending_registration(admin, c6_id)
    _, admin_page = admin.post(
        f"/admin/registrations/{c6_rid}/approve", {"activity_id": str(c6_id)}
    )
    _, a_messages = a.get("/me/messages")
    _, c6_detail = a.get(f"/activities/{c6_id}")
    c6_pass = (
        "审核通过" in a_messages
        and "我的报名" in c6_detail
        and "badge-approved" in c6_detail
    )
    record(
        "C6",
        "管理员批准 A 的待审核报名",
        "变为已通过且生成通知",
        "审批页显示批准成功，学生消息含审核通过",
        c6_pass,
        [
            snapshot("C6-审批后页面", admin_page),
            snapshot("C6-审核通过消息", a_messages),
        ],
    )

    # C7
    c7_title = "C7 审核拒绝验收活动"
    c7_id, _ = make_activity(admin, c7_title, policy="APPROVAL", capacity=2, days=7)
    b.post(f"/activities/{c7_id}/registrations", {})
    c7_rid = find_pending_registration(admin, c7_id)
    _, reject_page = admin.post(
        f"/admin/registrations/{c7_rid}/reject", {"activity_id": str(c7_id)}
    )
    _, b_messages = b.get("/me/messages")
    c7_pass = "审核未通过" in b_messages
    record(
        "C7",
        "管理员拒绝另一待审核报名",
        "变为已拒绝且生成通知",
        "学生消息含审核未通过",
        c7_pass,
        [
            snapshot("C7-拒绝后页面", reject_page),
            snapshot("C7-拒绝消息", b_messages),
        ],
    )

    # C8
    c8_title = "C8 满额批准验收活动"
    c8_id, _ = make_activity(admin, c8_title, policy="APPROVAL", capacity=1, days=8)
    a.post(f"/activities/{c8_id}/registrations", {})
    c8_a_rid = find_pending_registration(admin, c8_id)
    admin.post(
        f"/admin/registrations/{c8_a_rid}/approve", {"activity_id": str(c8_id)}
    )
    b.post(f"/activities/{c8_id}/registrations", {})
    c8_b_rid = find_pending_registration(admin, c8_id)
    _, c8_page = admin.post(
        f"/admin/registrations/{c8_b_rid}/approve", {"activity_id": str(c8_id)}
    )
    _, c8_detail = b.get(f"/activities/{c8_id}")
    c8_pass = (
        "名额已满" in c8_page
        and "我的报名" in c8_detail
        and "badge-pending" in c8_detail
    )
    record(
        "C8",
        "名额已满时批准 B 的报名",
        "批准失败，不超出人数上限",
        "审批页提示名额已满，B 仍为待审核",
        c8_pass,
        [
            snapshot("C8-批准失败提示", c8_page),
            snapshot("C8-B仍待审核", c8_detail),
        ],
    )

    # C9
    c9_title = "C9 取消报名验收活动"
    c9_id, _ = make_activity(admin, c9_title, policy="DIRECT", capacity=2, days=9)
    _, c9_before = a.post(f"/activities/{c9_id}/registrations", {})
    before = remaining_slots(c9_before)
    c9_rid = find_registration_id(a, c9_id, c9_title)
    _, c9_after = a.post(
        f"/registrations/{c9_rid}/cancel", {"next": "/me/registrations"}
    )
    _, c9_detail = a.get(f"/activities/{c9_id}")
    after = remaining_slots(c9_detail)
    _, c9_regs = a.get("/me/registrations")
    c9_pass = before == 1 and after == 2 and "已取消" in c9_regs
    record(
        "C9",
        "学生取消已通过报名",
        "状态变为已取消，统计同步变化",
        f"取消前剩余 {before}，取消后剩余 {after}，我的报名显示已取消",
        c9_pass,
        [
            snapshot("C9-取消前详情", c9_before),
            snapshot("C9-取消后详情", c9_detail),
            snapshot("C9-我的报名", c9_regs),
        ],
    )

    # C10 前置：创建一条待重启后核对的数据
    c10_title = "C10 重启持久化验收活动"
    c10_id, _ = make_activity(admin, c10_title, policy="DIRECT", capacity=2, days=10)
    _, c10_detail = a.post(f"/activities/{c10_id}/registrations", {})
    c10_rid = find_registration_id(a, c10_id, c10_title)
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "activity_id": c10_id,
                "registration_id": c10_rid,
                "title": c10_title,
                "student_id": "2024001",
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )
    snapshot("C10-重启前详情", c10_detail)

    write_log()
    passed_count = sum(1 for item in RECORDS if item["passed"])
    print(f"\nC1—C9 合计 {len(RECORDS)} 项，通过 {passed_count} 项。")
    print("现在停止并重新启动服务，然后执行：python tools/acceptance_run.py --verify")
    return 0 if passed_count == len(RECORDS) else 1


def verify_restart() -> int:
    if not os.path.exists(STATE_PATH):
        print("缺少 state.json，请先执行 C1—C9。")
        return 2
    with open(STATE_PATH, encoding="utf-8") as fh:
        state = json.load(fh)

    student = Session()
    login(student, "2024001", "123456")
    _, detail = student.get(f"/activities/{state['activity_id']}")
    _, messages = student.get("/me/messages")
    _, registrations = student.get("/me/registrations")
    passed = (
        "badge-approved" in detail
        and state["title"] in messages
        and state["title"] in registrations
    )
    record(
        "C10",
        "重启服务后查询活动、报名、消息",
        "数据仍一致",
        "活动详情仍为已通过，消息与我的报名仍存在",
        passed,
        [
            snapshot("C10-重启后详情", detail),
            snapshot("C10-重启后消息", messages),
        ],
    )

    existing: list[dict] = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as fh:
            existing = json.load(fh).get("records", [])
    existing = [item for item in existing if item.get("id") != "C10"] + RECORDS
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "run_at": datetime.now(TZ).isoformat(timespec="seconds"),
                "base_url": BASE,
                "total": len(existing),
                "passed": sum(1 for item in existing if item["passed"]),
                "records": existing,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )
    print(f"C10 {'通过' if passed else '失败'}。")
    return 0 if passed else 1


def write_log() -> None:
    passed_count = sum(1 for item in RECORDS if item["passed"])
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "run_at": datetime.now(TZ).isoformat(timespec="seconds"),
                "base_url": BASE,
                "total": len(RECORDS),
                "passed": passed_count,
                "records": RECORDS,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    try:
        if "--verify" in sys.argv:
            raise SystemExit(verify_restart())
        raise SystemExit(run_initial())
    except Exception as exc:  # noqa: BLE001
        print(f"验收执行失败：{exc}", file=sys.stderr)
        write_log()
        raise SystemExit(1)
