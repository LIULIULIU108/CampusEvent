"""领域/应用错误，带 HTTP 语义。"""

from __future__ import annotations


class AppError(Exception):
    status_code = 400
    default_message = "请求无法处理"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(AppError):
    status_code = 400
    default_message = "输入校验失败"

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("；".join(errors.values()) or self.default_message)


class NotFoundError(AppError):
    status_code = 404
    default_message = "资源不存在"


class PermissionDeniedError(AppError):
    status_code = 403
    default_message = "没有权限执行该操作"


class ConflictError(AppError):
    status_code = 409
    default_message = "操作与当前状态冲突"


class DomainError(AppError):
    status_code = 400
    default_message = "业务规则不允许该操作"


class UnsupportedPolicyError(AppError):
    status_code = 500
    default_message = "未支持的报名方式"
