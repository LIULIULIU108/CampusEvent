"""SQLite 连接、事务与建库。"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

import click
from flask import current_app, g

SCHEMA_VERSION = 2


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE"],
            isolation_level=None,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        g.db = conn
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@contextmanager
def transaction(*, immediate: bool = True) -> Iterator[sqlite3.Connection]:
    """显式事务。

    连接使用 autocommit（isolation_level=None），因此这里可以明确控制
    BEGIN IMMEDIATE / COMMIT / ROLLBACK，避免隐式事务带来的竞态。
    """

    conn = get_db()
    conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()


def _migrate_to_v2(conn: sqlite3.Connection) -> None:
    """v1 -> v2：重建 student/activity，新增 email_outbox。"""
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        with current_app.open_resource(
            "migrations_v2/002_cr01_cr02.sql"
        ) as fh:
            conn.executescript(fh.read().decode("utf-8"))
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def init_db() -> None:
    conn = get_db()
    with current_app.open_resource("schema_v2.sql") as fh:
        conn.executescript(fh.read().decode("utf-8"))

    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    elif version < SCHEMA_VERSION:
        _migrate_to_v2(conn)
    conn.commit()


@click.command("init-db")
def init_db_command() -> None:
    """创建数据库表（幂等）。"""
    init_db()
    click.echo("数据库已初始化。")


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
