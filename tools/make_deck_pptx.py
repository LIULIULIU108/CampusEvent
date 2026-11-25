"""生成实验二答辩 PPT（12 页，baseline-v1）。"""

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
EVID = os.path.join(DOCS, "evidence", "png")
OUT = os.path.join(DOCS, "09_实验二答辩PPT_24计科2班_刘东梁.pptx")

FONT = "微软雅黑"
NAVY = RGBColor(0x10, 0x22, 0x4D)
BLUE = RGBColor(0x1F, 0x5E, 0xFF)
TEAL = RGBColor(0x0F, 0x9F, 0x8F)
INK = RGBColor(0x17, 0x20, 0x33)
MUTED = RGBColor(0x65, 0x70, 0x83)
LIGHT = RGBColor(0xF4, 0xF7, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xB7, 0x79, 0x1F)
GREEN = RGBColor(0x1D, 0x7A, 0x4C)
RED = RGBColor(0xC0, 0x39, 0x2B)


def rgb(hex_value: str) -> RGBColor:
    value = hex_value.lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def style_run(run, size, bold=False, color=INK, font=FONT):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.language_id = 0x0804


def textbox(slide, left, top, width, height, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.04):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = align
        paragraph.space_after = Pt(3)
        if isinstance(line, tuple):
            text, size, bold, color = line
        else:
            text, size, bold, color = line, 16, False, INK
        run = paragraph.add_run()
        run.text = text
        style_run(run, size, bold, color)
    return box


def rect(slide, left, top, width, height, fill, line=None, radius=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    shape.shadow.inherit = False
    return shape


def background(slide, color=LIGHT):
    rect(slide, 0, 0, 13.333, 7.5, color, radius=False)


def header(slide, kicker, title, dark=False):
    textbox(slide, 0.7, 0.38, 9.5, 0.3, [(kicker, 11, True, TEAL if not dark else RGBColor(0x8F, 0xD8, 0xD0))])
    textbox(slide, 0.7, 0.68, 11.7, 0.7, [(title, 28, True, WHITE if dark else INK)])


def footer(slide, number, dark=False):
    color = RGBColor(0xB8, 0xC4, 0xDA) if dark else MUTED
    textbox(slide, 0.7, 7.08, 7.0, 0.25, [("CampusEvent · 实验二 · baseline-v1", 9, False, color)])
    textbox(slide, 11.9, 7.08, 0.7, 0.25, [(f"{number:02d}", 9, True, color)], PP_ALIGN.RIGHT)


def image_fit(slide, path, left, top, max_w, max_h):
    with Image.open(path) as image:
        width, height = image.size
    ratio = min(max_w / width, max_h / height)
    return slide.shapes.add_picture(path, Inches(left), Inches(top), width=Inches(width * ratio), height=Inches(height * ratio))


def new_slide(prs, number, kicker, title, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background(slide, NAVY if dark else LIGHT)
    header(slide, kicker, title, dark)
    footer(slide, number, dark)
    return slide


def card(slide, left, top, width, height, title, body, accent=BLUE, dark_text=True):
    rect(slide, left, top, width, height, WHITE)
    rect(slide, left, top, 0.07, height, accent, radius=False)
    textbox(slide, left + 0.2, top + 0.16, width - 0.35, 0.4, [(title, 14, True, INK)])
    textbox(slide, left + 0.2, top + 0.62, width - 0.35, height - 0.7, [(body, 10.5, False, MUTED)])


def add_table(slide, rows, left, top, width, height, col_widths, font_size=10, header=True):
    table = slide.shapes.add_table(rows=len(rows), cols=len(rows[0]), left=Inches(left), top=Inches(top), width=Inches(width), height=Inches(height)).table
    for index, column_width in enumerate(col_widths):
        table.columns[index].width = Inches(column_width)
    for row_index, row in enumerate(rows):
        table.rows[row_index].height = Inches(height / len(rows))
        for col_index, value in enumerate(row):
            cell = table.cell(row_index, col_index)
            cell.text = ""
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.04)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            fill = NAVY if (header and row_index == 0) else (WHITE if row_index % 2 else RGBColor(0xF8, 0xFA, 0xFF))
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill
            paragraph = cell.text_frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.LEFT
            run = paragraph.add_run()
            run.text = str(value)
            style_run(run, font_size, header and row_index == 0, WHITE if (header and row_index == 0) else INK)
    return table


def build() -> str:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1 封面
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background(slide, NAVY)
    rect(slide, 0, 0, 0.12, 7.5, TEAL, radius=False)
    textbox(slide, 0.9, 1.0, 6.0, 0.35, [("SOFTWARE ENGINEERING · LAB 2", 11, True, RGBColor(0x8F, 0xD8, 0xD0))])
    textbox(slide, 0.9, 1.55, 11.8, 0.9, [("CampusEvent", 44, True, WHITE)])
    textbox(slide, 0.9, 2.55, 11.8, 0.6, [("校园活动报名与管理系统 · baseline-v1", 22, False, RGBColor(0xD8, 0xE2, 0xF4))])
    textbox(slide, 0.9, 3.35, 11.0, 0.9, [("两类报名规则  ·  策略模式  ·  观察者通知  ·  SQLite  ·  公网部署", 14, False, RGBColor(0xB8, 0xC4, 0xDA))])
    rect(slide, 0.9, 4.55, 5.7, 0.05, TEAL, radius=False)
    textbox(slide, 0.9, 4.8, 6.4, 0.8, [("24计科2班  242806010203  刘东梁", 14, True, WHITE), ("2026 年 11 月 25 日", 11, False, RGBColor(0xB8, 0xC4, 0xDA))])
    textbox(slide, 8.15, 4.8, 4.2, 0.6, [("https://campusevent-app.thevibehosting.com", 10, False, RGBColor(0x8F, 0xD8, 0xD0))])
    textbox(slide, 0.9, 6.55, 11.5, 0.35, [("初始版本交付：设计 → 实现 → 107 条测试 → C1—C10 验收 → 公网部署；CR 尚未发布。", 10, False, RGBColor(0x8F, 0x9F, 0xBD))])
    slide.notes_slide.notes_text_frame.text = "开场：说明本次为实验二初始版本，CR 未发布，变更阶段后续进行。"

    # 2 目标
    slide = new_slide(prs, 2, "EXPERIMENT GOALS", "实验二要解决什么")
    card(slide, 0.7, 1.65, 3.85, 2.1, "设计先行", "从需求识别领域对象、服务与职责边界；先出用例、类图、时序图，再让 AI 写代码。", BLUE)
    card(slide, 4.75, 1.65, 3.85, 2.1, "用模式应对变化", "Strategy 封装两类报名规则；Observer 解耦报名与通知；用 SOLID 解释依赖方向。", TEAL)
    card(slide, 8.8, 1.65, 3.85, 2.1, "可验证交付", "C1—C10 真实 HTTP 验收；107 条 pytest；README 从零可运行；公网可访问。", AMBER)
    rect(slide, 0.7, 4.15, 11.95, 1.15, WHITE)
    textbox(slide, 0.95, 4.32, 11.4, 0.9, [
        ("本次范围：P2-F01—P2-F08，两类报名 + 站内通知", 15, True, INK),
        ("不做：候补、邮件/短信、签到、分页、移动端；CR 未发布，不提前实现任何变更功能。", 11, False, MUTED),
    ])
    textbox(slide, 0.7, 6.0, 11.95, 0.5, [("评价重点：职责划分是否合理、模式是否必要、测试是否可复现、变更是否可评估。", 11, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "强调范围边界：没有 CR 就没有变更实现，不虚构。"

    # 3 需求
    slide = new_slide(prs, 3, "REQUIREMENTS", "需求边界：八个功能点")
    rows = [
        ["编号", "功能", "初始实现"],
        ["P2-F01", "活动管理", "创建/编辑/删除；容量、报名方式"],
        ["P2-F02", "活动查看", "列表、名称筛选、详情"],
        ["P2-F03", "报名/取消", "禁止重复有效报名"],
        ["P2-F04", "报名策略", "直接通过 / 待审核"],
        ["P2-F05", "审批", "批准时复查名额"],
        ["P2-F06", "状态管理", "四状态与转换规则"],
        ["P2-F07", "站内通知", "结果消息、已读"],
        ["P2-F08", "统计", "已通过/待审核/剩余"],
    ]
    add_table(slide, rows, 0.7, 1.65, 7.3, 4.55, [1.15, 1.65, 4.4], 9)
    rect(slide, 8.35, 1.65, 4.3, 4.55, NAVY)
    textbox(slide, 8.6, 1.85, 3.8, 0.4, [("关键业务规则", 15, True, WHITE)])
    textbox(slide, 8.6, 2.35, 3.8, 3.6, [
        ("• 有效报名 = 待审核 / 已通过", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("• 待审核不占名额，批准才占", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("• 满额批准失败，保持待审核", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("• 取消/拒绝后允许重新申请", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("• 有报名记录的活动不能删除", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("• 通知失败只留痕，不回滚报名", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
    ])
    textbox(slide, 0.7, 6.4, 11.9, 0.4, [("设计由学生先定：AI 只按已评审的类图/接口实现，不自行扩大范围。", 10.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "需求表格与规则；强调待审核不占名额。"

    # 4 架构
    slide = new_slide(prs, 4, "ARCHITECTURE", "架构：依赖方向固定")
    image_fit(slide, os.path.join(DIAG, "component.png"), 0.55, 1.55, 9.0, 5.1)
    rect(slide, 9.75, 1.65, 2.95, 4.9, WHITE)
    textbox(slide, 9.95, 1.85, 2.6, 0.4, [("分层职责", 14, True, INK)])
    textbox(slide, 9.95, 2.35, 2.6, 4.0, [
        ("Web", 11, True, BLUE),
        ("会话、路由、页面", 9.5, False, MUTED),
        ("Service", 11, True, BLUE),
        ("用例编排、事务", 9.5, False, MUTED),
        ("Domain", 11, True, BLUE),
        ("策略、事件、实体", 9.5, False, MUTED),
        ("Repository", 11, True, BLUE),
        ("参数化 SQL", 9.5, False, MUTED),
        ("SQLite", 11, True, BLUE),
        ("单文件持久化", 9.5, False, MUTED),
    ])
    slide.notes_slide.notes_text_frame.text = "Web → Service → Domain/Repository；Domain 不依赖 Flask。"

    # 5 类图
    slide = new_slide(prs, 5, "DOMAIN MODEL", "领域模型：谁负责什么")
    image_fit(slide, os.path.join(DIAG, "class-v1.png"), 0.35, 1.5, 12.65, 4.95)
    textbox(slide, 0.7, 6.55, 12.0, 0.4, [("RegistrationService 编排；策略决定受理；观察者只负责通知；Repository 只做 SQL。", 10.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "类图重点：Activity/Student/Registration/Policy/Service/Observer。"

    # 6 策略
    slide = new_slide(prs, 6, "STRATEGY", "名额检查放在哪：策略决策 + 共享 CapacityChecker")
    steps = [
        ("1", "公共前置条件", "活动存在、未开始、无有效报名，由 Service 统一校验。"),
        ("2", "策略决定结果", "Direct：有名额→已通过；Approval：→待审核。"),
        ("3", "审批再次检查", "批准在 BEGIN IMMEDIATE 内复查名额与状态。"),
    ]
    for index, (num, title, body) in enumerate(steps):
        left = 0.7 + index * 2.55
        rect(slide, left, 1.7, 2.3, 1.9, WHITE)
        rect(slide, left, 1.7, 0.06, 1.9, BLUE if index < 2 else TEAL, radius=False)
        textbox(slide, left + 0.15, 1.82, 0.4, 0.35, [(num, 18, True, BLUE)])
        textbox(slide, left + 0.55, 1.82, 1.65, 0.4, [(title, 11.5, True, INK)])
        textbox(slide, left + 0.15, 2.35, 2.0, 1.1, [(body, 9.5, False, MUTED)])
    rect(slide, 8.35, 1.7, 4.25, 1.9, NAVY)
    textbox(slide, 8.55, 1.85, 3.9, 0.35, [("结论", 12, True, RGBColor(0x8F, 0xD8, 0xD0))])
    textbox(slide, 8.55, 2.25, 3.9, 1.2, [("名额不属于所有策略的公共前置条件；\n放在 Service 会让审核型“满额不能提交”，与需求冲突。", 9.5, False, WHITE)])
    rect(slide, 0.7, 3.95, 11.9, 2.45, RGBColor(0x10, 0x22, 0x4D))
    textbox(slide, 0.95, 4.1, 11.4, 0.35, [("代码骨架", 11, True, RGBColor(0x8F, 0xD8, 0xD0))])
    textbox(slide, 0.95, 4.5, 11.4, 1.7, [
        ("policy = registry.resolve(activity.policy_type)", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("decision = policy.decide(RegistrationContext(activity, student, approved, now))", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("if not decision.accepted: raise DomainError(decision.reason)", 10.5, False, RGBColor(0xD8, 0xE2, 0xF4)),
        ("# 新增规则：新增实现 + Registry 一行，主流程不改", 9.5, False, RGBColor(0x8F, 0xD8, 0xD0)),
    ])
    textbox(slide, 0.7, 6.6, 11.9, 0.35, [("代价：类比 if/else 多 5—7 个；收益：两类规则差异被隔离，可独立测试。", 10, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "这是设计评审的核心问题：名额检查为什么不在服务层。"

    # 7 观察者
    slide = new_slide(prs, 7, "OBSERVER", "通知失败，不回滚报名")
    image_fit(slide, os.path.join(DIAG, "sequence-direct.png"), 0.45, 1.55, 8.1, 5.0)
    rect(slide, 8.8, 1.65, 3.9, 4.9, WHITE)
    textbox(slide, 9.0, 1.85, 3.5, 0.4, [("事务边界", 14, True, INK)])
    textbox(slide, 9.0, 2.35, 3.5, 3.9, [
        ("1. 报名事务提交", 10.5, True, BLUE),
        ("2. 提交后发布事件", 10, False, MUTED),
        ("3. 每个观察者独立事务", 10.5, True, BLUE),
        ("4. notification_attempt 幂等", 10, False, MUTED),
        ("5. 失败写 FAILED，不回滚", 10.5, True, TEAL),
        ("6. 页面不宣称通知成功", 10, False, MUTED),
        ("初始版本不自动重试；留痕供后续 CR。", 9.5, False, AMBER),
    ])
    slide.notes_slide.notes_text_frame.text = "重点解释通知失败语义与幂等表。"

    # 8 状态与数据
    slide = new_slide(prs, 8, "STATE & DATA", "状态机与数据一致性")
    image_fit(slide, os.path.join(DIAG, "state-registration.png"), 0.6, 1.6, 5.7, 4.8)
    rect(slide, 6.65, 1.65, 6.0, 4.85, WHITE)
    textbox(slide, 6.9, 1.85, 5.5, 0.4, [("SQLite 约束", 14, True, INK)])
    textbox(slide, 6.9, 2.35, 5.5, 3.9, [
        ("• 部分唯一索引：同一学生同一活动最多一条有效报名", 10.5, False, MUTED),
        ("• CHECK：容量 > 0；状态四值；报名方式两值", 10.5, False, MUTED),
        ("• BEGIN IMMEDIATE：报名/审批读名额 + 写记录原子化", 10.5, False, MUTED),
        ("• UPDATE ... WHERE status='PENDING'：防重复批准", 10.5, False, MUTED),
        ("• PRAGMA user_version=1：为 CR 迁移预留", 10.5, False, MUTED),
        ("• 外键开启；通知尝试表 (event_id, channel) 唯一", 10.5, False, MUTED),
    ])
    textbox(slide, 0.7, 6.55, 11.9, 0.35, [("应用层校验 + 数据库约束双保险；不依赖单点检查。", 10, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "状态机与数据库约束；强调并发防护。"

    # 9 演示
    slide = new_slide(prs, 9, "DEMO", "真实运行：报名、审批、取消")
    shots = [
        ("C2-报名后详情.png", "直接报名：已通过"),
        ("C6-审核通过消息.png", "审核通过：站内消息"),
        ("C9-我的报名.png", "取消后：历史保留"),
    ]
    for index, (filename, caption) in enumerate(shots):
        left = 0.7 + index * 4.15
        rect(slide, left, 1.65, 3.9, 4.55, WHITE)
        image_fit(slide, os.path.join(EVID, filename), left + 0.12, 1.8, 3.66, 3.55)
        textbox(slide, left + 0.15, 5.55, 3.6, 0.4, [(caption, 10.5, True, INK)])
    textbox(slide, 0.7, 6.45, 11.9, 0.4, [("截图来自真实 HTTP 响应（非静态拼图）；完整证据见 docs/evidence。", 10, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "现场演示建议：登录学生报名、管理员审批、学生看消息与取消。"

    # 10 测试
    slide = new_slide(prs, 10, "TEST & ACCEPTANCE", "验收：C1—C10 全部通过，107 条测试")
    rows = [["用例", "结果", "用例", "结果"]]
    pairs = [
        ("C1 创建直接活动", "通过", "C6 批准 + 通知", "通过"),
        ("C2 直接报名 + 通知", "通过", "C7 拒绝 + 通知", "通过"),
        ("C3 重复报名拒绝", "通过", "C8 满额批准失败", "通过"),
        ("C4 满额第三人失败", "通过", "C9 取消 + 统计", "通过"),
        ("C5 审核待审核", "通过", "C10 重启持久化", "通过"),
    ]
    rows.extend([list(pair) for pair in pairs])
    add_table(slide, rows, 0.7, 1.65, 7.7, 3.7, [3.1, 0.75, 3.1, 0.75], 9.5)
    rect(slide, 8.75, 1.65, 3.9, 1.7, NAVY)
    textbox(slide, 8.95, 1.8, 3.5, 0.4, [("107", 30, True, WHITE)])
    textbox(slide, 8.95, 2.45, 3.5, 0.4, [("pytest 全部通过", 11, False, RGBColor(0xD8, 0xE2, 0xF4))])
    rect(slide, 8.75, 3.55, 3.9, 3.0, WHITE)
    textbox(slide, 8.95, 3.72, 3.5, 0.35, [("测试层次", 12, True, INK)])
    textbox(slide, 8.95, 4.15, 3.5, 2.2, [
        ("领域单测：策略/注册表", 9.5, False, MUTED),
        ("服务集成：报名/审批/通知", 9.5, False, MUTED),
        ("HTTP：权限/页面/404", 9.5, False, MUTED),
        ("真实验收：C1—C10 + 截图", 9.5, False, MUTED),
        ("持久化：重启后复核", 9.5, False, MUTED),
    ])
    textbox(slide, 0.7, 5.7, 7.8, 0.9, [("修复记录：tzdata 缺失、重复报名竞态、通知失败隔离、验收脚本解析错误；均有测试/重跑证据。", 9.5, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "强调 107 条测试与 C1—C10 真实通过；不虚构通过率。"

    # 11 部署
    slide = new_slide(prs, 11, "DEPLOYMENT", "已部署到公网")
    image_fit(slide, os.path.join(EVID, "public-home.png"), 0.65, 1.6, 5.9, 4.9)
    image_fit(slide, os.path.join(EVID, "线上-管理页.png"), 6.75, 1.6, 5.9, 4.9)
    textbox(slide, 0.7, 6.55, 12.0, 0.35, [("https://campusevent-app.thevibehosting.com  ·  gunicorn 1 worker  ·  SQLite  ·  冷启动 1—3s", 10, False, MUTED)])
    slide.notes_slide.notes_text_frame.text = "公网地址、部署方式、演示账号；强调免费容器会休眠。"

    # 12 下一步
    slide = new_slide(prs, 12, "NEXT", "下一阶段：等 CR，再变更", dark=True)
    textbox(slide, 0.9, 1.55, 11.5, 0.8, [("当前只交付 baseline-v1；不提前实现、不虚构变更数据。", 17, True, WHITE)])
    card(slide, 0.9, 2.65, 3.75, 2.15, "策略扩展", "新增报名规则：新增 Policy 实现 + Registry 一行 + 迁移。", TEAL, False)
    card(slide, 4.85, 2.65, 3.75, 2.15, "通知扩展", "新增渠道：新增 Observer + 注册；事件发布器不改。", BLUE, False)
    card(slide, 8.8, 2.65, 3.75, 2.15, "流程约束", "先影响分析 → 分支实现 → C1—C10 回归 → change-v2。", AMBER, False)
    textbox(slide, 0.9, 5.25, 11.6, 0.9, [
        ("待办：教师 CR 发布 → 变更影响分析 → V2 类图 → 回归测试 → change-v2 标签 → 更新报告/PPT", 12, False, RGBColor(0xD8, 0xE2, 0xF4)),
    ])
    textbox(slide, 0.9, 6.45, 11.6, 0.35, [("谢谢！欢迎现场抽取需求演示。", 13, True, RGBColor(0x8F, 0xD8, 0xD0))])
    slide.notes_slide.notes_text_frame.text = "结束：明确 CR 未发布，变更阶段后续完成；当前可演示初始功能。"

    os.makedirs(DOCS, exist_ok=True)
    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
