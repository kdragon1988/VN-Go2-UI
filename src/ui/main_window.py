"""
メインウィンドウ

Unitree Go2 Controller - Mission Impossible Edition
戦術的HUDインターフェース

主な機能:
- タクティカルダッシュボードレイアウト
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
    CameraWidget, StatusWidget, RobotViewWidget, SpeedWidget,
    ActionsWidget
)
from .styles import loadStylesheet


class MainWindow(QMainWindow):
    """
    メインウィンドウ

    Mission Impossible風タクティカルHUDのメインウィンドウ
    """

    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        
        self.setWindowTitle("◆ UNITREE GO2 // TACTICAL INTERFACE ◆")
        self.setMinimumSize(1600, 900)
        self.resize(1900, 1000)
        
        # スタイルシート適用（ミッションインポッシブル風）
        stylesheet = loadStylesheet("mission")
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
        mainLayout.setContentsMargins(12, 12, 12, 12)
        mainLayout.setSpacing(12)

        # === 左パネル（ステータス・コントロール） ===
        leftPanel = QFrame()
        leftPanel.setObjectName("tacticalPanel")
        leftPanel.setStyleSheet("""
            QFrame#tacticalPanel {
                background-color: #0A0A0A;
                border: 1px solid #1A1A1A;
                border-top: 2px solid #DC143C;
            }
        """)
        leftPanel.setFixedWidth(340)
        leftLayout = QVBoxLayout(leftPanel)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(0)

        # ヘッダー - IMF Tactical Style
        headerContainer = QWidget()
        headerContainer.setStyleSheet("background-color: #050505;")
        headerLayout = QVBoxLayout(headerContainer)
        headerLayout.setContentsMargins(16, 16, 16, 12)
        headerLayout.setSpacing(4)
        
        # クラシファイドマーカー
        classifiedLabel = QLabel("◆◆◆ CLASSIFIED ◆◆◆")
        classifiedLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        classifiedLabel.setAlignment(Qt.AlignCenter)
        headerLayout.addWidget(classifiedLabel)
        
        # メインタイトル
        titleLabel = QLabel("UNITREE GO2")
        titleLabel.setStyleSheet("""
            color: #FFFFFF;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 8px;
        """)
        titleLabel.setAlignment(Qt.AlignCenter)
        headerLayout.addWidget(titleLabel)

        # サブタイトル
        subtitleLabel = QLabel("TACTICAL CONTROL SYSTEM v1.0")
        subtitleLabel.setStyleSheet("""
            color: #404040;
            font-size: 9px;
            letter-spacing: 3px;
        """)
        subtitleLabel.setAlignment(Qt.AlignCenter)
        headerLayout.addWidget(subtitleLabel)

        leftLayout.addWidget(headerContainer)

        # セパレーター
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #DC143C; min-height: 2px; max-height: 2px;")
        leftLayout.addWidget(separator)

        # ステータスウィジェット
        self.statusWidget = StatusWidget()
        leftLayout.addWidget(self.statusWidget, 1)

        mainLayout.addWidget(leftPanel)

        # === 中央パネル（カメラ + 情報） ===
        centerPanel = QWidget()
        centerLayout = QVBoxLayout(centerPanel)
        centerLayout.setContentsMargins(0, 0, 0, 0)
        centerLayout.setSpacing(12)

        # ヘッダー（時刻表示）- 作戦時刻風
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(16)
        
        # ライブフィードインジケーター
        liveIndicator = QLabel("● LIVE")
        liveIndicator.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        headerLayout.addWidget(liveIndicator)
        
        # 時刻表示
        self.clockLabel = QLabel("00:00:00")
        self.clockLabel.setStyleSheet("""
            color: #FFFFFF;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        headerLayout.addWidget(self.clockLabel)
        
        headerLayout.addStretch()

        # 日付表示
        self.dateLabel = QLabel("2025-01-01")
        self.dateLabel.setStyleSheet("""
            color: #404040;
            font-size: 11px;
            letter-spacing: 2px;
        """)
        headerLayout.addWidget(self.dateLabel)
        
        # ミッションステータス
        missionLabel = QLabel("◆ MISSION ACTIVE")
        missionLabel.setStyleSheet("""
            color: #00E676;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        headerLayout.addWidget(missionLabel)

        centerLayout.addLayout(headerLayout)

        # カメラウィジェット - 諜報映像風
        self.cameraWidget = CameraWidget()
        self.cameraWidget.setStyleSheet("""
            QWidget#cameraWidget {
                background-color: #050505;
                border: 1px solid #DC143C;
            }
        """)
        centerLayout.addWidget(self.cameraWidget, 2)

        # 下部情報パネル
        bottomInfoLayout = QHBoxLayout()
        bottomInfoLayout.setSpacing(12)

        # バッテリーウィジェット
        batteryFrame = QFrame()
        batteryFrame.setStyleSheet("""
            QFrame {
                background-color: #0A0A0A;
                border: 1px solid #1A1A1A;
                border-left: 2px solid #DC143C;
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
                background-color: #0A0A0A;
                border: 1px solid #1A1A1A;
                border-left: 2px solid #DC143C;
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
        rightLayout.setSpacing(12)

        # IMUウィジェット
        imuFrame = QFrame()
        imuFrame.setStyleSheet("""
            QFrame {
                background-color: #0A0A0A;
                border: 1px solid #1A1A1A;
                border-top: 2px solid #DC143C;
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
                background-color: #0A0A0A;
                border: 1px solid #1A1A1A;
                border-top: 2px solid #DC143C;
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
                background-color: #0A0A0A;
                border: 1px solid #1A1A1A;
                border-top: 2px solid #DC143C;
            }
        """)
        controllerFrameLayout = QVBoxLayout(controllerFrame)
        controllerFrameLayout.setContentsMargins(0, 0, 0, 0)
        self.controllerWidget = ControllerWidget()
        controllerFrameLayout.addWidget(self.controllerWidget)
        rightLayout.addWidget(controllerFrame, 1)

        mainLayout.addWidget(rightPanel)

        # === 最右パネル（特殊動作） ===
        actionsPanel = QFrame()
        actionsPanel.setStyleSheet("""
            QFrame {
                background-color: #0A0A0A;
                border: 1px solid #DC143C;
            }
        """)
        actionsPanel.setFixedWidth(280)
        actionsPanelLayout = QVBoxLayout(actionsPanel)
        actionsPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.actionsWidget = ActionsWidget()
        actionsPanelLayout.addWidget(self.actionsWidget)
        mainLayout.addWidget(actionsPanel)

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
                background-color: #050505;
                color: #404040;
                border-top: 1px solid #1A1A1A;
                font-size: 10px;
                letter-spacing: 1px;
            }
        """)
        self.setStatusBar(statusBar)

        # 左側: ショートカットヒント
        hintLabel = QLabel("◆ ESC: ABORT  |  SPACE: DEPLOY  |  D: RETRACT")
        hintLabel.setStyleSheet("color: #404040; padding: 4px;")
        statusBar.addWidget(hintLabel)

        # 右側: バージョン
        versionLabel = QLabel("◆ TACTICAL INTERFACE v1.0")
        versionLabel.setStyleSheet("color: #DC143C; padding: 4px;")
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
        self.actionsWidget.setEnabled(connected)

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
            "◆ MISSION ABORT",
            "ミッションを終了しますか？\n\n"
            "ロボットとの接続が切断されます。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

