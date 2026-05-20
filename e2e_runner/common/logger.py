"""日志工具模块"""
import logging
import os
from datetime import datetime
from pathlib import Path


class Logger:
    """日志工具类（单例模式）"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        self._logger = logging.getLogger("e2e_runner")
        self._logger.setLevel(logging.DEBUG)

        if not self._logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            self._logger.addHandler(console_handler)

    def _get_log_dir(self):
        """获取日志目录"""
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _get_file_handler(self):
        """获取文件处理器（按天分割）"""
        log_dir = self._get_log_dir()
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"e2e_test_{today}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        return file_handler

    def _ensure_file_handler(self):
        """确保文件处理器已添加"""
        log_dir = self._get_log_dir()
        today = datetime.now().strftime("%Y-%m-%d")

        for handler in self._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler_base = os.path.basename(handler.baseFilename)
                if handler_base == f"e2e_test_{today}.log":
                    return

        self._logger.addHandler(self._get_file_handler())

    def debug(self, msg):
        self._ensure_file_handler()
        self._logger.debug(msg)

    def info(self, msg):
        self._ensure_file_handler()
        self._logger.info(msg)

    def warning(self, msg):
        self._ensure_file_handler()
        self._logger.warning(msg)

    def error(self, msg):
        self._ensure_file_handler()
        self._logger.error(msg)

    def critical(self, msg):
        self._ensure_file_handler()
        self._logger.critical(msg)


logs = Logger()
