"""生成实验二 baseline-v1 项目总结 DOCX（5—8 页）。"""

from __future__ import annotations

import os
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DIAG = os.path.join(DOCS, "diagrams")
EVID = os.path.join(DOCS, "evidence", "png")
OUT = os.path.join(DOCS, "08_实验报告_24计科2班_刘东梁.docx")

BODY_FONT = "宋体"
HEAD_FONT = "微软雅黑"
INK = RGBColor(0x17, 0x20, 0x33)
MUTED = RGBColor(0x65, 0x70, 0x83)
BRAND = RGBColor(0x14, 0x39, 0xA6)


def set_run_font(run, name: str = BODY_FONT, size: float | None = None, bold=None, color=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def para(document, text="", size=10.5, bold=False, color=INK, align=None, space_after=4, line=1.3):
    p = document.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if text:
        run = p.add_run(text)
        set_run_font(run, BODY_FONT, size, bold, color)
    return p


def heading(document, text, level=1):
    size = 15 if level == 1 else 12.5
    color = BRAND if level == 1 else INK
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, HEAD_FONT, size, True, color)
    return p


def bullet(document, text, size=10.5):
    p = document.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.25
    run = p.add_run(text)
    set_run_font(run, BODY_FONT, size)
    return p


def shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def add_table(document, headers, rows, widths, font_size=8.5):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.width = Cm(widths[index])
        shade(cell, "EAF0FF")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(header)
        set_run_font(run, HEAD_FONT, font_size, True, BRAND)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].width = Cm(widths[index])
            p = cells[index].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            run = p.add_run(str(value))
            set_run_font(run, BODY_FONT, font_size)
    return table


def add_caption(document, text):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    set_run_font(run, BODY_FONT, 8.5, False, MUTED)


def add_image(document, filename, width_cm=16.5, caption=None):
    path = os.path.join(DIAG, filename) if not os.path.isabs(filename) else filename
    if not os.path.exists(path):
        return
    document.add_picture(path, width=Cm(width_cm))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.paragraphs[-1].paragraph_format.keep_with_next = True
    if caption:
        add_caption(document, caption)


def add_image_row(document, items, width_cm=8.0):
    table = document.add_table(rows=1, cols=len(items))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    for index, (path, caption) in enumerate(items):
        cell = table.rows[0].cells[index]
        cell.width = Cm(width_cm + 0.8)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if os.path.exists(path):
            p.add_run().add_picture(path, width=Cm(width_cm))
        sub = cell.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = sub.add_run(caption)
        set_run_font(run, BODY_FONT, 8, False, MUTED)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)
    set_run_font(run, BODY_FONT, 8, False, MUTED)


def build() -> str:
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.1)
    section.bottom_margin = Cm(1.9)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = header.add_run("《软件工程》实验二 · CampusEvent · baseline-v1")
    set_run_font(run, BODY_FONT, 8.5, False, MUTED)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(footer)

    # ---------- 封面 ----------
    for _ in range(3):
        para(document, "", size=11)
    para(document, "《软件工程》课程实验二", 14, True, MUTED, WD_ALIGN_PARAGRAPH.CENTER, 6)
    para(document, "校园活动报名与管理系统", 26, True, INK, WD_ALIGN_PARAGRAPH.CENTER, 4)
    para(document, "项目总结（初始版本 baseline-v1）", 15, False, BRAND, WD_ALIGN_PARAGRAPH.CENTER, 24)
    para(
        document,
        "直接报名 / 审核报名 · 策略模式 · 观察者通知 · SQLite 持久化",
        11,
        False,
        MUTED,
        WD_ALIGN_PARAGRAPH.CENTER,
        30,
    )

    info = document.add_table(rows=5, cols=2)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    info.autofit = False
    rows = [
        ("课程名称", "软件工程"),
        ("实验名称", "实验二：基于设计模式的校园活动报名与管理系统"),
        ("班级 / 学号", "24计科2班 / 242806010203"),
        ("姓名", "刘东梁"),
        ("提交日期", "2026 年 11 月 25 日"),
    ]
    for index, (key, value) in enumerate(rows):
        cells = info.rows[index].cells
        cells[0].width = Cm(4.0)
        cells[1].width = Cm(10.0)
        shade(cells[0], "EEF3FF")
        p0 = cells[0].paragraphs[0]
        r0 = p0.add_run(key)
        set_run_font(r0, HEAD_FONT, 10, True, BRAND)
        p1 = cells[1].paragraphs[0]
        r1 = p1.add_run(value)
        set_run_font(r1, BODY_FONT, 10)

    para(document, "", size=10)
    para(
        document,
        "说明：教师需求变更单（CR）尚未发布。本报告只覆盖初始版本；"
        "变更版类图、影响分析与回归结果留待 CR 发布后补充，不虚构数据。",
        9,
        False,
        MUTED,
        WD_ALIGN_PARAGRAPH.CENTER,
        6,
    )

    document.add_page_break()

    # ---------- 1 目标与范围 ----------
    heading(document, "1  实验目标与范围", 1)
    para(
        document,
        "本实验以校园活动报名与管理系统 CampusEvent 为载体，练习从需求中识别领域对象、"
        "业务服务与职责边界，使用策略模式表达两类报名规则，使用观察者/事件分发解耦报名与通知，"
        "并在实现前完成类图与关键时序图。初始版本还需完成自动化测试、真实运行验收与云服务器部署。",
    )
    heading(document, "1.1  范围", 2)
    para(
        document,
        "实现 P2-F01—P2-F08：活动管理、活动浏览与名称筛选、报名/取消、两类报名规则、"
        "管理员审批、状态管理、站内通知、按活动统计。角色为学生与管理员，使用固定演示账号，"
        "不实现注册与复杂权限。",
    )
    para(
        document,
        "明确不做：候补队列、邮件/短信、活动签到、分页、移动端 App、第三方日历、真实支付。"
        "教师 CR 发布前不提前实现任何变更功能。",
    )

    heading(document, "1.2  验收依据", 1)
    para(
        document,
        "以指导书 3.5 节 C1—C10 为最低验收用例；以附录 B 的业务规则为边界；"
        "以 README 可从零启动、pytest 可复现、公网可访问为交付标准。",
    )

    # ---------- 2 需求分析 ----------
    heading(document, "2  需求分析", 1)
    para(
        document,
        "核心用例包括：登录/登出（UC-01）、浏览与筛选活动（UC-02）、查看详情（UC-03）、"
        "报名（UC-04）、取消报名（UC-05）、审批（UC-06）、管理活动（UC-07）、查看消息（UC-08）、"
        "查看统计（UC-09）。关键规则如下：",
    )
    add_table(
        document,
        ["规则", "内容"],
        [
            ("BR-01", "容量为正整数；已通过数不得超过容量。"),
            ("BR-02", "直接报名：有名额立即通过；满额不落库。"),
            ("BR-03", "审核型：提交后待审核，待审核不占名额。"),
            ("BR-04", "批准时再次检查名额；满额保持待审核。"),
            ("BR-05", "同一学生同一活动最多一条有效报名；取消/拒绝后可再报。"),
            ("BR-06", "活动开始后禁止新增报名；取消不受开始时间限制。"),
            ("BR-07", "有报名记录的活动不能删除；容量不得低于已通过数。"),
            ("BR-08", "通知失败留痕，不回滚已提交的报名。"),
        ],
        [1.6, 14.6],
    )
    para(
        document,
        "数据对象：Student、Activity、Registration、Message，以及 notification_attempt 通知尝试表。"
        "详细字段、用例说明与追踪矩阵见 docs/01_需求分析.md。",
        size=10,
    )

    # ---------- 3 设计 ----------
    heading(document, "3  软件设计", 1)
    para(
        document,
        "系统采用 Web → Service → Domain/Repository → SQLite 的分层依赖。Web 只做参数与页面，"
        "Service 编排用例与事务，Domain 承载规则，Repository 隔离 SQL；Domain 不依赖 Flask。",
    )
    add_image(document, "component.png", 15.0, "图 1  组件与依赖方向")

    heading(document, "3.1  领域模型与职责", 2)
    para(
        document,
        "Student 表示学生身份；Activity 保存活动信息并提供 is_open/remaining；Registration 保存报名状态；"
        "Message 保存站内消息。报名业务由 RegistrationService 编排，审批由 ApprovalService 编排，"
        "统计由 StatisticsService 聚合。",
    )
    add_image(document, "class-v1.png", 17.0, "图 2  初版 UML 类图（baseline-v1）")

    heading(document, "3.2  策略模式：两类报名规则", 2)
    para(
        document,
        "RegistrationPolicy 定义 decide(context) → PolicyDecision；DirectRegistrationPolicy 有名额时返回"
        "“已通过”，否则拒绝；ApprovalRegistrationPolicy 返回“待审核”。PolicyRegistry 按 PolicyType 选择实现，"
        "未知类型显式报错，避免静默降级。",
    )
    para(
        document,
        "名额检查的位置是本次设计的关键决策：直接报名在提交时判断名额，审核型在批准时判断，"
        "因此名额不属于所有策略的公共前置条件。设计上把名额计算抽为 CapacityChecker，"
        "由策略与审批服务复用；RegistrationService 只校验活动存在、未开始、无有效报名等公共条件，"
        "不硬编码报名类型分支。",
    )

    heading(document, "3.3  观察者：报名与通知解耦", 2)
    para(
        document,
        "报名/审批先在 BEGIN IMMEDIATE 事务中提交，提交后发布 DomainEvent；EventPublisher 逐个通知观察者。"
        "InAppNotificationObserver 写站内消息；notification_attempt 以 (event_id, channel) 唯一记录 PENDING/SENT/FAILED，"
        "实现幂等与失败留痕。通知异常不回滚报名，页面也不宣称通知一定成功。",
    )
    add_image(
        document,
        "sequence-direct.png",
        14.5,
        "图 3  直接报名时序图（管理员审批时序图见 docs/diagrams/sequence-approval-decision.png）",
    )
    para(
        document,
        "状态机：待审核可转已通过/已拒绝/已取消；已通过可转已取消；已拒绝/已取消为终态。"
        "批准必须发生在活动开始前，取消不限制开始时间；状态转换在服务层校验，数据库 CHECK 兜底。",
        size=10,
    )

    heading(document, "3.4  SOLID 与模式成本", 2)
    para(
        document,
        "SRP：策略只决定受理结果，服务只编排，观察者只发通知，仓储只做 SQL。OCP：新增规则/渠道通过新增实现与注册，"
        "不改主流程。LSP：两种策略可互换。DIP：服务依赖策略、观察者、仓储抽象。代价是类比 if/else 多 5—7 个，"
        "调用链更长；但本项目的两类规则与通知解耦是真实变化点，收益大于成本。",
    )
    para(
        document,
        "为后续 CR 预留：PolicyRegistry、NotificationObserver、PRAGMA user_version 与变更分析模板。"
        "本次不预实现候补/邮件等未发布功能。",
        size=10,
    )

    # ---------- 4 实现 ----------
    heading(document, "4  实现与运行", 1)
    para(
        document,
        "技术栈：Python 3.12、Flask 3.1、Jinja2、SQLite（标准库 sqlite3）、pytest。前端手写 CSS，无 CDN/npm。"
        "数据库包含 student、activity、registration、message、notification_attempt 五张表；"
        "registration 上建立部分唯一索引 ux_registration_active，保证同一学生同一活动最多一条有效报名。",
    )
    para(
        document,
        "写路径使用 BEGIN IMMEDIATE：报名在事务内复查有效报名与名额；批准在事务内复查活动未开始、名额、"
        "并以 UPDATE ... WHERE status='PENDING' 检查并发；取消校验归属与状态。所有 SQL 参数化，"
        "模板自动转义，密码使用 werkzeug 哈希。",
    )
    add_image_row(
        document,
        [
            (os.path.join(EVID, "C2-报名后详情.png"), "图 5  直接报名成功"),
            (os.path.join(EVID, "C4-C名额已满.png"), "图 6  满额拒绝"),
        ],
        8.2,
    )
    para(
        document,
        "活动管理端支持创建/编辑/删除、容量下限检查、已有有效报名时锁定报名方式；"
        "有报名记录的活动拒绝删除。删除确认、审批、取消等危险操作均有二次确认。",
        size=10,
    )

    # ---------- 5 测试 ----------
    heading(document, "5  测试与验收", 1)
    para(
        document,
        "测试环境：Windows 11、Python 3.12.14、Flask 3.1.3、pytest 9.2.0、SQLite。"
        "自动化测试 107 条全部通过；真实 HTTP 验收 C1—C10 全部通过，证据保存为 HTML/JSON/PNG。",
    )
    add_table(
        document,
        ["用例", "场景", "结果"],
        [
            ("C1", "创建直接报名活动，容量 2", "通过"),
            ("C2", "直接报名自动通过并通知", "通过"),
            ("C3", "重复有效报名被拒绝", "通过"),
            ("C4", "满额后第三名学生报名失败", "通过"),
            ("C5", "审核型报名进入待审核", "通过"),
            ("C6", "批准待审核并通知", "通过"),
            ("C7", "拒绝待审核并通知", "通过"),
            ("C8", "满额批准失败，保持待审核", "通过"),
            ("C9", "取消报名，统计同步变化", "通过"),
            ("C10", "重启后数据仍一致", "通过"),
        ],
        [2.0, 12.0, 2.2],
        font_size=9,
    )
    para(document, "", size=2)
    add_image_row(
        document,
        [
            (os.path.join(EVID, "C6-审核通过消息.png"), "图 7  审核通过站内消息"),
            (os.path.join(EVID, "C9-我的报名.png"), "图 8  取消后的报名历史"),
        ],
        8.2,
    )
    para(
        document,
        "缺陷与修复：① Windows 缺少 tzdata 导致时区加载失败，加入依赖后通过；"
        "② 重复报名竞态，增加部分唯一索引与 BEGIN IMMEDIATE；"
        "③ 通知失败可能影响报名，改为提交后发布并写通知尝试表；"
        "④ 验收脚本误把 flash 标题当表格行，改为从 title-cell 解析后重跑通过。",
        size=9.5,
    )

    # ---------- 6 部署 ----------
    heading(document, "6  部署", 1)
    para(
        document,
        "项目已部署到 The Vibe Hosting：https://campusevent-app.thevibehosting.com 。"
        "运行方式为 gunicorn 单 worker、2 线程，监听容器 80；SQLite 位于 /root/myapp/instance/campus_event.db。"
        "平台自动提供 HTTPS 子域，免费容器闲置约 10 分钟休眠，首次访问需 1—3 秒唤醒。",
    )
    add_image_row(
        document,
        [
            (os.path.join(EVID, "public-home.png"), "图 9  公网登录页"),
            (os.path.join(EVID, "线上-管理页.png"), "图 10  公网管理页"),
        ],
        8.2,
    )
    para(
        document,
        "演示账号：admin/admin123、2024001/123456、2024002/123456、2024003/123456。"
        "公网只使用虚构演示数据；管理员密码、密钥与数据库均不提交仓库。",
        size=9.5,
    )

    # ---------- 7 变更阶段 ----------
    heading(document, "7  需求变更阶段说明", 1)
    para(
        document,
        "截至本报告，教师需求变更单（CR）尚未发布。按课程要求，学生不得提前针对 CR 实现功能；"
        "因此本版本不包含变更后的类图、影响分析、回归结果或可维护性指标。",
    )
    para(
        document,
        "已为变更做好准备：报名规则通过 RegistrationPolicy 抽象，新规则只需新增实现并在 Registry 注册；"
        "通知通过 NotificationObserver 抽象，新渠道只需新增观察者；数据库以 PRAGMA user_version=1 记录版本，"
        "后续通过迁移脚本升级；变更分析模板见 docs/04_变更影响分析_模板.md。",
    )
    para(
        document,
        "CR 发布后：从 baseline-v1 建分支 → 先写影响分析 → 实现 → 运行全部 C1—C10 与新增用例 → "
        "打 change-v2 标签 → 更新 V2 类图、回归表、本报告与 PPT。上述内容本次均未实施，避免虚构。",
        size=10,
    )

    # ---------- 8 问题与反思 ----------
    heading(document, "8  问题与反思", 1)
    bullet(
        document,
        "设计决策必须由人做：AI 初稿倾向把名额检查放在服务层；审核型报名提交时不占名额，"
        "这一业务语义只有回到需求才能发现。最终由人决定“策略决策 + 共享 CapacityChecker”。",
    )
    bullet(
        document,
        "模式不是目的：策略/观察者增加了类与调用链；如果只有一种报名规则、一个通知渠道，直接实现更简单。"
        "本项目的收益来自两类规则与通知解耦这一真实变化点。",
    )
    bullet(
        document,
        "AI 产出必须验证：验收脚本曾把 flash 中的活动名当成表格行，导致用例操作到错误活动；"
        "只有真实 HTTP 重跑与证据核对才发现。后续仍需坚持“AI 生成、人来验收”。",
    )
    bullet(
        document,
        "边界与诚实：本次没有 CR，就没有变更数据；报告中明确写“待补充”，不用推测数字替代。"
        "设计评审签名也需同班同学完成，不能代签。",
    )

    # ---------- 附录 ----------
    heading(document, "附录  运行与证据", 1)
    para(
        document,
        "启动：python -m venv .venv → pip install -r requirements.txt → python cli.py seed-demo → python run.py。"
        "测试：python -m pytest（107 passed）。公网：https://campusevent-app.thevibehosting.com 。",
        size=9.5,
    )
    para(
        document,
        "代码与文档：app/、tests/、docs/；证据：docs/evidence/acceptance-log.json 与 docs/evidence/png/；"
        "Git 标签：baseline-v1。变更版标签 change-v2 待 CR 后创建。",
        size=9.5,
    )

    os.makedirs(DOCS, exist_ok=True)
    document.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
