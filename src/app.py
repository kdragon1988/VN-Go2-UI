"""
メインアプリケーション

Unitree Go2 Controller の統合アプリケーション

主な機能:
- UIとロボット通信の統合
- コントローラー入力の処理
- 状態管理とイベント処理

制限事項:
- シングルインスタンスのみサポート
"""

import sys
import math
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from .robot import Go2Client, WebSocketClient, WebRTCClient, ConnectionMode, RobotState
from .controller import GamepadController, GamepadState, XboxButton
from .ui import MainWindow
from .utils import setup_logger, get_logger


class Go2ControllerApp(QObject):
    """
    Go2コントローラーアプリケーション

    UI、ロボット通信、コントローラー入力を統合管理

    Attributes:
        window: メインウィンドウ
        robotClient: ロボット通信クライアント
        gamepad: ゲームパッドコントローラー
    
    接続モード:
        - webrtc: WebRTC直接接続（推奨、Jetson不要）
        - websocket: Jetson経由のWebSocket接続
        - direct: SDK2直接接続（cyclonedds必要）
    """

    # シグナル定義
    connectionStateChanged = Signal(bool)
    robotStateUpdated = Signal(object)
    gamepadStateUpdated = Signal(object)

    # 速度設定
    BASE_SPEED_VX = 0.8      # 基本前後速度 (m/s)
    BASE_SPEED_VY = 0.3      # 基本左右速度 (m/s)
    BASE_SPEED_VYAW = 0.8    # 基本旋回速度 (rad/s)
    BOOST_MULTIPLIER = 1.5   # ブースト時の速度倍率

    # Jetson WebSocketポート
    JETSON_WS_PORT = 8765

    def __init__(self):
        """アプリケーションの初期化"""
        super().__init__()

        # ロガー初期化
        self.logger = setup_logger("unitree_go2")
        self.logger.info("Unitree Go2 Controller を起動しています...")

        # コンポーネント初期化（接続時に選択）
        self.robotClient = None
        self.gamepad = GamepadController()
        self.window: Optional[MainWindow] = None

        # 接続モード: "webrtc" (推奨) / "websocket" / "direct"
        self._connectionMode = "webrtc"

        # 状態
        self._connected = False
        self._speedMultiplier = 1.0
        self._lastRobotState: Optional[RobotState] = None

        # タイマー
        self._gamepadTimer: Optional[QTimer] = None
        self._controlTimer: Optional[QTimer] = None

    def initialize(self) -> bool:
        """
        アプリケーションの初期化

        Returns:
            bool: 初期化成功時True
        """
        try:
            # メインウィンドウ作成
            self.window = MainWindow()

            # シグナル接続
            self._connectSignals()

            # ゲームパッド初期化
            self.gamepad.initialize()
            self.gamepad.start()

            # コールバック設定
            self.gamepad.setStateCallback(self._onGamepadState)
            self.gamepad.setButtonCallback(self._onGamepadButton)

            # ゲームパッドポーリングタイマー（メインスレッドで実行必須）
            self._gamepadTimer = QTimer()
            self._gamepadTimer.timeout.connect(self._pollGamepad)
            self._gamepadTimer.start(16)  # ~60Hz

            # 制御ループタイマー
            self._controlTimer = QTimer()
            self._controlTimer.timeout.connect(self._controlLoop)
            self._controlTimer.start(20)  # 50Hz

            self.logger.info("初期化完了")
            return True

        except Exception as e:
            self.logger.error(f"初期化エラー: {e}")
            return False

    def _connectSignals(self) -> None:
        """シグナルとスロットの接続"""
        if not self.window:
            return

        # ステータスウィジェットのシグナル
        self.window.statusWidget.connectClicked.connect(self._onConnect)
        self.window.statusWidget.disconnectClicked.connect(self._onDisconnect)
        self.window.statusWidget.standUpClicked.connect(self._onStandUp)
        self.window.statusWidget.standDownClicked.connect(self._onStandDown)
        self.window.statusWidget.emergencyStopClicked.connect(self._onEmergencyStop)
        self.window.statusWidget.recoveryClicked.connect(self._onRecovery)
        
        # 特殊動作ウィジェットのシグナル
        self.window.actionsWidget.actionTriggered.connect(self._onSpecialAction)
        self.window.actionsWidget.obstacleAvoidChanged.connect(self._onObstacleAvoidChanged)

    def _pollGamepad(self) -> None:
        """
        ゲームパッドをポーリング（メインスレッドで実行）
        
        macOSではpygameのイベント処理はメインスレッドでのみ可能
        """
        self.gamepad.poll()

    @Slot(str)
    def _onConnect(self, ip: str) -> None:
        """
        接続ボタンクリック時の処理

        Args:
            ip: 接続先IPアドレス
        """
        # 接続モードを判定（ステータスウィジェットから取得）
        if hasattr(self.window.statusWidget, 'modeCombo'):
            modeIndex = self.window.statusWidget.modeCombo.currentIndex()
            modeMap = {0: "webrtc", 1: "websocket", 2: "direct"}
            self._connectionMode = modeMap.get(modeIndex, "webrtc")
        
        modeLabels = {
            "webrtc": "🚀 WebRTC (直接接続)",
            "websocket": "🌐 WebSocket (Jetson経由)",
            "direct": "📡 Direct (SDK2)"
        }
        modeStr = modeLabels.get(self._connectionMode, "Unknown")
        self.logger.info(f"Go2に接続中: {ip} ({modeStr})")
        
        try:
            if self._connectionMode == "webrtc":
                # WebRTC直接接続（推奨！）
                # IPが空または"ap"の場合はAPモード
                if not ip or ip.lower() == "ap":
                    self.robotClient = WebRTCClient(connectionMode=ConnectionMode.LOCAL_AP)
                else:
                    self.robotClient = WebRTCClient(
                        robotIp=ip, 
                        connectionMode=ConnectionMode.LOCAL_STA
                    )
                self.robotClient.setStateCallback(self._onRobotState)
                self.robotClient.setVideoCallback(self._onVideoFrame)
                
                if self.robotClient.connect():
                    self._connected = True
                    self.window.updateConnectionState(True)
                    self.logger.info("🚀 WebRTC接続成功！（Jetson不要）")
                else:
                    self._showConnectionError(ip, "WebRTC接続に失敗しました")
                    
            elif self._connectionMode == "websocket":
                # WebSocket経由でJetsonに接続
                self.robotClient = WebSocketClient(jetsonIp=ip, port=self.JETSON_WS_PORT)
                self.robotClient.setStateCallback(self._onRobotState)
                
                if self.robotClient.connect():
                    self._connected = True
                    self.window.updateConnectionState(True)
                    self.logger.info("WebSocket接続成功")
                else:
                    self._showConnectionError(ip, "WebSocket接続に失敗しました")
            else:
                # 従来のSDK2直接接続（シミュレーション）
                self.robotClient = Go2Client()
                self.robotClient.robotIp = ip
                self.robotClient.setStateCallback(self._onRobotState)
                self.robotClient.setVideoCallback(self._onVideoFrame)
                
                if self.robotClient.connect():
                    self._connected = True
                    self.window.updateConnectionState(True)
                    self.logger.info("接続成功")
                else:
                    self._showConnectionError(ip, "SDK2接続に失敗しました")
                    
        except Exception as e:
            self.logger.error(f"接続エラー: {e}")
            QMessageBox.critical(
                self.window,
                "接続エラー",
                f"接続中にエラーが発生しました。\n\n{e}"
            )
    
    def _showConnectionError(self, ip: str, message: str) -> None:
        """接続エラーダイアログを表示"""
        self.logger.error(message)
        
        hints = {
            "webrtc": "• Go2のWiFi APに接続しているか確認\n• または同一LAN上にいるか確認",
            "websocket": "• Jetson上で bridge_server.py を起動してください",
            "direct": "• cyclonedds のインストールが必要です\n• Python 3.11が必要です"
        }
        
        QMessageBox.warning(
            self.window,
            "接続エラー",
            f"{message}\n\nIP: {ip}\n\n"
            f"ヒント:\n{hints.get(self._connectionMode, '')}"
        )

    @Slot()
    def _onDisconnect(self) -> None:
        """切断ボタンクリック時の処理"""
        self.logger.info("Go2から切断中...")
        
        try:
            if self.robotClient:
                self.robotClient.disconnect()
            self._connected = False
            self.window.updateConnectionState(False)
            self.logger.info("切断完了")
        except Exception as e:
            self.logger.error(f"切断エラー: {e}")

    @Slot()
    def _onStandUp(self) -> None:
        """立ち上がりコマンド"""
        if self._connected and self.robotClient:
            self.logger.info("コマンド: Stand Up")
            self.robotClient.standUp()

    @Slot()
    def _onStandDown(self) -> None:
        """伏せるコマンド"""
        if self._connected and self.robotClient:
            self.logger.info("コマンド: Stand Down")
            self.robotClient.standDown()

    @Slot()
    def _onEmergencyStop(self) -> None:
        """緊急停止コマンド"""
        self.logger.warning("⚠️ 緊急停止!")
        if self._connected and self.robotClient:
            self.robotClient.emergencyStop()

    @Slot()
    def _onRecovery(self) -> None:
        """リカバリーコマンド"""
        if self._connected and self.robotClient:
            self.logger.info("コマンド: Recovery Stand")
            self.robotClient.recoveryStand()

    @Slot(str)
    def _onSpecialAction(self, actionName: str) -> None:
        """
        特殊動作実行

        Args:
            actionName: 動作名
        """
        if not self._connected or not self.robotClient:
            return
        
        self.logger.info(f"🎭 特殊動作: {actionName}")
        
        # 動作名からメソッドを呼び出し
        actionMethod = getattr(self.robotClient, actionName, None)
        if actionMethod and callable(actionMethod):
            try:
                actionMethod()
            except Exception as e:
                self.logger.error(f"特殊動作エラー: {e}")
        else:
            self.logger.warning(f"未対応の動作: {actionName}")

    @Slot(bool)
    def _onObstacleAvoidChanged(self, enabled: bool) -> None:
        """
        障害物回避ON/OFF

        Args:
            enabled: 有効状態
        """
        if not self._connected or not self.robotClient:
            return
        
        self.logger.info(f"🛡️ 障害物回避: {'ON' if enabled else 'OFF'}")
        
        if hasattr(self.robotClient, 'setObstacleAvoid'):
            self.robotClient.setObstacleAvoid(enabled)

    def _onRobotState(self, state: RobotState) -> None:
        """
        ロボット状態受信コールバック

        Args:
            state: 受信したロボット状態
        """
        self._lastRobotState = state

        if self.window:
            # モード更新
            self.window.updateMode(state.modeStr)

            # バッテリー更新
            self.window.updateBattery(
                state.batteryLevel,
                state.batteryVoltage,
                state.batteryCurrent,
                state.batteryTemperature
            )

            # IMU更新
            self.window.updateIMU(
                state.imu.rollDeg,
                state.imu.pitchDeg,
                state.imu.yawDeg,
                state.imu.gyroscope,
                state.imu.accelerometer
            )

            # 速度更新
            self.window.updateVelocity(
                state.velocity[0],
                state.velocity[1],
                state.velocity[2]
            )

            # 足状態更新
            contacts = [foot.contact for foot in state.feet]
            forces = [foot.force for foot in state.feet]
            self.window.updateFootStates(contacts, forces)

    def _onVideoFrame(self, frame) -> None:
        """
        映像フレーム受信コールバック

        Args:
            frame: 受信した映像フレーム
        """
        if self.window:
            self.window.updateVideoFrame(frame)

    def _onGamepadState(self, state: GamepadState) -> None:
        """
        ゲームパッド状態更新コールバック

        Args:
            state: ゲームパッド状態
        """
        if self.window:
            self.window.updateControllerState(
                state.connected,
                state.controllerName,
                state.leftStickX,
                state.leftStickY,
                state.rightStickX,
                state.rightStickY,
                state.leftTrigger,
                state.rightTrigger,
                state.buttons,
                state.isButtonPressed(XboxButton.L_STICK),
                state.isButtonPressed(XboxButton.R_STICK)
            )

    def _onGamepadButton(self, button: XboxButton, pressed: bool) -> None:
        """
        ゲームパッドボタンイベントコールバック

        Args:
            button: 押されたボタン
            pressed: 押下状態
        """
        if not pressed:  # ボタンリリース時は無視
            return

        self.logger.debug(f"ボタン: {button.name}")

        if button == XboxButton.A:
            self._onStandUp()
        elif button == XboxButton.B:
            self._onStandDown()
        elif button == XboxButton.X:
            if self._connected and self.robotClient:
                self.robotClient.balanceStand()
        elif button == XboxButton.Y:
            if self._connected and self.robotClient:
                self.robotClient.damp()
        elif button == XboxButton.BACK:
            self._onEmergencyStop()
        elif button == XboxButton.START:
            self._onRecovery()
        elif button == XboxButton.LB:
            self._speedMultiplier = max(0.3, self._speedMultiplier - 0.1)
            self.logger.info(f"速度倍率: {self._speedMultiplier:.1f}")
        elif button == XboxButton.RB:
            self._speedMultiplier = min(1.5, self._speedMultiplier + 0.1)
            self.logger.info(f"速度倍率: {self._speedMultiplier:.1f}")

    def _controlLoop(self) -> None:
        """
        制御ループ（50Hz）

        コントローラー入力を処理して移動コマンドを送信
        """
        if not self._connected or not self.robotClient:
            return

        state = self.gamepad.state
        if not state.connected:
            return

        # スティック入力から速度を計算
        # 左スティック: 前後移動 + 左右移動
        # 右スティック: 旋回
        vx = -state.leftStickY * self.BASE_SPEED_VX * self._speedMultiplier
        vy = -state.leftStickX * self.BASE_SPEED_VY * self._speedMultiplier
        vyaw = -state.rightStickX * self.BASE_SPEED_VYAW * self._speedMultiplier

        # トリガーでブースト
        if state.rightTrigger > 0.1:
            vx *= (1.0 + state.rightTrigger * (self.BOOST_MULTIPLIER - 1.0))
        if state.leftTrigger > 0.1:
            vx *= -(1.0 + state.leftTrigger * (self.BOOST_MULTIPLIER - 1.0))

        # 移動コマンド送信
        self.robotClient.move(vx, vy, vyaw)

    def run(self) -> int:
        """
        アプリケーションを実行

        Returns:
            int: 終了コード
        """
        if not self.window:
            self.logger.error("ウィンドウが初期化されていません")
            return 1

        self.window.show()
        self.logger.info("アプリケーション起動完了")

        return 0

    def cleanup(self) -> None:
        """
        終了処理

        リソースの解放と接続の切断
        """
        self.logger.info("終了処理中...")

        # タイマー停止
        if self._gamepadTimer:
            self._gamepadTimer.stop()
        
        if self._controlTimer:
            self._controlTimer.stop()

        # ゲームパッド停止
        self.gamepad.stop()

        # ロボット切断
        if self._connected:
            self.go2Client.disconnect()

        self.logger.info("終了処理完了")


def createApplication() -> tuple:
    """
    アプリケーションインスタンスを作成

    Returns:
        tuple: (QApplication, Go2ControllerApp)
    """
    # QApplication作成
    app = QApplication(sys.argv)
    app.setApplicationName("Unitree Go2 Controller")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VN_Unitree")

    # コントローラーアプリ作成
    controllerApp = Go2ControllerApp()

    return app, controllerApp

