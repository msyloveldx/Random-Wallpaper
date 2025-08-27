import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).parent / "logs"


def ensure_logs_dir():
    """确保日志目录存在。"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # 最多降级到当前目录
        pass


def get_logger(logger_name):
    """获取带有控制台与滚动文件处理器的日志记录器。

    - 控制台级别: INFO
    - 文件级别: INFO，单文件 5MB，最多保留 5 个备份
    """
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # 文件（滚动）
    try:
        ensure_logs_dir()
        log_file = LOG_DIR / f"{logger_name}.log"
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except Exception:
        # 若文件处理器创建失败，不影响主流程
        pass

    return logger


