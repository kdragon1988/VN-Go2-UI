"""
スタイルモジュール

QSSスタイルシートの読み込み
"""

import os
from pathlib import Path


def loadStylesheet(name: str = "cyberpunk") -> str:
    """
    スタイルシートを読み込む

    Args:
        name: スタイルシート名（拡張子なし）

    Returns:
        str: スタイルシートの内容
    """
    stylePath = Path(__file__).parent / f"{name}.qss"
    
    if stylePath.exists():
        with open(stylePath, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"[Style] スタイルシートが見つかりません: {stylePath}")
        return ""


__all__ = ["loadStylesheet"]

