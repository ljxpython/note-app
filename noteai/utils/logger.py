#!/usr/bin/env python3
"""
NoteAI 日志系统 - 基于loguru
"""
import os
import sys
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, Optional
from loguru import logger as loguru_logger

class NoteAILogger:
    """NoteAI日志管理器 - 基于loguru"""

    def __init__(self):
        self.setup_logger()

    def setup_logger(self):
        """配置loguru日志器"""
        # 移除默认处理器
        loguru_logger.remove()

        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 控制台处理器（彩色输出，显示更多信息）
        loguru_logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <yellow>{extra}</yellow> - <level>{message}</level>",
            colorize=True
        )

        # 文件处理器（详细日志）
        loguru_logger.add(
            log_dir / "noteai.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention=5,
            compression="zip",
            encoding="utf-8"
        )

        # 错误日志处理器
        loguru_logger.add(
            log_dir / "error.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention=5,
            compression="zip",
            encoding="utf-8"
        )

        # JSON格式日志处理器
        loguru_logger.add(
            log_dir / "noteai.json",
            level="INFO",
            format=self._json_formatter,
            rotation="10 MB",
            retention=5,
            compression="zip",
            encoding="utf-8"
        )

    def _json_formatter(self, record):
        """JSON格式化器"""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"]
        }

        # 添加额外字段
        extra = record.get("extra", {})
        if "user_id" in extra:
            log_entry["user_id"] = extra["user_id"]
        if "request_id" in extra:
            log_entry["request_id"] = extra["request_id"]
        if "ip_address" in extra:
            log_entry["ip_address"] = extra["ip_address"]

        return json.dumps(log_entry, ensure_ascii=False)

    def debug(self, message: str, **kwargs):
        """调试日志"""
        loguru_logger.bind(**kwargs).debug(message)

    def info(self, message: str, **kwargs):
        """信息日志"""
        loguru_logger.bind(**kwargs).info(message)

    def warning(self, message: str, **kwargs):
        """警告日志"""
        loguru_logger.bind(**kwargs).warning(message)

    def error(self, message: str, **kwargs):
        """错误日志"""
        loguru_logger.bind(**kwargs).error(message)

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        loguru_logger.bind(**kwargs).critical(message)
    
    def log_request(self, method: str, path: str, status_code: int,
                   response_time: float, user_id: Optional[str] = None,
                   ip_address: Optional[str] = None):
        """记录HTTP请求日志"""
        message = f"{method} {path} - {status_code} - {response_time:.3f}s"
        loguru_logger.bind(
            user_id=user_id,
            ip_address=ip_address,
            method=method,
            path=path,
            status_code=status_code,
            response_time=response_time
        ).info(message)

    def log_auth(self, action: str, user_id: Optional[str] = None,
                email: Optional[str] = None, success: bool = True,
                ip_address: Optional[str] = None):
        """记录认证日志"""
        status = "SUCCESS" if success else "FAILED"
        message = f"AUTH {action} - {status}"
        if email:
            message += f" - {email}"

        if success:
            loguru_logger.bind(
                user_id=user_id,
                email=email,
                action=action,
                success=success,
                ip_address=ip_address
            ).info(message)
        else:
            loguru_logger.bind(
                user_id=user_id,
                email=email,
                action=action,
                success=success,
                ip_address=ip_address
            ).warning(message)

    def log_ai_usage(self, operation: str, user_id: str, processing_time: float,
                    success: bool = True, error: Optional[str] = None):
        """记录AI使用日志"""
        status = "SUCCESS" if success else "FAILED"
        message = f"AI {operation} - {status} - {processing_time:.3f}s"
        if error:
            message += f" - {error}"

        if success:
            loguru_logger.bind(
                user_id=user_id,
                operation=operation,
                processing_time=processing_time,
                success=success,
                error=error
            ).info(message)
        else:
            loguru_logger.bind(
                user_id=user_id,
                operation=operation,
                processing_time=processing_time,
                success=success,
                error=error
            ).error(message)

    def log_database(self, operation: str, table: str, success: bool = True,
                    error: Optional[str] = None, user_id: Optional[str] = None):
        """记录数据库操作日志"""
        status = "SUCCESS" if success else "FAILED"
        message = f"DB {operation} {table} - {status}"
        if error:
            message += f" - {error}"

        if success:
            loguru_logger.bind(
                operation=operation,
                table=table,
                success=success,
                error=error,
                user_id=user_id
            ).debug(message)
        else:
            loguru_logger.bind(
                operation=operation,
                table=table,
                success=success,
                error=error,
                user_id=user_id
            ).error(message)

# 全局日志实例
logger = NoteAILogger()

# 便捷函数
def get_logger() -> NoteAILogger:
    """获取日志实例"""
    return logger

def log_startup():
    """记录启动日志"""
    logger.info("🚀 NoteAI 服务启动")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"日志目录: {Path('logs').absolute()}")

def log_shutdown():
    """记录关闭日志"""
    logger.info("🛑 NoteAI 服务关闭")

# 异常处理装饰器
def log_exceptions(func):
    """异常日志装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数 {func.__name__} 发生异常: {str(e)}",
                        function=func.__name__, exception=str(e))
            raise
    return wrapper

# 直接暴露loguru的logger供高级使用
loguru_logger = loguru_logger
