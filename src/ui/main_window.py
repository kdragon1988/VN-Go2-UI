"""
メインウィンドウ

Unitree Go2 Controller のメインUI

主な機能:
- ダッシュボードレイアウト
- 全ウィジェットの統合
- キーボードショートカット
"""

import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSplitter, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QAction

from .widgets import (
    BatteryWidget, IMUWidget, ControllerWidget,
    CameraWidget, StatusWidget, RobotViewWidget, SpeedWidget
)
from .styles import loadStylesheet


class MainWindow(QMainWindow):
    """
    メインウィンドウ

    サイバーパンク風ダッシュボードUIのメインウィンドウ
    """

    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        
        self.setWindowTitle("UNITREE GO2 CONTROLLER // CYBERPUNK EDITION")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # スタイルシート適用
        stylesheet = loadStylesheet("cyberpunk")
        self.setStyleSheet(stylesheet)
        
        self._setupUi()
        self._setupShortcuts()
        self._setupStatusBar()
        self._startClock()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        # 中央ウィジェット
        centralWidget = QWidget()
        centralWidget.setObjectName("centralWidget")
        self.setCentralWidget(centralWidget)

        # メインレイアウト
        mainLayout = QHBoxLayout(centralWidget)
        mainLayout.setContentsMargins(16, 16, 16, 16)
        mainLayout.setSpacing(16)

        # === 左パネル（ステータス・コントロール） ===
        leftPanel = QFrame()
        leftPanel.setStyleSheet("""
            QFrame {
                background-color: #12121a;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
            }
        """)
        leftPanel.setFixedWidth(320)
        leftLayout = QVBoxLayout(leftPanel)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(0)

        # ロゴ/タイトル
        titleContainer = QWidget()
        titleLayout = QVBoxLayout(titleContainer)
        titleLayout.setContentsMargins(16, 20, 16, 16)
        
        titleLabel = QLabel("UNITREE GO2")
        titleLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 6px;
        """)
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLayout.addWidget(titleLabel)

        subtitleLabel = QLabel("CONTROL SYSTEM v1.0")
        subtitleLabel.setStyleSheet("""
            color: #8080a0;
            font-size: 10px;
            letter-spacing: 4px;
        """)
        subtitleLabel.setAlignment(Qt.AlignCenter)
        titleLayout.addWidget(subtitleLabel)

        leftLayout.addWidget(titleContainer)

        # セパレーター
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #2a2a4a;")
        separator.setFixedHeight(1)
        leftLayout.addWidget(separator)

        # ステータスウィジェット
        self.statusWidget = StatusWidget()
        leftLayout.addWidget(self.statusWidget, 1)

        mainLayout.addWidget(leftPanel)

        # === 中央パネル（カメラ + 情報） ===
        centerPanel = QWidget()
        centerLayout = QVBoxLayout(centerPanel)
        centerLayout.setContentsMargins(0, 0, 0, 0)
        centerLayout.setSpacing(16)

        # ヘッダー（時刻表示）
        headerLayout = QHBoxLayout()
        
        self.clockLabel = QLabel("00:00:00")
        self.clockLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 18px;
            font-family: "SF Mono", monospace;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        headerLayout.addWidget(self.clockLabel)
        headerLayout.addStretch()

        self.dateLabel = QLabel("2025-01-01")
        self.dateLabel.setStyleSheet("""
            color: #8080a0;
            font-size: 12px;
            font-family: "SF Mono", monospace;
            letter-spacing: 1px;
        """)
        headerLayout.addWidget(self.dateLabel)

        centerLayout.addLayout(headerLayout)

        # カメラウィジェット
        self.cameraWidget = CameraWidget()
        self.cameraWidget.setStyleSheet("""
            QWidget#cameraWidget {
                background-color: #0a0a0f;
                border: 2px solid #00ffff;
                border-radius: 12px;
            }
        """)
        centerLayout.addWidget(self.cameraWidget, 2)

        # 下部情報パネル
        bottomInfoLayout = QHBoxLayout()
        bottomInfoLayout.setSpacing(16)

        # バッテリーウィジェット
        batteryFrame = QFrame()
        batteryFrame.setStyleSheet("""
            QFrame {
                background-color: #12121a;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
            }
        """)
        batteryFrameLayout = QVBoxLayout(batteryFrame)
        batteryFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.batteryWidget = BatteryWidget()
        batteryFrameLayout.addWidget(self.batteryWidget)
        bottomInfoLayout.addWidget(batteryFrame, 1)

        # 速度ウィジェット
        speedFrame = QFrame()
        speedFrame.setStyleSheet("""
            QFrame {
                background-color: #12121a;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
            }
        """)
        speedFrameLayout = QVBoxLayout(speedFrame)
        speedFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.speedWidget = SpeedWidget()
        speedFrameLayout.addWidget(self.speedWidget)
        bottomInfoLayout.addWidget(speedFrame, 1)

        centerLayout.addLayout(bottomInfoLayout, 1)

        mainLayout.addWidget(centerPanel, 1)

        # === 右パネル（センサー情報） ===
        rightPanel = QWidget()
        rightLayout = QVBoxLayout(rightPanel)
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightLayout.setSpacing(16)

        # IMUウィジェット
        imuFrame = QFrame()
        imuFrame.setStyleSheet("""
            QFrame {
                background-color: #12121a;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
            }
        """)
        imuFrameLayout = QVBoxLayout(imuFrame)
        imuFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.imuWidget = IMUWidget()
        imuFrameLayout.addWidget(self.imuWidget)
        rightLayout.addWidget(imuFrame, 1)

        # ロボットビューウィジェット
        robotFrame = QFrame()
        robotFrame.setStyleSheet("""
            QFrame {
                background-color: #12121a;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
            }
        """)
        robotFrameLayout = QVBoxLayout(robotFrame)
        robotFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.robotViewWidget = RobotViewWidget()
        robotFrameLayout.addWidget(self.robotViewWidget)
        rightLayout.addWidget(robotFrame, 1)

        # コントローラーウィジェット
        controllerFrame = QFrame()
        controllerFrame.setStyleSheet("""
            QFrame {
                background-color: #12121a;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
            }
        """)
        controllerFrameLayout = QVBoxLayout(controllerFrame)
        controllerFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.controllerWidget = ControllerWidget()
        controllerFrameLayout.addWidget(self.controllerWidget)
        rightLayout.addWidget(controllerFrame, 1)

        mainLayout.addWidget(rightPanel)

    def _setupShortcuts(self) -> None:
        """キーボードショートカットの設定"""
        # 緊急停止: Escape
        escapeShortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        escapeShortcut.activated.connect(self._onEmergencyStop)

        # 立ち上がり: Space
        spaceShortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        spaceShortcut.activated.connect(self.statusWidget.standUpClicked.emit)

        # 伏せる: D
        downShortcut = QShortcut(QKeySequence("D"), self)
        downShortcut.activated.connect(self.statusWidget.standDownClicked.emit)

    def _setupStatusBar(self) -> None:
        """ステータスバーの設定"""
        statusBar = QStatusBar()
        statusBar.setStyleSheet("""
            QStatusBar {
                background-color: #0a0a0f;
                color: #8080a0;
                border-top: 1px solid #2a2a4a;
                font-family: "SF Mono", monospace;
                font-size: 11px;
            }
        """)
        self.setStatusBar(statusBar)

        # 左側: ショートカットヒント
        hintLabel = QLabel("ESC: Emergency Stop | SPACE: Stand | D: Down")
        hintLabel.setStyleSheet("color: #4a4a6a; padding: 4px;")
        statusBar.addWidget(hintLabel)

        # 右側: バージョン
        versionLabel = QLabel("v1.0.0 // CYBERPUNK EDITION")
        versionLabel.setStyleSheet("color: #00ffff; padding: 4px;")
        statusBar.addPermanentWidget(versionLabel)

    def _startClock(self) -> None:
        """時計の開始"""
        self._clockTimer = QTimer(self)
        self._clockTimer.timeout.connect(self._updateClock)
        self._clockTimer.start(1000)
        self._updateClock()

    def _updateClock(self) -> None:
        """時計を更新"""
        from datetime import datetime
        now = datetime.now()
        self.clockLabel.setText(now.strftime("%H:%M:%S"))
        self.dateLabel.setText(now.strftime("%Y-%m-%d"))
        
        # カメラのタイムスタンプも更新
        self.cameraWidget.updateTimestamp(now.strftime("%H:%M:%S"))

    def _onEmergencyStop(self) -> None:
        """緊急停止ショートカット"""
        self.statusWidget.emergencyStopClicked.emit()

    # === 外部からのUI更新メソッド ===

    @Slot(bool)
    def updateConnectionState(self, connected: bool) -> None:
        """接続状態を更新"""
        self.statusWidget.updateConnectionState(connected)

    @Slot(str)
    def updateMode(self, mode: str) -> None:
        """動作モードを更新"""
        self.statusWidget.updateMode(mode)

    @Slot(int, float, float, float)
    def updateBattery(self, level: int, voltage: float, current: float, temperature: float) -> None:
        """バッテリー情報を更新"""
        self.batteryWidget.updateBattery(level, voltage, current, temperature)

    @Slot(float, float, float, list, list)
    def updateIMU(self, roll: float, pitch: float, yaw: float, gyro: list, accel: list) -> None:
        """IMU情報を更新"""
        self.imuWidget.updateIMU(roll, pitch, yaw, gyro, accel)

    @Slot(float, float, float)
    def updateVelocity(self, vx: float, vy: float, vyaw: float) -> None:
        """速度情報を更新"""
        self.speedWidget.updateVelocity(vx, vy, vyaw)

    @Slot(list, list)
    def updateFootStates(self, contacts: list, forces: list) -> None:
        """足の状態を更新"""
        self.robotViewWidget.updateFootStates(contacts, forces)

    @Slot(object)
    def updateVideoFrame(self, frame) -> None:
        """映像フレームを更新"""
        self.cameraWidget.updateFrame(frame)

    @Slot(bool, str, float, float, float, float, float, float, dict, bool, bool)
    def updateControllerState(
        self,
        connected: bool,
        name: str,
        leftX: float,
        leftY: float,
        rightX: float,
        rightY: float,
        lt: float,
        rt: float,
        buttons: dict,
        leftPressed: bool,
        rightPressed: bool
    ) -> None:
        """コントローラー状態を更新"""
        self.controllerWidget.updateControllerState(
            connected, name, leftX, leftY, rightX, rightY,
            lt, rt, buttons, leftPressed, rightPressed
        )

    def closeEvent(self, event) -> None:
        """ウィンドウクローズイベント"""
        reply = QMessageBox.question(
            self,
            "終了確認",
            "アプリケーションを終了しますか？\n\n"
            "ロボットとの接続が切断されます。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

