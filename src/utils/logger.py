"""
ロギングユーティリティ

カラフルなコンソール出力を提供するロガー設定

主な機能:
- カラー付きコンソール出力
- ファイル出力
- ログレベル管理
"""

import logging
import sys
from typing import Optional

# カラーコード
COLORS = {
    "DEBUG": "\033[36m",      # シアン
    "INFO": "\033[32m",       # グリーン
    "WARNING": "\033[33m",    # イエロー
    "ERROR": "\033[31m",      # レッド
    "CRITICAL": "\033[35m",   # マゼンタ
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """
    カラー付きログフォーマッター
    """

    def __init__(self, fmt: str, datefmt: Optional[str] = None):
        """
        初期化

        Args:
            fmt: ログフォーマット文字列
            datefmt: 日時フォーマット文字列
        """
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードをフォーマット

        Args:
            record: ログレコード

        Returns:
            str: フォーマットされたログ文字列
        """
        levelName = record.levelname
        if levelName in COLORS:
            record.levelname = f"{COLORS[levelName]}{levelName}{COLORS['RESET']}"
            record.msg = f"{COLORS[levelName]}{record.msg}{COLORS['RESET']}"
        return super().format(record)


def setup_logger(
    name: str = "unitree_go2",
    level: int = logging.DEBUG,
    logFile: Optional[str] = None
) -> logging.Logger:
    """
    ロガーのセットアップ

    Args:
        name: ロガー名
        level: ログレベル
        logFile: ログファイルパス（Noneの場合はファイル出力なし）

    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # コンソールハンドラ
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(level)
    
    consoleFormat = "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s"
    consoleDateFormat = "%H:%M:%S"
    consoleHandler.setFormatter(ColoredFormatter(consoleFormat, consoleDateFormat))
    logger.addHandler(consoleHandler)

    # ファイルハンドラ（オプション）
    if logFile:
        fileHandler = logging.FileHandler(logFile, encoding="utf-8")
        fileHandler.setLevel(level)
        
        fileFormat = "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(funcName)s:%(lineno)d │ %(message)s"
        fileHandler.setFormatter(logging.Formatter(fileFormat))
        logger.addHandler(fileHandler)

    return logger


def get_logger(name: str = "unitree_go2") -> logging.Logger:
    """
    既存のロガーを取得

    Args:
        name: ロガー名

    Returns:
        logging.Logger: ロガー
    """
    return logging.getLogger(name)

