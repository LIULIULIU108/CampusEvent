# app_v2 — CampusEvent change-v2

`app/` 是未修改的 `baseline-v1` 原始代码；本目录是 change-v2 应用，所有变更内容集中在这里，避免改动原代码。

- 入口：`run_v2.py` / `cli_v2.py`；gunicorn：`app_v2:create_app_v2()`
- 数据库：`schema_v2.sql`；v1→v2 迁移：`migrations_v2/002_cr01_cr02.sql`
- CR-01：`domain/policies.py` 中的 `GradeLimitedDirectRegistrationPolicy`、`Student.grade`
- CR-02：`services/email.py`、`services/notifications.py`、`repositories.py` 的 `EmailOutboxRepository`
- 模板/静态：`templates/`、`static/`（本目录内为 v2 版本）
- 测试：`tests_v2/`，配置 `pytest_v2.ini`
- 原 `app/`、`tests/`、`run.py`、`cli.py` 与 `baseline-v1` 完全一致，未修改。
