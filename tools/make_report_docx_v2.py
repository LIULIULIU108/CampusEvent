"""生成实验二 change-v2 项目总结 DOCX（5—8 页）。"""

from __future__ import annotations

import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DIAG = os.path.join(DOCS, "diagrams")
EVID = os.path.join(DOCS, "evidence", "change-v2")
OUT = os.path.join(DOCS, "08_实验报告_v2_24计科2班_刘东梁.docx")

BODY_FONT = "宋体"
HEAD_FONT = "微软雅黑"
INK = RGBColor(0x17, 0x20, 0x33)
MUTED = RGBColor(0x65, 0x70, 0x83)
BRAND = RGBColor(0x14, 0x39, 0xA6)
TEAL = RGBColor(0x0F, 0x76, 0x6E)


def set_font(run, name=BODY_FONT, size=None, bold=None, color=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def para(document, text="", size=10.5, bold=False, color=INK, align=None, space_after=4, line=1.25):
    p = document.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if text:
        run = p.add_run(text)
        set_font(run, BODY_FONT, size, bold, color)
    return p


def heading(document, text, level=1):
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(9 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_font(run, HEAD_FONT, 15 if level == 1 else 12, True, BRAND if level == 1 else INK)
    return p


def bullet(document, text, size=10):
    p = document.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.2
    run = p.add_run(text)
    set_font(run, BODY_FONT, size)
    return p


def shade(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def table(document, headers, rows, widths, size=8.5):
    t = document.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.width = Cm(widths[i])
        shade(cell, "EAF0FF")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(header), HEAD_FONT, size, True, BRAND)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].width = Cm(widths[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            set_font(p.add_run(str(value)), BODY_FONT, size)
    return t


def caption(document, text):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    set_font(p.add_run(text), BODY_FONT, 8.5, False, MUTED)


def image(document, path, width_cm, cap=None):
    if not os.path.exists(path):
        return
    document.add_picture(path, width=Cm(width_cm))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.paragraphs[-1].paragraph_format.keep_with_next = bool(cap)
    if cap:
        caption(document, cap)


def image_row(document, items, width_cm=8.2):
    t = document.add_table(rows=1, cols=len(items))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tr_pr = t.rows[0]._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    for i, (path, cap) in enumerate(items):
        cell = t.rows[0].cells[i]
        cell.width = Cm(width_cm + 0.8)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if os.path.exists(path):
            p.add_run().add_picture(path, width=Cm(width_cm))
        sub = cell.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(sub.add_run(cap), BODY_FONT, 8, False, MUTED)


def page_number(paragraph):
    run = paragraph.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    set_font(run, BODY_FONT, 8, False, MUTED)


def build() -> str:
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.1)
    section.right_margin = Cm(2.1)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(header.add_run("《软件工程》实验二 · CampusEvent · change-v2"), BODY_FONT, 8.5, False, MUTED)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    page_number(footer)

    # 封面
    for _ in range(3):
        para(document, "", 11)
    para(document, "《软件工程》课程实验二", 14, True, MUTED, WD_ALIGN_PARAGRAPH.CENTER, 6)
    para(document, "校园活动报名与管理系统", 25, True, INK, WD_ALIGN_PARAGRAPH.CENTER, 3)
    para(document, "变更版项目总结（change-v2）", 15, False, BRAND, WD_ALIGN_PARAGRAPH.CENTER, 20)
    para(
        document,
        "CR-01 年级限定报名  ·  CR-02 Mock 邮件通知  ·  策略/观察者  ·  v1→v2 迁移",
        10.5, False, MUTED, WD_ALIGN_PARAGRAPH.CENTER, 26,
    )
    info = document.add_table(rows=5, cols=2)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    info.autofit = False
    rows = [
        ("课程名称", "软件工程"),
        ("实验名称", "实验二：基于设计模式的校园活动报名与管理系统"),
        ("班级 / 学号", "24计科2班 / 242806010203"),
        ("姓名", "刘东梁"),
        ("提交日期", "2026 年 11 月 26 日"),
    ]
    for i, (key, value) in enumerate(rows):
        cells = info.rows[i].cells
        cells[0].width = Cm(4.0)
        cells[1].width = Cm(10.2)
        shade(cells[0], "EEF3FF")
        set_font(cells[0].paragraphs[0].add_run(key), HEAD_FONT, 10, True, BRAND)
        set_font(cells[1].paragraphs[0].add_run(value), BODY_FONT, 10)
    para(document, "", 8)
    para(
        document,
        "说明：原 app/、tests/、run.py、cli.py 保持 baseline-v1 原样；change-v2 全部在 app_v2/、tests_v2/、run_v2.py、cli_v2.py。",
        8.5, False, MUTED, WD_ALIGN_PARAGRAPH.CENTER, 4,
    )
    document.add_page_break()

    # 1
    heading(document, "1  实验目标与变更范围", 1)
    para(
        document,
        "本实验在 CampusEvent 初始版本（baseline-v1）上实施教师 CR-01、CR-02：用策略模式新增年级限定报名规则，"
        "用观察者/发件箱增加 Mock 邮件通知，并完成 v1→v2 数据库迁移、C1—C10 回归与公网部署。",
    )
    para(
        document,
        "范围：P2-F01—P2-F08 + CR1-01—CR1-05 + CR2-01—CR2-05。不做候补、真实 SMTP/短信、签到、分页、移动端。",
        size=10,
    )
    para(
        document,
        "代码组织：app/、tests/、run.py、cli.py 与 baseline-v1 完全一致；所有变更集中在 app_v2/ 与 tests_v2/，"
        "便于对比两版，也满足“原代码不动、变更内容用 v2 命名区分”的要求。",
        size=10,
    )

    # 2
    heading(document, "2  需求与变更", 1)
    table(
        document,
        ["变更", "规则", "验收"],
        [
            ("CR-01", "Student.grade（1—4）；新增 GRADE_DIRECT；仅大二/大三可报名；其他年级明确拒绝；名额/开始时间/重复报名规则不变", "CR1-01—05"),
            ("CR-02", "报名通过、审核通过/拒绝时，站内消息 + Mock 邮件；邮件记录收件人/主题/内容/状态；失败留痕不回滚；事件级幂等", "CR2-01—05"),
            ("MIG-01", "v1→v2：student.grade、activity 策略 CHECK、email_outbox；旧数据保留", "迁移测试"),
        ],
        [1.5, 13.2, 2.5],
        8.5,
    )
    para(
        document,
        "原直接报名/审核报名行为不变；待审核提交不发邮件，只有通过/拒绝事件才进入邮件通道。",
        size=9.5,
    )

    # 3
    heading(document, "3  变更设计", 1)
    para(
        document,
        "CR-01 新增 GradeLimitedDirectRegistrationPolicy：先判断学生 grade ∈ {2,3}，再复用 CapacityChecker 检查名额；"
        "PolicyRegistry 注册第三策略。RegistrationService 主流程未改。",
        size=10,
    )
    para(
        document,
        "CR-02 新增 EmailNotificationObserver，与站内观察者并列；supports() 只订阅通过/拒绝事件；"
        "EmailPublisher 增加 on_error()，失败时写 email_outbox=FAILED，不回滚报名；event_id 唯一防重复。",
        size=10,
    )
    image(document, os.path.join(DIAG, "class-v2.png"), 16.0, "图 1  变更版 UML 类图（change-v2）")
    image(document, os.path.join(DIAG, "sequence-email.png"), 13.5, "图 2  报名事件的双通道通知与失败分支")

    # 4
    heading(document, "4  实现与迁移", 1)
    para(
        document,
        "数据库 v2：student 增加 grade；activity.policy_type 支持 GRADE_DIRECT；新增 email_outbox（event_id UNIQUE，"
        "记录 recipient/subject/content/status/error/time）；notification_attempt 继续记录渠道级 SENT/FAILED。",
        size=10,
    )
    para(
        document,
        "v1→v2 迁移在事务内重建 student/activity（SQLite 不能直接改 CHECK），复制数据、修正 sqlite_sequence、"
        "关闭/恢复外键；迁移测试验证学生、活动、报名、消息保留与外键完整。",
        size=10,
    )
    image_row(
        document,
        [
            (os.path.join(EVID, "png", "CR1-03-大一拒绝.png"), "图 3  大一报名被明确拒绝"),
            (os.path.join(EVID, "png", "CR2-02-邮件记录.png"), "图 4  站内 + Mock 邮件记录"),
        ],
        8.1,
    )

    # 5
    heading(document, "5  测试与回归", 1)
    para(
        document,
        "change-v2 全量 pytest：123 passed；原 baseline tests 107 passed 仍可单独运行。"
        "C1—C10 在 change-v2 真实 HTTP 回归 10/10；CR 验收 11/11。",
        size=10,
    )
    table(
        document,
        ["用例", "场景", "结果"],
        [
            ("C1—C10", "直接/审核/满额/取消/重启持久化（回归）", "10/10"),
            ("CR1-01/02", "大二、大三报名年级限定", "通过"),
            ("CR1-03/04", "大一、大四报名", "拒绝并提示"),
            ("CR1-05", "C1—C10 回归", "通过"),
            ("CR2-01", "直接报名：站内 + 邮件", "通过"),
            ("CR2-02", "审核通过/拒绝：站内 + 邮件", "通过"),
            ("CR2-03", "模拟邮件失败：报名保留，错误留痕", "通过"),
            ("CR2-04", "重复事件：不重复通知", "通过"),
            ("CR2-05", "C1—C10 回归", "通过"),
            ("MIG-01", "v1→v2 数据/外键/序列", "通过"),
        ],
        [2.4, 12.2, 2.2],
        8.5,
    )
    para(
        document,
        "主要缺陷与修复：SQLite CHECK 迁移（重建表）、邮件失败记录被回滚（on_error）、待审核误发邮件（supports）、"
        "旧 gunicorn 未重启导致读取 v2 活动失败（部署脚本改为显式停止 gunicorn）。",
        size=9.2,
    )

    # 6
    heading(document, "6  部署", 1)
    para(
        document,
        "公网：https://campusevent-app.thevibehosting.com 。平台 The Vibe Hosting；gunicorn 单 worker、2 线程；"
        "SQLite 位于 /root/myapp/instance/campus_event.db；启动时自动迁移 v1→v2，并执行 set-demo-grades/seed-cr-demo。",
        size=10,
    )
    image_row(
        document,
        [
            (os.path.join(EVID, "public", "png", "public-home.png"), "图 5  公网登录页（change-v2）"),
            (os.path.join(EVID, "public", "png", "线上-管理页-v2.png"), "图 6  公网管理页（5 个活动）"),
        ],
        8.1,
    )

    # 7
    heading(document, "7  影响分析与可维护性", 1)
    table(
        document,
        ["指标", "baseline-v1", "change-v2", "说明"],
        [
            ("自动化测试", "107", "123", "新增 16 条 CR/迁移测试"),
            ("新增类/异常", "—", "7", "年级策略、邮件观察者、MockSender、Outbox 模型/仓储、邮件服务、异常"),
            ("修改的核心业务类", "—", "0", "RegistrationService / ApprovalService 未改"),
            ("修改的通知基础设施", "—", "1", "EventPublisher 增加 supports/on_error"),
            ("C1—C10 回归失败", "—", "0", "10/10 通过"),
            ("AI 关键交互", "—", "约 6 轮", "见 AI_DEV_LOG"),
            ("集中修改时长", "—", "约 2 小时", "含实现、迁移、测试、文档、部署"),
        ],
        [3.6, 3.4, 3.4, 6.2],
        8.5,
    )
    para(
        document,
        "结论：CR-01 只新增策略、CR-02 只新增观察者/发件箱，核心报名/审批服务零修改；"
        "代价是通知子系统增加两个钩子、迁移需要重建两张表。收益是两类变化可独立测试、独立失败、可观测。",
        size=9.5,
    )

    # 8
    heading(document, "8  问题与反思", 1)
    bullet(document, "设计决策要回到业务语义：待审核不占名额，所以邮件只订阅通过/拒绝事件；否则会给待审核学生发无效通知。")
    bullet(document, "失败语义比成功路径更难：邮件失败不能回滚报名，也不能丢失错误；最终用 on_error + 发件箱 FAILED 解决。")
    bullet(document, "原代码不动的代价是 v2 目录重复；但换来 baseline/change 两版可并列比较，符合课程“可追踪两版”的要求。")
    bullet(document, "部署脚本必须显式停止旧 gunicorn：SQLite 已迁移 v2，旧 baseline 进程读取 GRADE_DIRECT 会 500；本次已修正并复测。")

    heading(document, "附录  运行与证据", 1)
    para(
        document,
        "v2 启动：python cli_v2.py seed-demo → python run_v2.py；测试：python -m pytest -c pytest_v2.ini。"
        "证据：docs/evidence/change-v2/cr-log.json、regression/acceptance-log.json、png/；"
        "Git：baseline-v1 与 change-v2 两个标签。",
        size=9.2,
    )

    os.makedirs(DOCS, exist_ok=True)
    document.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
