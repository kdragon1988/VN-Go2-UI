"""
コントローラー入力モジュール

ゲームパッド（Xbox互換）の入力処理を担当
"""

from .gamepad import GamepadController, GamepadState, XboxButton, XboxAxis

__all__ = ["GamepadController", "GamepadState", "XboxButton", "XboxAxis"]

