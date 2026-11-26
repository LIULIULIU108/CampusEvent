# AI_DEV_LOG — CampusEvent baseline-v1 + change-v2

> 记录关键 AI 协作事件，不粘贴全部对话。AI 生成内容均经运行/测试验证；不以 AI 声称“完成”替代验收。
>
> 前 9 条为 `baseline-v1`；后 8 条为 `change-v2`（CR-01 年级限定、CR-02 Mock 邮件、v1→v2 迁移、原代码不动的目录重构）。

| 时间/版本 | 任务与发给 AI 的关键指令 | AI 产出与问题 | 学生判断/验证 |
| --- | --- | --- | --- |
| 2026-11-25 / `0a65452` | 阅读实验指导书附录 B，提炼 CampusEvent 的角色、P2-F01—F08、C1—C10 与范围边界；先出需求/用例再写代码。 | 生成需求分析、用例说明、追踪矩阵；提出可考虑候补/邮件等扩展。 | 明确 CR 未发布，拒绝提前实现候补/邮件；只保留两类报名与站内通知；设计评审签名待同学补签。 |
| 2026-11-25 / `0a65452` | 根据需求画初版 UML 类图、组件图、状态机与 3 张时序图，说明策略/观察者职责。 | 生成 PlantUML 源文件与中文 PNG；类图初版关系较多、布局偏宽。 | 保留类图用于设计评审；确认“设计先于实现”的提交顺序；类图在文档中可读。 |
| 2026-11-25 / `0c6b1ff` | 设计报名规则：直接/审核两类，说明名额检查应放服务还是策略。 | AI 初稿倾向把名额检查放在 `RegistrationService` 公共前置条件。 | 拒绝该方案：审核型提交时不占名额，名额应在批准时检查；改为策略决策 + `CapacityChecker` 共享口径，服务只做公共前置条件。 |
| 2026-11-25 / `0c6b1ff` | 解耦报名与站内通知，处理通知失败与重复通知。 | AI 初稿在服务内直接写消息；提出用事件/观察者。 | 采用“事务提交后发布事件 + 每观察者隔离 + `notification_attempt` 幂等/留痕”；明确通知失败不回滚报名，初始版本不自动重试。 |
| 2026-11-25 / `0c6b1ff` | 设计 SQLite 表、约束与并发策略。 | AI 生成基本表结构；对重复报名提出应用层检查。 | 追加部分唯一索引 `ux_registration_active` 与 `BEGIN IMMEDIATE`，把数据库约束作为最后防线；保留 `user_version=1` 供后续 CR 迁移。 |
| 2026-11-25 / `0c6b1ff` | 编写 pytest，覆盖 C1—C10 与边界；固定时钟避免跨日随机失败。 | 首轮出现测试夹具签名遗漏、系统临时目录权限错误；先修工具/夹具再跑业务。 | 统一 `make_activity(app, ...)` 调用、固定时钟、工作区临时目录；最终 **107 passed**。 |
| 2026-11-25 / `0c6b1ff` | 通过真实 HTTP 执行 C1—C10 并保存证据。 | 验收脚本把顶部 flash 中的活动名当成表格行，导致后续用例操作错误活动。 | 发现后改为从 `<td class="title-cell">` 匹配；清空数据库重跑，C1—C10 全部通过；如实记录为测试工具缺陷。 |
| 2026-11-25 / 部署 | 部署到 The Vibe Hosting 新子域，不覆盖实验一 StudyTask。 | 创建 `campusevent-app.thevibehosting.com`；远端安装依赖、写 run.sh、gunicorn 启动；公网健康检查与管理员登录成功。 | 部署前用 `hostname` 核实目标主机；公网只放虚构演示数据；保留免费计划页脚；密钥仅本地保存。 |
| 2026-11-25 / 报告 | 生成 5—8 页 DOCX 报告与答辩 PPT，变更章节留待 CR。 | 生成报告/PPT 初稿，引用真实 C1—C10 证据与公网地址。 | 明确写“CR 未发布、变更阶段待补充”，不填虚构变更指标；评审签名仍待外部完成。 |
| 2026-11-26 / CR 分析 | 阅读教师材料 CR-01/CR-02，先写影响分析：受影响类、迁移、测试、风险。 | 生成 `docs/04_变更影响分析.md` 与 V2 类图/邮件时序图；估算新增 7 类、核心服务 0 修改。 | 确认从 `baseline-v1` 建 `change-v2` 分支；先设计后改代码；不修改基线标签。 |
| 2026-11-26 / CR-01 | 年级限定报名：Student.grade + 仅大二/大三；不修改 RegistrationService 主流程。 | AI 提出新增 `GradeLimitedDirectRegistrationPolicy`，复用 `CapacityChecker`；更新表单/标签/seed。 | 采用独立策略；年级 1/4 明确拒绝；C1—C10 原行为不变。 |
| 2026-11-26 / CR-02 | 站内消息之外增加 Mock 邮件；失败留痕、不重复、不回滚报名。 | AI 提出 `EmailNotificationObserver` + `MockEmailSender` + `email_outbox`；`EventPublisher` 增加 supports/on_error。 | 待审核不发邮件；失败写 FAILED 与错误；同一 event_id 只发一次；邮件不接真实 SMTP。 |
| 2026-11-26 / 迁移 | v1→v2：grade、策略 CHECK、email_outbox，旧数据必须保留。 | AI 初稿尝试直接 ALTER，SQLite 不支持改 CHECK。 | 改为事务内重建 student/activity、复制数据、修正 sqlite_sequence、外键检查；迁移测试通过。 |
| 2026-11-26 / 目录 | 用户要求“原先代码不能动，后更改内容用 v2 命名区分”。 | 将变更从 `app/` 抽离为 `app_v2/`、`tests_v2/`、`run_v2.py`、`cli_v2.py`；原 `app/tests/cli/run` 恢复并保持 baseline 原样。 | 校验 `git diff baseline-v1 -- app tests cli.py run.py` 为空；baseline 107、v2 123 两套测试分别通过。 |
| 2026-11-26 / 测试 | 补 CR1-01—05、CR2-01—05、MIG-01；C1—C10 回归。 | AI 生成 16 条新测试；首轮测试目录编码/导入损坏，改用 UTF-8 Python 重写。 | v2 123 passed；C1—C10 真实 HTTP 10/10；CR 11/11；迁移测试通过。 |
| 2026-11-26 / 部署 | 部署 change-v2 到同一公网地址；迁移 v1 数据库；验证年级/邮件。 | 部署后旧 baseline gunicorn 未退出，读取 v2 `GRADE_DIRECT` 导致 500；AI 在 run.sh 中改为显式 `pkill gunicorn`。 | 重启后公网登录/管理页/年级拒绝/邮件记录全部通过；截图保存 change-v2/public。 |
| 2026-11-26 / 报告 | 生成 change-v2 报告与 PPT，保留 baseline 版本，文件名含 v2。 | 生成 5 页 DOCX 与 14 页 PPT；引用变更证据、迁移、指标；文件为 `08_..._v2...`、`09_..._v2...`。 | 报告页数 5（在 5—8 内）；PPT 14 页；明确原代码未改、变更在 app_v2。 |

## 补充说明

- 关键 AI 交互按上表 17 条计（baseline 9 + change-v2 8）；这是代表性记录，不是全部对话轮次。
- 学生/用户已确认：身份信息、部署到 Vibe Hosting、CR-01/CR-02 变更、原代码不动并用 v2 命名区分。
- 设计评审记录：`docs/06_设计评审记录.md` 仍为**待同班同学评审签字**状态，未代签。
- 变更阶段材料：`docs/04_变更影响分析.md`（实际分析），`change-v2` 标签待创建；`app_v2/` 为唯一变更实现。
