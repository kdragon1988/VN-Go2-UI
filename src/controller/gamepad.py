"""
ゲームパッド入力処理モジュール

Xbox互換コントローラーからの入力を処理

主な機能:
- Bluetooth/有線Xboxコントローラーの検出
- ボタン・スティック入力の読み取り
- デッドゾーン処理
- 入力イベントのコールバック

制限事項:
- macOSでのXbox互換コントローラーのみサポート
- pygameライブラリが必要
- macOSではメインスレッドでのみイベント処理可能
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any
from enum import IntEnum


class XboxButton(IntEnum):
    """
    Xboxコントローラーのボタンマッピング

    macOS + pygameでの標準的なマッピング
    """
    A = 0           # Aボタン（下）
    B = 1           # Bボタン（右）
    X = 2           # Xボタン（左）
    Y = 3           # Yボタン（上）
    LB = 4          # 左バンパー
    RB = 5          # 右バンパー
    BACK = 6        # Backボタン（Viewボタン）
    START = 7       # Startボタン（Menuボタン）
    GUIDE = 8       # Xboxボタン（ガイド）
    L_STICK = 9     # 左スティック押し込み
    R_STICK = 10    # 右スティック押し込み


class XboxAxis(IntEnum):
    """
    Xboxコントローラーの軸マッピング
    """
    LEFT_X = 0      # 左スティック X軸
    LEFT_Y = 1      # 左スティック Y軸
    RIGHT_X = 2     # 右スティック X軸（または3）
    RIGHT_Y = 3     # 右スティック Y軸（または4）
    LT = 4          # 左トリガー（または2）
    RT = 5          # 右トリガー（または5）


@dataclass
class GamepadState:
    """
    ゲームパッドの現在状態

    Attributes:
        connected: 接続状態
        leftStickX: 左スティックX軸 (-1.0 ~ 1.0)
        leftStickY: 左スティックY軸 (-1.0 ~ 1.0)
        rightStickX: 右スティックX軸 (-1.0 ~ 1.0)
        rightStickY: 右スティックY軸 (-1.0 ~ 1.0)
        leftTrigger: 左トリガー (0.0 ~ 1.0)
        rightTrigger: 右トリガー (0.0 ~ 1.0)
        buttons: 各ボタンの押下状態
        dpadX: D-Pad X軸 (-1, 0, 1)
        dpadY: D-Pad Y軸 (-1, 0, 1)
    """
    connected: bool = False
    controllerName: str = ""
    
    # スティック
    leftStickX: float = 0.0
    leftStickY: float = 0.0
    rightStickX: float = 0.0
    rightStickY: float = 0.0
    
    # トリガー
    leftTrigger: float = 0.0
    rightTrigger: float = 0.0
    
    # ボタン状態（キー: ボタン番号, 値: 押下状態）
    buttons: Dict[int, bool] = field(default_factory=dict)
    
    # D-Pad
    dpadX: int = 0
    dpadY: int = 0
    
    def isButtonPressed(self, button: XboxButton) -> bool:
        """
        指定ボタンが押されているかチェック

        Args:
            button: チェックするボタン

        Returns:
            bool: 押されている場合True
        """
        return self.buttons.get(button, False)

    def copy(self) -> "GamepadState":
        """状態のコピーを作成"""
        import copy
        return copy.deepcopy(self)


class GamepadController:
    """
    ゲームパッドコントローラー

    Xbox互換コントローラーからの入力を処理し、
    コールバック経由でアプリケーションに通知

    Note:
        macOSではpygameのイベント処理はメインスレッドでのみ実行可能。
        poll()メソッドをQTimerなどでメインスレッドから呼び出すこと。

    Attributes:
        state: 現在のゲームパッド状態
        deadzone: スティックのデッドゾーン閾値
    """

    def __init__(self, deadzone: float = 0.15):
        """
        ゲームパッドコントローラーの初期化

        Args:
            deadzone: スティックのデッドゾーン閾値 (0.0 ~ 1.0)
        """
        self.state = GamepadState()
        self.deadzone = deadzone
        
        # pygame関連
        self._joystick = None
        self._pygameInitialized = False
        
        # コールバック
        self._stateCallback: Optional[Callable[[GamepadState], None]] = None
        self._buttonCallback: Optional[Callable[[XboxButton, bool], None]] = None
        
        # 前回のボタン状態（変化検出用）
        self._prevButtons: Dict[int, bool] = {}

    def initialize(self) -> bool:
        """
        pygameとジョイスティックの初期化

        Returns:
            bool: 初期化成功時True
        """
        try:
            import pygame
            
            # pygame初期化（ジョイスティックのみ）
            pygame.init()
            pygame.joystick.init()
            
            self._pygameInitialized = True
            
            # コントローラーの検出
            numJoysticks = pygame.joystick.get_count()
            print(f"[GamepadController] 検出されたコントローラー数: {numJoysticks}")
            
            if numJoysticks > 0:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
                
                self.state.connected = True
                self.state.controllerName = self._joystick.get_name()
                print(f"[GamepadController] 接続: {self.state.controllerName}")
                print(f"  - ボタン数: {self._joystick.get_numbuttons()}")
                print(f"  - 軸数: {self._joystick.get_numaxes()}")
                print(f"  - ハット数: {self._joystick.get_numhats()}")
            else:
                self.state.connected = False
                print("[GamepadController] コントローラーが見つかりません")
            
            return True
            
        except ImportError:
            print("[GamepadController] pygameがインストールされていません")
            return False
        except Exception as e:
            print(f"[GamepadController] 初期化エラー: {e}")
            return False

    def start(self) -> None:
        """
        ゲームパッドの使用を開始（初期化のみ）
        
        Note:
            実際のポーリングはpoll()をメインスレッドから呼び出すこと
        """
        if not self._pygameInitialized:
            if not self.initialize():
                return
        
        print("[GamepadController] 初期化完了（poll()をメインスレッドから呼び出してください）")

    def stop(self) -> None:
        """
        ゲームパッドの使用を停止
        """
        if self._pygameInitialized:
            import pygame
            pygame.joystick.quit()
            pygame.quit()
            self._pygameInitialized = False
        
        print("[GamepadController] 停止")

    def poll(self) -> None:
        """
        入力をポーリング（メインスレッドから呼び出すこと）
        
        この関数をQTimerなどでメインスレッドから定期的に呼び出す
        """
        if not self._pygameInitialized:
            return
        
        try:
            import pygame
            
            # pygameイベント処理（メインスレッドで実行必須）
            pygame.event.pump()
            
            # コントローラー接続チェック
            numJoysticks = pygame.joystick.get_count()
            
            if numJoysticks == 0 and self.state.connected:
                # 切断検出
                self.state.connected = False
                self._joystick = None
                print("[GamepadController] コントローラーが切断されました")
                
            elif numJoysticks > 0 and not self.state.connected:
                # 再接続検出
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
                self.state.connected = True
                self.state.controllerName = self._joystick.get_name()
                print(f"[GamepadController] コントローラーが再接続されました: {self.state.controllerName}")
            
            if self._joystick and self.state.connected:
                self._updateState()
            
            # コールバック呼び出し
            if self._stateCallback:
                self._stateCallback(self.state.copy())
                
        except Exception as e:
            print(f"[GamepadController] ポーリングエラー: {e}")

    def setStateCallback(self, callback: Callable[[GamepadState], None]) -> None:
        """
        状態更新コールバックを設定

        Args:
            callback: ゲームパッド状態を受け取るコールバック関数
        """
        self._stateCallback = callback

    def setButtonCallback(self, callback: Callable[[XboxButton, bool], None]) -> None:
        """
        ボタンイベントコールバックを設定

        Args:
            callback: (ボタン, 押下状態) を受け取るコールバック関数
        """
        self._buttonCallback = callback

    def _updateState(self) -> None:
        """
        ジョイスティックから現在の状態を読み取り
        """
        if not self._joystick:
            return
        
        numAxes = self._joystick.get_numaxes()
        numButtons = self._joystick.get_numbuttons()
        numHats = self._joystick.get_numhats()
        
        # 軸の読み取り
        if numAxes >= 2:
            self.state.leftStickX = self._applyDeadzone(
                self._joystick.get_axis(XboxAxis.LEFT_X)
            )
            self.state.leftStickY = self._applyDeadzone(
                self._joystick.get_axis(XboxAxis.LEFT_Y)
            )
        
        if numAxes >= 4:
            # macOSでは軸のマッピングが異なる場合がある
            self.state.rightStickX = self._applyDeadzone(
                self._joystick.get_axis(2 if numAxes <= 4 else XboxAxis.RIGHT_X)
            )
            self.state.rightStickY = self._applyDeadzone(
                self._joystick.get_axis(3 if numAxes <= 4 else XboxAxis.RIGHT_Y)
            )
        
        # トリガーの読み取り（0~1にマッピング）
        if numAxes >= 6:
            # 軸4,5がトリガーの場合
            self.state.leftTrigger = (self._joystick.get_axis(4) + 1.0) / 2.0
            self.state.rightTrigger = (self._joystick.get_axis(5) + 1.0) / 2.0
        elif numAxes >= 5:
            # 軸2がLT, 軸5がRTの場合（一部コントローラー）
            self.state.leftTrigger = max(0, self._joystick.get_axis(4))
            self.state.rightTrigger = max(0, self._joystick.get_axis(4))
        
        # ボタンの読み取り
        for i in range(min(numButtons, 15)):
            pressed = self._joystick.get_button(i)
            prevPressed = self._prevButtons.get(i, False)
            
            self.state.buttons[i] = pressed
            
            # ボタン状態変化の検出
            if pressed != prevPressed:
                self._prevButtons[i] = pressed
                if self._buttonCallback:
                    try:
                        button = XboxButton(i)
                        self._buttonCallback(button, pressed)
                    except ValueError:
                        # 未定義のボタン番号
                        pass
        
        # D-Pad（ハット）の読み取り
        if numHats > 0:
            hat = self._joystick.get_hat(0)
            self.state.dpadX = hat[0]
            self.state.dpadY = hat[1]

    def _applyDeadzone(self, value: float) -> float:
        """
        デッドゾーンを適用

        Args:
            value: 入力値 (-1.0 ~ 1.0)

        Returns:
            float: デッドゾーン適用後の値
        """
        if abs(value) < self.deadzone:
            return 0.0
        
        # デッドゾーン外の値を0~1に再マッピング
        sign = 1.0 if value > 0 else -1.0
        normalizedValue = (abs(value) - self.deadzone) / (1.0 - self.deadzone)
        return sign * normalizedValue


# ボタン名のマッピング（表示用）
BUTTON_NAMES = {
    XboxButton.A: "A",
    XboxButton.B: "B",
    XboxButton.X: "X",
    XboxButton.Y: "Y",
    XboxButton.LB: "LB",
    XboxButton.RB: "RB",
    XboxButton.BACK: "BACK",
    XboxButton.START: "START",
    XboxButton.GUIDE: "GUIDE",
    XboxButton.L_STICK: "L3",
    XboxButton.R_STICK: "R3",
}

