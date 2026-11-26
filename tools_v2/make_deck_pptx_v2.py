"""生成实验二 change-v2 答辩 PPT（14 页）。"""

from __future__ import annotations

import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DIAG = os.path.join(DOCS, "diagrams")
EVID = os.path.join(DOCS, "evidence", "change-v2")
OUT = os.path.join(DOCS, "09_实验二答辩PPT_v2_24计科2班_刘东梁.pptx")

FONT = "微软雅黑"
NAVY = RGBColor(0x10, 0x22, 0x4D)
BLUE = RGBColor(0x1F, 0x5E, 0xFF)
TEAL = RGBColor(0x0F, 0x9F, 0x8F)
INK = RGBColor(0x17, 0x20, 0x33)
MUTED = RGBColor(0x65, 0x70, 0x83)
LIGHT = RGBColor(0xF4, 0xF7, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xB7, 0x79, 0x1F)


def style(run, size, bold=False, color=INK):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.language_id = 0x0804


def text(slide, left, top, width, height, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = frame.margin_right = Inches(0.03)
    frame.margin_top = frame.margin_bottom = Inches(0.03)
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(3)
        if isinstance(line, tuple):
            value, size, bold, color = line
        else:
            value, size, bold, color = line, 15, False, INK
        r = p.add_run()
        r.text = value
        style(r, size, bold, color)
    return box


def rect(slide, left, top, width, height, fill, radius=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def bg(slide, color=LIGHT):
    rect(slide, 0, 0, 13.333, 7.5, color, radius=False)


def header(slide, kicker, title, dark=False):
    text(slide, 0.7, 0.36, 9, 0.3, [(kicker, 10.5, True, RGBColor(0x8F, 0xD8, 0xD0) if dark else TEAL)])
    text(slide, 0.7, 0.66, 11.8, 0.7, [(title, 27, True, WHITE if dark else INK)])


def footer(slide, number, dark=False):
    color = RGBColor(0xB8, 0xC4, 0xDA) if dark else MUTED
    text(slide, 0.7, 7.1, 7, 0.25, [("CampusEvent · change-v2 · 24计科2班 刘东梁", 8.5, False, color)])
    text(slide, 12.0, 7.1, 0.6, 0.25, [(f"{number:02d}", 8.5, True, color)], PP_ALIGN.RIGHT)


def new(prs, number, kicker, title, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg(slide, NAVY if dark else LIGHT)
    header(slide, kicker, title, dark)
    footer(slide, number, dark)
    return slide


def image(slide, path, left, top, max_w, max_h):
    if not os.path.exists(path):
        return
    with Image.open(path) as im:
        w, h = im.size
    ratio = min(max_w / w, max_h / h)
    slide.shapes.add_picture(path, Inches(left), Inches(top), width=Inches(w * ratio), height=Inches(h * ratio))


def card(slide, left, top, width, height, title, body, accent=BLUE):
    rect(slide, left, top, width, height, WHITE)
    rect(slide, left, top, 0.07, height, accent, radius=False)
    text(slide, left + 0.2, top + 0.14, width - 0.35, 0.35, [(title, 13.5, True, INK)])
    text(slide, left + 0.2, top + 0.58, width - 0.35, height - 0.65, [(body, 10, False, MUTED)])


def table(slide, rows, left, top, width, height, widths, size=9.5):
    t = slide.shapes.add_table(len(rows), len(rows[0]), Inches(left), Inches(top), Inches(width), Inches(height)).table
    for i, w in enumerate(widths):
        t.columns[i].width = Inches(w)
    for ri, row in enumerate(rows):
        t.rows[ri].height = Inches(height / len(rows))
        for ci, value in enumerate(row):
            cell = t.cell(ri, ci)
            cell.text = ""
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if ri == 0 else (WHITE if ri % 2 else RGBColor(0xF8, 0xFA, 0xFF))
            p = cell.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(value)
            style(r, size, ri == 0, WHITE if ri == 0 else INK)


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg(slide, NAVY)
    rect(slide, 0, 0, 0.12, 7.5, TEAL, radius=False)
    text(slide, 0.9, 1.0, 7, 0.35, [("SOFTWARE ENGINEERING · LAB 2 · CHANGE", 10.5, True, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 0.9, 1.55, 12, 0.9, [("CampusEvent", 44, True, WHITE)])
    text(slide, 0.9, 2.55, 11.8, 0.5, [("校园活动报名与管理系统 · change-v2", 21, False, RGBColor(0xD8, 0xE2, 0xF4))])
    text(slide, 0.9, 3.3, 11.5, 0.5, [("CR-01 年级限定报名  ·  CR-02 Mock 邮件  ·  v1→v2 迁移  ·  C1—C10 回归", 13, False, RGBColor(0xB8, 0xC4, 0xDA))])
    rect(slide, 0.9, 4.45, 5.7, 0.05, TEAL, radius=False)
    text(slide, 0.9, 4.7, 6, 0.8, [("24计科2班  242806010203  刘东梁", 14, True, WHITE), ("2026 年 11 月 26 日", 11, False, RGBColor(0xB8, 0xC4, 0xDA))])
    text(slide, 8.0, 4.7, 4.5, 0.5, [("https://campusevent-app.thevibehosting.com", 9.5, False, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 0.9, 6.55, 11.5, 0.4, [("原 app/、tests/、run.py、cli.py 保持 baseline 原样；变更集中在 app_v2/、tests_v2/。", 9.5, False, RGBColor(0x8F, 0x9F, 0xBD))])
    slide.notes_slide.notes_text_frame.text = "开场：change-v2 在 baseline-v1 上完成 CR-01/CR-02；原代码未改。"

    # 2
    slide = new(prs, 2, "CHANGE SCOPE", "变更范围：两单 CR，核心服务零修改")
    card(slide, 0.7, 1.65, 3.8, 2.0, "CR-01 年级限定", "Student.grade；新增 GRADE_DIRECT 策略；仅大二/大三；其他年级拒绝。", TEAL)
    card(slide, 4.75, 1.65, 3.8, 2.0, "CR-02 Mock 邮件", "站内 + 邮件双通道；失败留痕；事件级幂等；不接真实 SMTP。", BLUE)
    card(slide, 8.8, 1.65, 3.8, 2.0, "v1→v2 迁移", "grade、策略 CHECK、email_outbox；旧数据保留、外键校验。", AMBER)
    rect(slide, 0.7, 4.05, 11.95, 1.15, WHITE)
    text(slide, 0.95, 4.22, 11.4, 0.9, [("代码组织：baseline 原样 vs change-v2 独立目录", 13.5, True, INK), ("app/、tests/、run.py、cli.py 与 baseline-v1 完全一致；变更全部在 app_v2/、tests_v2/、run_v2.py、cli_v2.py。", 10, False, MUTED)])
    text(slide, 0.7, 5.65, 12, 0.5, [("验收：CR1-01—05、CR2-01—05、MIG-01 共 11 项；C1—C10 回归 10/10；pytest 123 条。", 10, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "强调原代码不动、v2 目录独立，便于对比两版。"

    # 3
    slide = new(prs, 3, "REQUIREMENTS", "需求：变更后的规则")
    rows = [
        ["变更", "规则", "验收"],
        ["CR-01", "grade 1—4；仅 2/3 可报名；名额/开始时间/重复报名约束不变", "CR1-01—05"],
        ["CR-02", "报名通过、审核通过/拒绝发 Mock 邮件；失败留痕不回滚；不重复", "CR2-01—05"],
        ["MIG-01", "v1→v2 数据迁移；grade、策略 CHECK、email_outbox", "迁移测试"],
    ]
    table(slide, rows, 0.7, 1.65, 11.9, 2.4, [1.4, 8.3, 2.2], 9.5)
    rect(slide, 0.7, 4.35, 5.8, 2.15, NAVY)
    text(slide, 0.95, 4.5, 5.3, 0.35, [("关键决策", 13, True, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 0.95, 4.9, 5.3, 1.4, [("• 年级限定 = 新策略，不改 RegistrationService", 9.5, False, WHITE), ("• 邮件 = 新观察者 + 发件箱，不改 ApprovalService", 9.5, False, WHITE), ("• 待审核不发邮件；只有通过/拒绝进入邮件通道", 9.5, False, WHITE)])
    rect(slide, 6.8, 4.35, 5.8, 2.15, WHITE)
    text(slide, 7.05, 4.5, 5.3, 0.35, [("不变项", 13, True, INK)])
    text(slide, 7.05, 4.9, 5.3, 1.4, [("• 直接/审核报名行为", 9.5, False, MUTED), ("• 名额、开始时间、重复报名约束", 9.5, False, MUTED), ("• 原有站内消息", 9.5, False, MUTED), ("• C1—C10 验收", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "需求表；强调原行为不变。"

    # 4
    slide = new(prs, 4, "ARCHITECTURE", "变更落在两个扩展点")
    rect(slide, 0.7, 1.7, 5.7, 2.0, WHITE)
    text(slide, 0.95, 1.85, 5.2, 0.4, [("策略扩展点", 14, True, TEAL)])
    text(slide, 0.95, 2.3, 5.2, 1.2, [("RegistrationPolicy + PolicyRegistry", 10.5, False, INK), ("新增 GradeLimitedDirectRegistrationPolicy；Service 只依赖抽象。", 9.5, False, MUTED)])
    rect(slide, 6.85, 1.7, 5.7, 2.0, WHITE)
    text(slide, 7.1, 1.85, 5.2, 0.4, [("通知扩展点", 14, True, BLUE)])
    text(slide, 7.1, 2.3, 5.2, 1.2, [("NotificationObserver + EventPublisher", 10.5, False, INK), ("新增 EmailNotificationObserver；on_error 记录失败详情。", 9.5, False, MUTED)])
    rect(slide, 0.7, 4.05, 11.85, 1.6, NAVY)
    text(slide, 0.95, 4.2, 11.3, 0.35, [("依赖方向不变", 13, True, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 0.95, 4.6, 11.3, 0.8, [("Web → Service → Domain/Repository → SQLite；Domain 不依赖 Flask。", 10.5, False, WHITE), ("baseline 的 app/ 未改；v2 的 app_v2/ 独立组装，run_v2/cli_v2 为入口。", 9.5, False, RGBColor(0xD8, 0xE2, 0xF4))])
    text(slide, 0.7, 6.1, 12, 0.5, [("代价：通知子系统多两个钩子；迁移需重建 student/activity。", 10, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "架构：两个扩展点；原代码不动，v2 独立目录。"

    # 5
    slide = new(prs, 5, "DOMAIN MODEL", "变更版类图：新增 7 个类/异常")
    image(slide, os.path.join(DIAG, "class-v2.png"), 0.35, 1.5, 12.6, 4.95)
    text(slide, 0.7, 6.55, 12, 0.4, [("新增：年级策略、邮件观察者、MockSender、Outbox 模型/仓储、邮件服务/异常；EventPublisher 增加钩子。", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "类图：核心服务未改，新增策略/观察者/发件箱。"

    # 6
    slide = new(prs, 6, "CR-01 STRATEGY", "年级限定：先看年级，再看名额")
    for i, (num, title_, body) in enumerate([
        ("1", "公共前置条件", "活动存在、未开始、无有效报名；Service 统一校验。"),
        ("2", "策略判断年级", "grade ∈ {2,3}？不在则明确拒绝。"),
        ("3", "复用名额判断", "CapacityChecker；满额返回名额已满。"),
    ]):
        left = 0.7 + i * 2.55
        rect(slide, left, 1.7, 2.3, 1.85, WHITE)
        rect(slide, left, 1.7, 0.06, 1.85, TEAL, radius=False)
        text(slide, left + 0.15, 1.82, 0.4, 0.35, [(num, 18, True, TEAL)])
        text(slide, left + 0.55, 1.82, 1.65, 0.4, [(title_, 11, True, INK)])
        text(slide, left + 0.15, 2.35, 2.0, 1.05, [(body, 9.2, False, MUTED)])
    rect(slide, 8.4, 1.7, 4.25, 1.85, NAVY)
    text(slide, 8.6, 1.84, 3.9, 0.35, [("设计理由", 12, True, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 8.6, 2.22, 3.9, 1.15, [("年级限制是报名规则，不是服务公共前置条件；新策略可独立测试，原直接/审核策略不动。", 9.2, False, WHITE)])
    rect(slide, 0.7, 3.9, 11.9, 2.15, RGBColor(0x10, 0x22, 0x4D))
    text(slide, 0.95, 4.05, 11.4, 0.35, [("策略骨架", 11, True, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 0.95, 4.45, 11.4, 1.4, [("if ctx.student.grade not in {2, 3}:", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)), ("    return PolicyDecision(False, reason='该活动仅限大二、大三学生报名')", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)), ("return APPROVED if capacity.has_capacity(...) else '名额已满'", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4))])
    text(slide, 0.7, 6.25, 12, 0.4, [("测试：CR1-01—04；原 C1—C10 回归通过。", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "CR-01：独立策略；RegistrationService 零修改。"

    # 7
    slide = new(prs, 7, "CR-02 OBSERVER", "邮件：并行观察者 + 发件箱")
    image(slide, os.path.join(DIAG, "sequence-email.png"), 0.45, 1.55, 8.1, 5.0)
    rect(slide, 8.8, 1.65, 3.9, 4.9, WHITE)
    text(slide, 9.0, 1.82, 3.5, 0.35, [("事务与失败", 13.5, True, INK)])
    text(slide, 9.0, 2.25, 3.5, 3.9, [("1. 报名/审批事务提交", 10, True, BLUE), ("2. 发布 DomainEvent", 9.5, False, MUTED), ("3. supports() 过滤待审核", 10, True, BLUE), ("4. email_outbox PENDING", 9.5, False, MUTED), ("5. 发送成功 SENT", 10, True, TEAL), ("6. 失败 on_error → FAILED", 10, True, AMBER), ("7. 报名不回滚，不重复发送", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "CR-02：观察者 + 发件箱；失败留痕、幂等。"

    # 8
    slide = new(prs, 8, "MIGRATION", "v1→v2：数据保留是硬约束")
    rows = [["对象", "v1", "v2", "处理"],
            ["student", "无 grade", "grade 1—4", "重建表，默认 1"],
            ["activity", "CHECK 2 值", "CHECK 3 值", "重建表"],
            ["email_outbox", "无", "event_id UNIQUE", "新建"],
            ["数据", "学生/活动/报名/消息", "全部保留", "事务复制 + 外键校验"]]
    table(slide, rows, 0.7, 1.65, 11.9, 2.7, [2.0, 3.4, 3.4, 3.1], 9.5)
    card(slide, 0.7, 4.65, 5.8, 1.7, "迁移风险", "SQLite 不能改 CHECK；重建表、复制数据、修正序列、关闭/恢复外键。", AMBER)
    card(slide, 6.85, 4.65, 5.8, 1.7, "验证", "test_migration_v2：user_version=2、grade、email_outbox、外键、序列。", TEAL)
    slide.notes_slide.notes_text_frame.text = "迁移：重建两张表；测试保证数据/外键/序列。"

    # 9
    slide = new(prs, 9, "DEMO", "真实运行：拒绝与邮件记录")
    image(slide, os.path.join(EVID, "png", "CR1-03-大一拒绝.png"), 0.55, 1.55, 6.0, 4.9)
    image(slide, os.path.join(EVID, "png", "CR2-02-邮件记录.png"), 6.85, 1.55, 6.0, 4.9)
    text(slide, 0.7, 6.55, 12, 0.35, [("左：大一报名被明确拒绝；右：站内消息 + Mock 邮件记录（收件人/主题/状态）。", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "演示：年级拒绝与邮件记录。"

    # 10
    slide = new(prs, 10, "TEST & REGRESSION", "123 条测试；C1—C10 回归 10/10")
    rows = [["类型", "数量/结果"],
            ["change-v2 pytest", "123 passed"],
            ["baseline pytest（原样）", "107 passed"],
            ["C1—C10 真实 HTTP 回归", "10/10"],
            ["CR1/CR2/MIG 验收", "11/11"],
            ["迁移测试", "通过"]]
    table(slide, rows, 0.7, 1.65, 7.2, 3.4, [4.3, 2.9], 10)
    rect(slide, 8.25, 1.65, 4.4, 1.65, NAVY)
    text(slide, 8.45, 1.8, 4.0, 0.5, [("123", 30, True, WHITE)])
    text(slide, 8.45, 2.45, 4.0, 0.4, [("change-v2 全量通过", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4))])
    rect(slide, 8.25, 3.5, 4.4, 3.0, WHITE)
    text(slide, 8.45, 3.65, 4.0, 0.35, [("缺陷修复", 12, True, INK)])
    text(slide, 8.45, 4.05, 4.0, 2.2, [("• SQLite CHECK 迁移", 9.5, False, MUTED), ("• 邮件失败记录被回滚 → on_error", 9.5, False, MUTED), ("• 待审核误发邮件 → supports", 9.5, False, MUTED), ("• 旧 gunicorn 未重启 → 显式停止", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "测试：123 + 107；C1—C10 回归 10/10；CR 11/11。"

    # 11
    slide = new(prs, 11, "DEPLOYMENT", "已部署 change-v2")
    image(slide, os.path.join(EVID, "public", "png", "public-home.png"), 0.65, 1.6, 5.9, 4.85)
    image(slide, os.path.join(EVID, "public", "png", "线上-管理页-v2.png"), 6.75, 1.6, 5.9, 4.85)
    text(slide, 0.7, 6.55, 12, 0.35, [("https://campusevent-app.thevibehosting.com  ·  gunicorn 1 worker  ·  v2 数据库  ·  冷启动 1—3s", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "公网：app_v2 运行；5 个活动含年级限定；通知记录。"

    # 12
    slide = new(prs, 12, "MAINTAINABILITY", "可维护性：核心业务类 0 修改")
    rows = [["指标", "baseline-v1", "change-v2"],
            ["自动化测试", "107", "123"],
            ["新增类/异常", "—", "7"],
            ["修改核心业务类", "—", "0"],
            ["修改通知基础设施", "—", "1"],
            ["回归失败", "—", "0"],
            ["AI 关键交互", "—", "约 6 轮"],
            ["集中修改时长", "—", "约 2 小时"]]
    table(slide, rows, 0.7, 1.65, 7.8, 3.9, [3.7, 2.0, 2.1], 10)
    rect(slide, 8.8, 1.65, 3.85, 3.9, NAVY)
    text(slide, 9.0, 1.85, 3.45, 0.4, [("结论", 14, True, RGBColor(0x8F, 0xD8, 0xD0))])
    text(slide, 9.0, 2.35, 3.45, 2.9, [("策略/观察者扩展使核心服务零修改；", 10, False, WHITE), ("代价：通知子系统多两个钩子、迁移重建两张表。", 10, False, WHITE), ("收益：规则/渠道可独立测试、独立失败、可观测。", 10, False, WHITE)])
    text(slide, 0.7, 5.9, 12, 0.5, [("变更范围合理：新增 7 个类 + 1 个迁移；未出现核心服务分支膨胀。", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "可维护性：0 核心业务类修改；成本/收益。"

    # 13
    slide = new(prs, 13, "REFLECTION", "问题与反思")
    items = [
        ("迁移是风险中心", "SQLite 不能改 CHECK；用重建表 + 事务 + 外键检查 + 迁移测试控制风险。"),
        ("失败语义更难", "邮件失败不能回滚报名，也不能丢错误；on_error + email_outbox FAILED 解决。"),
        ("原代码不动的代价", "app_v2 目录重复；换来 baseline/change 两版可并列比较、可追溯。"),
        ("部署必须显式停止旧进程", "旧 baseline gunicorn 读取 v2 GRADE_DIRECT 会 500；部署脚本已改为 pkill gunicorn。"),
    ]
    for i, (title_, body) in enumerate(items):
        left = 0.7 + (i % 2) * 6.0
        top = 1.7 + (i // 2) * 2.3
        rect(slide, left, top, 5.75, 1.95, WHITE)
        text(slide, left + 0.2, top + 0.15, 5.3, 0.35, [(title_, 12.5, True, INK)])
        text(slide, left + 0.2, top + 0.58, 5.3, 1.2, [(body, 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "反思：迁移、失败语义、代码组织、部署进程。"

    # 14
    slide = new(prs, 14, "CONCLUSION", "change-v2 完成；两版可追溯", dark=True)
    text(slide, 0.9, 1.55, 11.5, 0.8, [("baseline-v1：两类报名 + 站内消息；change-v2：+ 年级限定 + Mock 邮件。", 16, True, WHITE)])
    card(slide, 0.9, 2.7, 3.75, 1.9, "标签", "baseline-v1 / change-v2", TEAL)
    card(slide, 4.85, 2.7, 3.75, 1.9, "测试", "123 + 107；C1—C10 10/10", BLUE)
    card(slide, 8.8, 2.7, 3.75, 1.9, "部署", "公网 change-v2；v1→v2 自动迁移", AMBER)
    text(slide, 0.9, 5.15, 11.6, 0.6, [("后续可做：真实 SMTP、候补队列、按活动配置年级范围、CSRF/限流。", 11, False, RGBColor(0xD8, 0xE2, 0xF4))])
    text(slide, 0.9, 6.4, 11.6, 0.35, [("谢谢！欢迎现场抽取变更功能演示。", 13, True, RGBColor(0x8F, 0xD8, 0xD0))])
    slide.notes_slide.notes_text_frame.text = "总结：两版标签；123+107 测试；公网；后续方向。"

    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
