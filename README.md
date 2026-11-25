# CampusEvent 校园活动报名与管理系统

《软件工程》实验二初始版本（`baseline-v1`）交付仓库。

校园管理员发布活动，学生浏览并报名。初始版本支持**直接报名**与**审核报名**两类规则，报名/审核结果通过**站内消息**通知；数据持久化在 SQLite。

> **范围说明**：教师需求变更单（CR）尚未发布，本仓库只完成初始版本（baseline-v1）。变更版类图、变更影响分析与 `change-v2` 回归**尚未实施**，模板见 [docs/04_变更影响分析_模板.md](docs/04_变更影响分析_模板.md)。本项目不伪造变更后的数据。

## 作者与提交信息

| 项 | 内容 |
| --- | --- |
| 班级 | 24计科2班 |
| 学号 | 242806010203 |
| 姓名 | 刘东梁 |
| 项目代号 | CampusEvent |
| 提交目录名 | `24计科2班_242806010203_CampusEvent`（按指导书 1.4 节命名规范） |
| 版本基线 | `baseline-v1` |
| 交付打包 | `dist/24计科2班_242806010203_CampusEvent.zip` |

## 在线访问地址

- **https://campusevent-app.thevibehosting.com**
- 健康检查：https://campusevent-app.thevibehosting.com/healthz

> 托管在 The Vibe Hosting 免费容器（256 MB）。闲置约 10 分钟会休眠，首次访问可能需要 1—3 秒唤醒；不要添加保活脚本。页脚保留平台要求的链接。

## 功能一览

| 编号 | 功能 | 初始版本实现 |
| --- | --- | --- |
| P2-F01 | 活动管理 | 管理员创建/编辑/删除活动；名称、类型、时间、地点、容量、报名方式 |
| P2-F02 | 活动查看 | 学生浏览列表、按名称筛选、查看详情 |
| P2-F03 | 报名/取消 | 学生报名、取消；重复有效报名被拒绝并留历史 |
| P2-F04 | 报名策略 | 直接报名自动通过；审核型进入待审核 |
| P2-F05 | 审批 | 管理员批准/拒绝；批准时再次检查名额 |
| P2-F06 | 状态管理 | 待审核/已通过/已拒绝/已取消；状态转换受规则约束 |
| P2-F07 | 站内通知 | 报名结果、审核结果写入消息列表，支持已读 |
| P2-F08 | 统计 | 按活动查看已通过数、待审核数、剩余名额 |

范围外：注册登录、多用户权限体系、候补、邮件/短信、活动签到、分页、移动端 App、第三方日历、真实支付。

## 技术栈

- Python 3.11+（开发与验证环境 3.12）
- Flask 3.x + Jinja2 服务端渲染
- SQLite（标准库 `sqlite3`，无 ORM）
- pytest（107 条自动化测试）
- 前端手写 CSS + 少量原生 JS，无 npm、无 CDN
- 部署：gunicorn + The Vibe Hosting

## 目录结构

```text
.
├─ app/
│  ├─ __init__.py           # 应用工厂、依赖组装、错误处理
│  ├─ config.py             # 配置与环境变量
│  ├─ db.py                 # 连接、BEGIN IMMEDIATE 事务、建库
│  ├─ schema.sql            # 表、CHECK、部分唯一索引
│  ├─ clock.py              # 可注入时钟
│  ├─ domain/               # 实体、枚举、策略、事件、通知文案
│  ├─ repositories.py       # 参数化 SQL 与行映射
│  ├─ services/             # 认证、活动、报名、审批、消息、统计
│  ├─ web/                  # 学生端、管理端、登录
│  ├─ templates/            # 中文页面
│  └─ static/               # style.css / app.js
├─ tests/                   # 107 条 pytest 测试
├─ docs/
│  ├─ 01_需求分析.md
│  ├─ 02_设计说明.md
│  ├─ 03_设计模式决策报告.md
│  ├─ 04_变更影响分析_模板.md
│  ├─ 05_测试报告.md
│  ├─ 06_设计评审记录.md
│  ├─ 07_部署文档.md
│  ├─ 08_实验报告_24计科2班_刘东梁.docx
│  ├─ 09_实验二答辩PPT_24计科2班_刘东梁.pptx
│  ├─ diagrams/             # PlantUML 源文件与 PNG
│  └─ evidence/             # C1—C10 真实响应、截图与 JSON
├─ deploy/                  # 部署脚本（不含密钥）
├─ tools/                   # 验收、证据、报告生成脚本
├─ run.py                   # 本地启动
├─ cli.py                   # init-db / seed-students / seed-demo
├─ requirements.txt
├─ pytest.ini
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
python cli.py seed-demo      # 3 名学生 + 4 个活动（仅空库写入）
```

只写学生、不写活动（验收脚本使用）：

```bash
python cli.py seed-students
```

### 4. 启动

```bash
python run.py
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

### 5. 运行测试

```bash
python -m pytest
```

预期：`107 passed`。测试使用临时数据库，不污染 `instance/`。

## 演示账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 学生 | `2024001` | `123456` |
| 学生 | `2024002` | `123456` |
| 学生 | `2024003` | `123456` |

均为虚构课程演示数据，请勿放入真实个人信息。

## 设计与模式

- **Strategy**：`RegistrationPolicy` + `DirectRegistrationPolicy` / `ApprovalRegistrationPolicy`，`PolicyRegistry` 选择策略。
- **Observer**：业务事务提交后发布 `DomainEvent`，`InAppNotificationObserver` 写站内消息；失败写入 `notification_attempt`。
- **Repository**：SQL 隔离在 `repositories.py`。
- 名额判断由 `CapacityChecker` 统一计算，策略/审批服务复用；`RegistrationService` 不硬编码报名类型分支。

详见 [docs/02_设计说明.md](docs/02_设计说明.md) 与 [docs/03_设计模式决策报告.md](docs/03_设计模式决策报告.md)。

## 验收结果

- 初始验收用例 **C1—C10：10/10 通过**（真实 HTTP 响应，非静态截图）。
- pytest：**107 passed**。
- 证据索引：`docs/evidence/png/`；机器可读记录：`docs/evidence/acceptance-log.json`。
- 测试环境、用例表、缺陷修复与已知限制见 [docs/05_测试报告.md](docs/05_测试报告.md)。

复现验收：

```bash
python cli.py seed-students
python run.py
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

完整步骤、环境变量、备份与故障处理见 [docs/07_部署文档.md](docs/07_部署文档.md)。`deploy/` 下脚本不含密钥；`.thevibehosting.json`、`.thevibehosting_key` 仅保存在本地并已加入 `.gitignore`。

## Git 标签与版本

| 标签 | 含义 |
| --- | --- |
| `baseline-v1` | 初始版本：设计、实现、107 条测试、C1—C10 证据、公网部署 |
| `change-v2` | **待教师 CR 发布后**创建，不在本次范围 |

## 文档索引

- [01 需求分析](docs/01_需求分析.md)
- [02 设计说明](docs/02_设计说明.md)
- [03 设计模式决策报告](docs/03_设计模式决策报告.md)
- [04 变更影响分析模板（待 CR）](docs/04_变更影响分析_模板.md)
- [05 测试报告](docs/05_测试报告.md)
- [06 设计评审记录（待评审同学签字）](docs/06_设计评审记录.md)
- [07 部署文档](docs/07_部署文档.md)
- [08 实验报告 DOCX](docs/08_实验报告_24计科2班_刘东梁.docx)
- [09 答辩 PPT](docs/09_实验二答辩PPT_24计科2班_刘东梁.pptx)
- [AI 协作记录](AI_DEV_LOG.md)

## 已知限制

- 演示版没有 CSRF token；管理员使用固定演示密码；公网只放虚构数据。生产化前需补 CSRF、改密、限流与审计。
- SQLite 单写者；本项目通过 `BEGIN IMMEDIATE` 与部分唯一索引保证一致性，但不适合高并发。
- 通知是 best-effort：业务事务提交后发送；失败写入 `notification_attempt`，初始版本不自动重试。
- 活动列表不分页；活动量很大时性能下降（课程规模 200 条以内）。
- **变更阶段尚未实施**：没有 `change-v2`、变更版类图、变更影响分析或回归结果；等待教师 CR。

## AI 协作记录

关键提示词、设计取舍、发现的问题与人工判断见 [AI_DEV_LOG.md](AI_DEV_LOG.md)。AI 生成内容均经测试/运行验证，不以 AI 声称“完成”替代验收。
