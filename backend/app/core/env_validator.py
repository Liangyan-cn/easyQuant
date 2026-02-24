import os
import sys
from typing import List, Optional
from urllib.parse import urlparse


class EnvValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        lines = [
            "",
            "=" * 60,
            "❌ 环境变量验证失败",
            "=" * 60,
            "",
        ]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"  {i}. {error}")
        lines.extend([
            "",
            "-" * 60,
            "💡 解决方案:",
            "  1. 复制 .env.example 为 .env",
            "  2. 根据上述错误修改 .env 中的配置",
            "  3. 重新启动服务",
            "",
            "  示例: cp .env.example .env && vim .env",
            "=" * 60,
            "",
        ])
        return "\n".join(lines)


REQUIRED_ENV_VARS = [
    {
        "name": "DATABASE_URL",
        "description": "PostgreSQL 数据库连接字符串",
        "example": "postgresql+asyncpg://user:password@localhost:5432/easyquant",
        "validator": lambda v: v.startswith(("postgresql", "sqlite")),
        "error_hint": "必须是有效的 PostgreSQL 或 SQLite 连接字符串",
    },
    {
        "name": "SECRET_KEY",
        "description": "JWT 签名密钥",
        "example": "your-super-secret-key-change-in-production",
        "validator": lambda v: len(v) >= 16 and v != "your-secret-key-change-in-production",
        "error_hint": "必须至少 16 个字符，且不能使用默认值",
        "required_in_production": True,
    },
]

OPTIONAL_ENV_VARS = [
    {
        "name": "REDIS_URL",
        "description": "Redis 连接字符串",
        "example": "redis://localhost:6379/0",
        "default": "redis://localhost:6379/0",
    },
    {
        "name": "CORS_ORIGINS",
        "description": "允许的跨域来源",
        "example": '["http://localhost:3000"]',
        "default": '["http://localhost:3000", "http://localhost:8080"]',
    },
    {
        "name": "DEBUG",
        "description": "调试模式",
        "example": "false",
        "default": "false",
    },
]


def validate_database_url(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            return "缺少数据库协议 (如 postgresql+asyncpg://)"
        if "postgresql" in parsed.scheme and not parsed.hostname:
            return "缺少数据库主机地址"
        return None
    except Exception as e:
        return f"URL 解析失败: {e}"


def validate_env_vars(is_production: bool = False) -> None:
    errors: List[str] = []
    
    for var_config in REQUIRED_ENV_VARS:
        name = var_config["name"]
        value = os.getenv(name)
        
        if not value:
            errors.append(
                f"{name}: 未设置\n"
                f"     说明: {var_config['description']}\n"
                f"     示例: {name}={var_config['example']}"
            )
            continue
        
        validator = var_config.get("validator")
        if validator and not validator(value):
            if var_config.get("required_in_production") and not is_production:
                continue
            errors.append(
                f"{name}: {var_config.get('error_hint', '值无效')}\n"
                f"     当前值: {value[:20]}{'...' if len(value) > 20 else ''}\n"
                f"     示例: {name}={var_config['example']}"
            )
    
    if name := "DATABASE_URL":
        value = os.getenv(name)
        if value:
            db_error = validate_database_url(value)
            if db_error:
                errors.append(f"{name}: {db_error}")
    
    if errors:
        raise EnvValidationError(errors)


def print_env_status() -> None:
    print("\n" + "=" * 60)
    print("📋 环境变量状态")
    print("=" * 60)
    
    print("\n必需变量:")
    for var_config in REQUIRED_ENV_VARS:
        name = var_config["name"]
        value = os.getenv(name)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"  ✅ {name}: {masked}")
        else:
            print(f"  ❌ {name}: 未设置")
    
    print("\n可选变量:")
    for var_config in OPTIONAL_ENV_VARS:
        name = var_config["name"]
        value = os.getenv(name, var_config.get("default"))
        if value:
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"  ✅ {name}: {masked}")
        else:
            print(f"  ⚪ {name}: 使用默认值")
    
    print("=" * 60 + "\n")


def startup_validation(verbose: bool = False) -> None:
    is_production = os.getenv("DEBUG", "false").lower() != "true"
    
    try:
        validate_env_vars(is_production=is_production)
        if verbose:
            print_env_status()
    except EnvValidationError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
