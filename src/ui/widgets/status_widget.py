"""
ステータスウィジェット

Go2の接続状態と動作モードを表示するウィジェット

主な機能:
- 接続状態のインジケーター
- 動作モード表示
- IPアドレス設定
- 接続/切断ボタン
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer


class StatusWidget(QWidget):
    """
    ステータス表示ウィジェット

    接続状態、動作モード、制御ボタンを集約
    """

    # シグナル定義
    connectClicked = Signal(str)      # 接続ボタンクリック（IPアドレス）
    disconnectClicked = Signal()      # 切断ボタンクリック
    standUpClicked = Signal()         # 立ち上がりボタン
    standDownClicked = Signal()       # 伏せるボタン
    emergencyStopClicked = Signal()   # 緊急停止ボタン
    recoveryClicked = Signal()        # リカバリーボタン

    def __init__(self, parent=None):
        """
        ステータスウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("statusWidget")
        
        self._connected = False
        self._mode = "---"
        self._blinkState = False
        
        self._setupUi()
        self._startBlinkAnimation()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # タイトル
        titleLabel = QLabel("🤖 SYSTEM STATUS")
        titleLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(titleLabel)

        # 接続状態
        connectionFrame = QFrame()
        connectionFrame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0f;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        connectionLayout = QVBoxLayout(connectionFrame)
        connectionLayout.setSpacing(8)

        # 状態インジケーター
        statusRow = QHBoxLayout()
        
        self.statusIndicator = QLabel("●")
        self.statusIndicator.setStyleSheet("""
            color: #ff3366;
            font-size: 16px;
        """)
        statusRow.addWidget(self.statusIndicator)

        self.statusLabel = QLabel("OFFLINE")
        self.statusLabel.setStyleSheet("""
            color: #ff3366;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        statusRow.addWidget(self.statusLabel)
        statusRow.addStretch()

        connectionLayout.addLayout(statusRow)

        # 接続モード選択
        modeSelectLayout = QHBoxLayout()
        
        modeSelectLabel = QLabel("MODE:")
        modeSelectLabel.setStyleSheet("color: #8080a0; font-size: 11px;")
        modeSelectLayout.addWidget(modeSelectLabel)

        self.modeCombo = QComboBox()
        self.modeCombo.addItem("🌐 WebSocket (Jetson経由)")
        self.modeCombo.addItem("📡 Direct (SDK2シミュレーション)")
        self.modeCombo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a2e;
                color: #00ffff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #00ffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #00ffff;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #00ffff;
                border: 1px solid #2a2a4a;
                selection-background-color: #2a2a4a;
            }
        """)
        self.modeCombo.currentIndexChanged.connect(self._onModeChanged)
        modeSelectLayout.addWidget(self.modeCombo, 1)

        connectionLayout.addLayout(modeSelectLayout)

        # IPアドレス入力
        ipLayout = QHBoxLayout()
        
        ipLabel = QLabel("IP:")
        ipLabel.setStyleSheet("color: #8080a0; font-size: 11px;")
        ipLayout.addWidget(ipLabel)

        self.ipInput = QLineEdit("192.168.123.18")  # デフォルトはJetsonのIP
        self.ipInput.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                color: #00ffff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: "SF Mono", monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #00ffff;
            }
        """)
        ipLayout.addWidget(self.ipInput, 1)

        connectionLayout.addLayout(ipLayout)

        # 接続ボタン
        buttonLayout = QHBoxLayout()
        
        self.connectBtn = QPushButton("CONNECT")
        self.connectBtn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                color: #00ff88;
                border: 1px solid #00ff88;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #0a0a0f;
            }
        """)
        self.connectBtn.clicked.connect(self._onConnectClicked)
        buttonLayout.addWidget(self.connectBtn)

        self.disconnectBtn = QPushButton("DISCONNECT")
        self.disconnectBtn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                color: #ff3366;
                border: 1px solid #ff3366;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ff3366;
                color: #0a0a0f;
            }
            QPushButton:disabled {
                color: #4a4a6a;
                border-color: #2a2a4a;
            }
        """)
        self.disconnectBtn.setEnabled(False)
        self.disconnectBtn.clicked.connect(self.disconnectClicked.emit)
        buttonLayout.addWidget(self.disconnectBtn)

        connectionLayout.addLayout(buttonLayout)
        layout.addWidget(connectionFrame)

        # 動作モード
        modeFrame = QFrame()
        modeFrame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0f;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        modeLayout = QVBoxLayout(modeFrame)

        modeTitle = QLabel("MODE")
        modeTitle.setStyleSheet("color: #8080a0; font-size: 9px; letter-spacing: 2px;")
        modeLayout.addWidget(modeTitle)

        self.modeLabel = QLabel("---")
        self.modeLabel.setStyleSheet("""
            color: #ffff00;
            font-size: 20px;
            font-weight: bold;
            font-family: "SF Mono", monospace;
            letter-spacing: 3px;
        """)
        self.modeLabel.setAlignment(Qt.AlignCenter)
        modeLayout.addWidget(self.modeLabel)

        layout.addWidget(modeFrame)

        # 制御ボタン
        controlLabel = QLabel("CONTROL")
        controlLabel.setStyleSheet("""
            color: #8080a0;
            font-size: 9px;
            letter-spacing: 2px;
        """)
        layout.addWidget(controlLabel)

        # 立ち/伏せボタン
        poseLayout = QHBoxLayout()
        
        self.standUpBtn = QPushButton("▲ STAND")
        self.standUpBtn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                color: #00ffff;
                border: 1px solid #00ffff;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00ffff;
                color: #0a0a0f;
            }
            QPushButton:disabled {
                color: #4a4a6a;
                border-color: #2a2a4a;
            }
        """)
        self.standUpBtn.setEnabled(False)
        self.standUpBtn.clicked.connect(self.standUpClicked.emit)
        poseLayout.addWidget(self.standUpBtn)

        self.standDownBtn = QPushButton("▼ DOWN")
        self.standDownBtn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                color: #ff00ff;
                border: 1px solid #ff00ff;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ff00ff;
                color: #0a0a0f;
            }
            QPushButton:disabled {
                color: #4a4a6a;
                border-color: #2a2a4a;
            }
        """)
        self.standDownBtn.setEnabled(False)
        self.standDownBtn.clicked.connect(self.standDownClicked.emit)
        poseLayout.addWidget(self.standDownBtn)

        layout.addLayout(poseLayout)

        # リカバリーボタン
        self.recoveryBtn = QPushButton("↻ RECOVERY")
        self.recoveryBtn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                color: #ffff00;
                border: 1px solid #ffff00;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ffff00;
                color: #0a0a0f;
            }
            QPushButton:disabled {
                color: #4a4a6a;
                border-color: #2a2a4a;
            }
        """)
        self.recoveryBtn.setEnabled(False)
        self.recoveryBtn.clicked.connect(self.recoveryClicked.emit)
        layout.addWidget(self.recoveryBtn)

        # 緊急停止
        self.emergencyBtn = QPushButton("⛔ EMERGENCY STOP")
        self.emergencyBtn.setStyleSheet("""
            QPushButton {
                background-color: #ff3366;
                color: #ffffff;
                border: 2px solid #ff0044;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff0044;
            }
            QPushButton:disabled {
                background-color: #4a4a6a;
                border-color: #2a2a4a;
                color: #8080a0;
            }
        """)
        self.emergencyBtn.setEnabled(False)
        self.emergencyBtn.clicked.connect(self.emergencyStopClicked.emit)
        layout.addWidget(self.emergencyBtn)

        layout.addStretch()

    def _startBlinkAnimation(self) -> None:
        """点滅アニメーションを開始"""
        self._blinkTimer = QTimer(self)
        self._blinkTimer.timeout.connect(self._blink)
        self._blinkTimer.start(500)

    def _blink(self) -> None:
        """点滅状態を切り替え"""
        self._blinkState = not self._blinkState
        if self._connected:
            color = "#00ff88" if self._blinkState else "#008844"
        else:
            color = "#ff3366" if self._blinkState else "#882233"
        self.statusIndicator.setStyleSheet(f"color: {color}; font-size: 16px;")

    def _onModeChanged(self, index: int) -> None:
        """
        接続モード変更時の処理

        Args:
            index: 選択されたモードのインデックス
        """
        if index == 0:  # WebSocket
            self.ipInput.setText("192.168.123.18")  # Jetson IP
        else:  # Direct
            self.ipInput.setText("192.168.123.161")  # Go2 MCU IP

    def _onConnectClicked(self) -> None:
        """接続ボタンクリック時の処理"""
        ip = self.ipInput.text().strip()
        if ip:
            self.connectClicked.emit(ip)

    def updateConnectionState(self, connected: bool) -> None:
        """
        接続状態を更新

        Args:
            connected: 接続状態
        """
        self._connected = connected
        
        if connected:
            self.statusLabel.setText("ONLINE")
            self.statusLabel.setStyleSheet("""
                color: #00ff88;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            """)
            self.statusIndicator.setStyleSheet("color: #00ff88; font-size: 16px;")
            
            self.connectBtn.setEnabled(False)
            self.disconnectBtn.setEnabled(True)
            self.ipInput.setEnabled(False)
            self.modeCombo.setEnabled(False)
            
            self.standUpBtn.setEnabled(True)
            self.standDownBtn.setEnabled(True)
            self.recoveryBtn.setEnabled(True)
            self.emergencyBtn.setEnabled(True)
        else:
            self.statusLabel.setText("OFFLINE")
            self.statusLabel.setStyleSheet("""
                color: #ff3366;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            """)
            self.statusIndicator.setStyleSheet("color: #ff3366; font-size: 16px;")
            
            self.connectBtn.setEnabled(True)
            self.disconnectBtn.setEnabled(False)
            self.ipInput.setEnabled(True)
            self.modeCombo.setEnabled(True)
            
            self.standUpBtn.setEnabled(False)
            self.standDownBtn.setEnabled(False)
            self.recoveryBtn.setEnabled(False)
            self.emergencyBtn.setEnabled(False)
            
            self.modeLabel.setText("---")

    def updateMode(self, mode: str) -> None:
        """
        動作モードを更新

        Args:
            mode: 動作モード文字列
        """
        self._mode = mode
        self.modeLabel.setText(mode)
        
        # モードに応じた色変更
        modeColors = {
            "STAND": "#00ff88",
            "DOWN": "#ff00ff",
            "WALK": "#00ffff",
            "RUN": "#ffff00",
            "IDLE": "#8080a0",
        }
        color = modeColors.get(mode, "#ffff00")
        self.modeLabel.setStyleSheet(f"""
            color: {color};
            font-size: 20px;
            font-weight: bold;
            font-family: "SF Mono", monospace;
            letter-spacing: 3px;
        """)

