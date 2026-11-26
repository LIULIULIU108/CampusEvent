# CampusEvent 校园活动报名与管理系统

《软件工程》实验二交付仓库，当前版本：**`change-v2`**（在 `baseline-v1` 上实施 CR-01、CR-02）。

校园管理员发布活动，学生浏览并报名。系统支持**直接报名**、**审核报名**、**年级限定直接报名**三类规则；报名/审核结果通过**站内消息**与 **Mock 邮件**双通道通知；数据持久化在 SQLite。

> **代码组织**：`app/`、`tests/`、`run.py`、`cli.py` 是 `baseline-v1` 原样代码，**未修改**；change-v2 的全部变更在 `app_v2/`、`tests_v2/`、`run_v2.py`、`cli_v2.py`，数据库为 `app_v2/schema_v2.sql`，迁移为 `app_v2/migrations_v2/`。

## 作者与提交信息

| 项 | 内容 |
| --- | --- |
| 班级 | 24计科2班 |
| 学号 | 242806010203 |
| 姓名 | 刘东梁 |
| 项目代号 | CampusEvent |
| 提交目录名 | `24计科2班_242806010203_CampusEvent`（按指导书 1.4 节命名规范） |
| 基线 | `baseline-v1` |
| 变更版 | `change-v2`（CR-01 + CR-02） |
| 交付打包 | `dist/24计科2班_242806010203_CampusEvent.zip` |

## 在线访问地址

- **https://campusevent-app.thevibehosting.com**
- 健康检查：https://campusevent-app.thevibehosting.com/healthz

> 托管在 The Vibe Hosting 免费容器（256 MB）。闲置约 10 分钟会休眠，首次访问可能需要 1—3 秒唤醒；不要添加保活脚本。页脚保留平台要求的链接。

## 变更内容

| 变更 | 实现 |
| --- | --- |
| CR-01 年级限定报名 | `Student.grade`（1—4）；新增 `GRADE_DIRECT` 策略，仅大二/大三可报名；其他年级明确拒绝；原直接/审核行为不变 |
| CR-02 Mock 邮件通知 | 新增 `EmailNotificationObserver` + `MockEmailSender` + `email_outbox`；报名通过、审核通过/拒绝时与站内消息并行记录；失败留痕、不回滚报名；事件级幂等 |
| 数据库迁移 | `PRAGMA user_version 1→2`；重建 student/activity 以增加 grade 与新策略 CHECK；新增 email_outbox |
| 管理端 | 新增“通知记录”页 `/admin/notifications`，查看邮件收件人/主题/状态/错误 |

## 功能一览

| 编号 | 功能 | change-v2 实现 |
| --- | --- | --- |
| P2-F01 | 活动管理 | 管理员创建/编辑/删除活动；名称、类型、时间、地点、容量、报名方式（三种） |
| P2-F02 | 活动查看 | 学生浏览列表、按名称筛选、查看详情 |
| P2-F03 | 报名/取消 | 学生报名、取消；重复有效报名被拒绝并留历史 |
| P2-F04 | 报名策略 | 直接通过 / 审核待定 / 年级限定（仅大二、大三） |
| P2-F05 | 审批 | 管理员批准/拒绝；批准时再次检查名额 |
| P2-F06 | 状态管理 | 待审核/已通过/已拒绝/已取消；状态转换受规则约束 |
| P2-F07 | 通知 | 站内消息 + Mock 邮件；邮件失败留痕，不影响报名 |
| P2-F08 | 统计 | 按活动查看已通过数、待审核数、剩余名额 |

范围外：注册登录、多用户权限体系、候补、真实 SMTP/短信、活动签到、分页、移动端 App、第三方日历、真实支付。

## 技术栈

- Python 3.11+（开发与验证环境 3.12）
- Flask 3.x + Jinja2 服务端渲染
- SQLite（标准库 `sqlite3`，无 ORM）
- pytest（**123 条**自动化测试）
- 前端手写 CSS + 少量原生 JS，无 npm、无 CDN
- 部署：gunicorn + The Vibe Hosting

## 目录结构

```text
.
├─ app/                     # baseline-v1 原始代码，未修改
│  ├─ __init__.py           # 应用工厂、依赖组装、错误处理
│  ├─ config.py             # 配置与环境变量
│  ├─ db.py                 # 连接、BEGIN IMMEDIATE 事务、迁移
│  ├─ schema.sql            # v2 表、CHECK、部分唯一索引
│  ├─ migrations/           # v1 -> v2 迁移脚本
│  ├─ clock.py              # 可注入时钟
│  ├─ domain/               # 实体、枚举、三种策略、事件、通知文案
│  ├─ repositories.py       # 参数化 SQL、email_outbox
│  ├─ services/             # 认证、活动、报名、审批、消息、邮件、统计
│  ├─ web/                  # 学生端、管理端、登录、通知记录
│  ├─ templates/            # 中文页面
│  └─ static/               # style.css / app.js
├─ app_v2/                  # change-v2 应用（所有变更集中在此）
├─ tests/                   # baseline-v1 的 107 条测试（原样保留）
├─ tests_v2/                # change-v2 的 123 条测试（含 CR/迁移）
├─ docs/
│  ├─ 01_需求分析.md
│  ├─ 02_设计说明.md
│  ├─ 03_设计模式决策报告.md
│  ├─ 04_变更影响分析.md
│  ├─ 05_测试报告.md
│  ├─ 06_设计评审记录.md
│  ├─ 07_部署文档.md
│  ├─ 08_实验报告_v2_24计科2班_刘东梁.docx
│  ├─ 09_实验二答辩PPT_v2_24计科2班_刘东梁.pptx
│  ├─ diagrams/             # V1/V2 类图、时序图、PNG
│  └─ evidence/             # baseline-v1 与 change-v2 证据
├─ deploy/                  # 部署脚本（不含密钥）
├─ tools/                   # 验收、证据、报告生成脚本
├─ run.py / run_v2.py       # baseline / change-v2 启动
├─ cli.py / cli_v2.py       # baseline / change-v2 CLI
├─ pytest.ini / pytest_v2.ini
├─ requirements.txt
├─ AI_DEV_LOG.md
└─ README.md
```

## 从零开始运行

### 1. 准备环境

```bash
cd <仓库目录>
python --version          # 需要 3.11 或更高
python -m venv .venv
```

激活虚拟环境：

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> Windows 上 `tzdata` 用于 `Asia/Shanghai` 时区，必须安装。受限网络可先 `pip download` 再离线安装。

### 3. 初始化数据库与演示数据

```bash
python cli_v2.py seed-demo   # 4 名学生（含年级）+ 5 个活动（含年级限定）
```

从 `baseline-v1` 旧数据库升级后，可同步演示年级：

```bash
python cli_v2.py set-demo-grades
```

只写学生、不写活动（验收脚本使用）：

```bash
python cli_v2.py seed-students
```

### 4. 启动

```bash
python run_v2.py
```

打开 <http://127.0.0.1:5000/>。默认监听 `127.0.0.1:5000`，可用环境变量覆盖：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CAMPUSEVENT_HOST` | `127.0.0.1` | 监听地址 |
| `CAMPUSEVENT_PORT` | `5000` | 端口 |
| `CAMPUSEVENT_DEBUG` | `0` | 仅本地开发设为 `1` |
| `CAMPUSEVENT_DATABASE` | `instance/campus_event.db` | SQLite 路径 |
| `CAMPUSEVENT_SECRET_KEY` | 开发默认值 | 部署时必须自定义 |
| `CAMPUSEVENT_ADMIN_PASSWORD` | `admin123` | 演示管理员密码，生产必须修改 |
| `CAMPUSEVENT_EMAIL_FAIL` | `0` | 设为 `1` 可模拟邮件发送失败（演示/测试） |

### 5. 运行测试

```bash
python -m pytest -c pytest_v2.ini
```

预期：**123 passed**。测试使用临时数据库，不污染 `instance/`。

## 演示账号

| 角色 | 账号 | 密码 | 年级 |
| --- | --- | --- | --- |
| 管理员 | `admin` | `admin123` | — |
| 学生 | `2024001` | `123456` | 大二 |
| 学生 | `2024002` | `123456` | 大三 |
| 学生 | `2024003` | `123456` | 大一 |
| 学生 | `2024004` | `123456` | 大四 |

均为虚构课程演示数据，请勿放入真实个人信息。年级限定活动：大二/大三通过，大一/大四被拒绝。

## 设计与模式

- **Strategy**：`RegistrationPolicy` + 直接/审核/年级限定三种实现，`PolicyRegistry` 选择策略；`RegistrationService` 主流程未因 CR-01 修改。
- **Observer**：业务事务提交后发布 `DomainEvent`；站内消息与 Mock 邮件是两个观察者；`EmailNotificationObserver.supports()` 只订阅通过/拒绝事件。
- **发件箱/幂等**：`email_outbox.event_id` 唯一；`notification_attempt(event_id, channel)` 记录每个渠道状态；邮件失败 `on_error` 写 FAILED，不回滚报名。
- **Repository**：SQL 隔离在 `repositories.py`；邮件记录独立仓储。
- 名额判断由 `CapacityChecker` 统一计算，策略/审批服务复用。

详见 [docs/02_设计说明.md](docs/02_设计说明.md)、[docs/03_设计模式决策报告.md](docs/03_设计模式决策报告.md) 与 [docs/04_变更影响分析.md](docs/04_变更影响分析.md)。

## 验收结果

- 初始验收 **C1—C10：10/10 通过**（change-v2 真实 HTTP 回归）。
- 变更验收 **CR1-01—CR1-05、CR2-01—CR2-05、MIG-01：11/11 通过**。
- pytest：**123 passed**。
- 基线证据：`docs/evidence/`；变更证据：`docs/evidence/change-v2/`（`cr-log.json` + `regression/acceptance-log.json` + PNG）。
- 测试环境、缺陷修复与已知限制见 [docs/05_测试报告.md](docs/05_测试报告.md)。

复现验收：

```bash
python cli_v2.py seed-students
python run_v2.py
# 另一终端
python tools/acceptance_run.py
# 停止并重新启动服务后
python tools/acceptance_run.py --verify
```

## 部署

- 公网地址：https://campusevent-app.thevibehosting.com
- 平台：The Vibe Hosting（免费容器，Ubuntu + 自动 HTTPS 子域）
- 运行方式：gunicorn 单 worker、2 线程，监听容器 80 端口
- 数据库：`/root/myapp/instance/campus_event.db`
- 健康检查：`/healthz`
- v1→v2 迁移在应用启动时自动执行；旧演示库升级后运行 `python cli_v2.py set-demo-grades`
- 邮件记录页：`/admin/notifications`（管理员）

完整步骤、环境变量、备份与故障处理见 [docs/07_部署文档.md](docs/07_部署文档.md)。`deploy/` 下脚本不含密钥；`.thevibehosting.json`、`.thevibehosting_key` 仅保存在本地并已加入 `.gitignore`。

## Git 标签与版本

| 标签 | 含义 |
| --- | --- |
| `baseline-v1` | 初始版本：两类报名 + 站内消息；107 条测试；C1—C10 证据 |
| `change-v2` | CR-01 年级限定 + CR-02 Mock 邮件；123 条测试；C1—C10 回归 + CR 证据 |

## 文档索引

- [01 需求分析](docs/01_需求分析.md)
- [02 设计说明](docs/02_设计说明.md)
- [03 设计模式决策报告](docs/03_设计模式决策报告.md)
- [04 变更影响分析（CR-01/CR-02）](docs/04_变更影响分析.md)
- [05 测试报告](docs/05_测试报告.md)
- [06 设计评审记录（待评审同学签字）](docs/06_设计评审记录.md)
- [07 部署文档](docs/07_部署文档.md)
- [08 实验报告 DOCX（change-v2）](docs/08_实验报告_v2_24计科2班_刘东梁.docx)
- [09 答辩 PPT（change-v2）](docs/09_实验二答辩PPT_v2_24计科2班_刘东梁.pptx)
- [AI 协作记录](AI_DEV_LOG.md)

## 已知限制

- 演示版没有 CSRF token；管理员使用固定演示密码；公网只放虚构数据。生产化前需补 CSRF、改密、限流与审计。
- SQLite 单写者；本项目通过 `BEGIN IMMEDIATE` 与部分唯一索引保证一致性，但不适合高并发。
- 通知是 best-effort：业务事务提交后发送；失败写入 `notification_attempt` / `email_outbox`，不自动重试。
- CR-02 使用 `MockEmailSender`，不连接真实 SMTP；收件人为 `学号@mock.campus.local`，仅用于课程演示。
- 年级限定规则固定为大二、大三（grade 2/3）；未做按活动配置年级范围。
- 活动列表不分页；活动量很大时性能下降（课程规模 200 条以内）。

## AI 协作记录

关键提示词、设计取舍、发现的问题与人工判断见 [AI_DEV_LOG.md](AI_DEV_LOG.md)。AI 生成内容均经测试/运行验证，不以 AI 声称“完成”替代验收。
