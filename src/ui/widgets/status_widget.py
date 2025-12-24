"""
ステータスウィジェット

Go2の接続状態と動作モードを表示するウィジェット
Mission Impossible風タクティカルデザイン

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
        layout.setSpacing(12)

        # セクションタイトル
        titleLabel = QLabel("◆ TACTICAL CONTROL")
        titleLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(titleLabel)

        # 接続状態フレーム
        connectionFrame = QFrame()
        connectionFrame.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 1px solid #1A1A1A;
                border-left: 2px solid #DC143C;
            }
        """)
        connectionLayout = QVBoxLayout(connectionFrame)
        connectionLayout.setSpacing(10)
        connectionLayout.setContentsMargins(12, 12, 12, 12)

        # 状態インジケーター
        statusRow = QHBoxLayout()
        
        self.statusIndicator = QLabel("●")
        self.statusIndicator.setStyleSheet("""
            color: #DC143C;
            font-size: 14px;
        """)
        statusRow.addWidget(self.statusIndicator)

        self.statusLabel = QLabel("DISCONNECTED")
        self.statusLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        statusRow.addWidget(self.statusLabel)
        statusRow.addStretch()

        connectionLayout.addLayout(statusRow)

        # プロトコル選択
        protocolLayout = QHBoxLayout()
        
        protocolLabel = QLabel("PROTOCOL")
        protocolLabel.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 2px;")
        protocolLayout.addWidget(protocolLabel)

        self.modeCombo = QComboBox()
        self.modeCombo.addItem("WEBRTC [DIRECT] ★")
        self.modeCombo.addItem("WEBSOCKET [RELAY]")
        self.modeCombo.addItem("SDK2 [LEGACY]")
        self.modeCombo.setStyleSheet("""
            QComboBox {
                background-color: #0C0C0C;
                color: #FFFFFF;
                border: 1px solid #1A1A1A;
                padding: 6px 10px;
                font-size: 10px;
            }
            QComboBox:hover {
                border-color: #DC143C;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                background-color: #DC143C;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #FFFFFF;
            }
            QComboBox QAbstractItemView {
                background-color: #0C0C0C;
                color: #FFFFFF;
                border: 1px solid #DC143C;
                selection-background-color: #DC143C;
                selection-color: #FFFFFF;
            }
        """)
        self.modeCombo.currentIndexChanged.connect(self._onModeChanged)
        protocolLayout.addWidget(self.modeCombo, 1)

        connectionLayout.addLayout(protocolLayout)

        # ターゲットIP入力
        ipLayout = QHBoxLayout()
        
        ipLabel = QLabel("TARGET")
        ipLabel.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 2px;")
        ipLayout.addWidget(ipLabel)

        self.ipInput = QLineEdit("ap")
        self.ipInput.setPlaceholderText("ap / IP ADDRESS")
        self.ipInput.setStyleSheet("""
            QLineEdit {
                background-color: #050505;
                color: #DC143C;
                border: 1px solid #1A1A1A;
                border-bottom: 1px solid #DC143C;
                padding: 8px 12px;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QLineEdit:focus {
                border-color: #DC143C;
            }
        """)
        ipLayout.addWidget(self.ipInput, 1)

        connectionLayout.addLayout(ipLayout)

        # 接続ボタン
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(8)
        
        self.connectBtn = QPushButton("▶ CONNECT")
        self.connectBtn.setStyleSheet("""
            QPushButton {
                background-color: #0C0C0C;
                color: #00E676;
                border: 1px solid #00E676;
                padding: 10px 14px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #00E676;
                color: #000000;
            }
        """)
        self.connectBtn.clicked.connect(self._onConnectClicked)
        buttonLayout.addWidget(self.connectBtn)

        self.disconnectBtn = QPushButton("■ TERMINATE")
        self.disconnectBtn.setStyleSheet("""
            QPushButton {
                background-color: #0C0C0C;
                color: #DC143C;
                border: 1px solid #DC143C;
                padding: 10px 14px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #DC143C;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                color: #303030;
                border-color: #1A1A1A;
            }
        """)
        self.disconnectBtn.setEnabled(False)
        self.disconnectBtn.clicked.connect(self.disconnectClicked.emit)
        buttonLayout.addWidget(self.disconnectBtn)

        connectionLayout.addLayout(buttonLayout)
        layout.addWidget(connectionFrame)

        # 動作モード表示
        modeFrame = QFrame()
        modeFrame.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 1px solid #1A1A1A;
                border-left: 2px solid #DC143C;
            }
        """)
        modeLayout = QVBoxLayout(modeFrame)
        modeLayout.setContentsMargins(12, 12, 12, 12)
        modeLayout.setSpacing(4)

        modeTitle = QLabel("OPERATION MODE")
        modeTitle.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 3px;")
        modeLayout.addWidget(modeTitle)

        self.modeLabel = QLabel("---")
        self.modeLabel.setStyleSheet("""
            color: #FFFFFF;
            font-size: 26px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        self.modeLabel.setAlignment(Qt.AlignCenter)
        modeLayout.addWidget(self.modeLabel)

        layout.addWidget(modeFrame)

        # コマンドセクション
        commandLabel = QLabel("◆ COMMAND INTERFACE")
        commandLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 9px;
            letter-spacing: 3px;
            margin-top: 8px;
        """)
        layout.addWidget(commandLabel)

        # 立ち/伏せボタン
        poseLayout = QHBoxLayout()
        poseLayout.setSpacing(8)
        
        self.standUpBtn = QPushButton("▲ DEPLOY")
        self.standUpBtn.setStyleSheet("""
            QPushButton {
                background-color: #0C0C0C;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
                padding: 12px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
                color: #000000;
            }
            QPushButton:disabled {
                color: #303030;
                border-color: #1A1A1A;
            }
        """)
        self.standUpBtn.setEnabled(False)
        self.standUpBtn.clicked.connect(self.standUpClicked.emit)
        poseLayout.addWidget(self.standUpBtn)

        self.standDownBtn = QPushButton("▼ RETRACT")
        self.standDownBtn.setStyleSheet("""
            QPushButton {
                background-color: #0C0C0C;
                color: #808080;
                border: 1px solid #404040;
                padding: 12px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #404040;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                color: #303030;
                border-color: #1A1A1A;
            }
        """)
        self.standDownBtn.setEnabled(False)
        self.standDownBtn.clicked.connect(self.standDownClicked.emit)
        poseLayout.addWidget(self.standDownBtn)

        layout.addLayout(poseLayout)

        # リカバリーボタン
        self.recoveryBtn = QPushButton("↻ RECOVERY PROTOCOL")
        self.recoveryBtn.setStyleSheet("""
            QPushButton {
                background-color: #0C0C0C;
                color: #FF9100;
                border: 1px solid #FF9100;
                padding: 12px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #FF9100;
                color: #000000;
            }
            QPushButton:disabled {
                color: #303030;
                border-color: #1A1A1A;
            }
        """)
        self.recoveryBtn.setEnabled(False)
        self.recoveryBtn.clicked.connect(self.recoveryClicked.emit)
        layout.addWidget(self.recoveryBtn)

        # 緊急停止
        self.emergencyBtn = QPushButton("⚠ EMERGENCY ABORT")
        self.emergencyBtn.setStyleSheet("""
            QPushButton {
                background-color: #DC143C;
                color: #FFFFFF;
                border: 2px solid #FF1744;
                padding: 14px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #FF1744;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                border-color: #303030;
                color: #404040;
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
            color = "#00E676" if self._blinkState else "#006633"
        else:
            color = "#DC143C" if self._blinkState else "#600000"
        self.statusIndicator.setStyleSheet(f"color: {color}; font-size: 14px;")

    def _onModeChanged(self, index: int) -> None:
        """
        接続モード変更時の処理

        Args:
            index: 選択されたモードのインデックス
        """
        if index == 0:  # WebRTC
            self.ipInput.setText("ap")
            self.ipInput.setPlaceholderText("ap / IP ADDRESS")
        elif index == 1:  # WebSocket
            self.ipInput.setText("192.168.123.18")
            self.ipInput.setPlaceholderText("JETSON IP")
        else:  # Direct
            self.ipInput.setText("192.168.123.161")
            self.ipInput.setPlaceholderText("GO2 MCU IP")

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
            self.statusLabel.setText("CONNECTED")
            self.statusLabel.setStyleSheet("""
                color: #00E676;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 3px;
            """)
            self.statusIndicator.setStyleSheet("color: #00E676; font-size: 14px;")
            
            self.connectBtn.setEnabled(False)
            self.disconnectBtn.setEnabled(True)
            self.ipInput.setEnabled(False)
            self.modeCombo.setEnabled(False)
            
            self.standUpBtn.setEnabled(True)
            self.standDownBtn.setEnabled(True)
            self.recoveryBtn.setEnabled(True)
            self.emergencyBtn.setEnabled(True)
        else:
            self.statusLabel.setText("DISCONNECTED")
            self.statusLabel.setStyleSheet("""
                color: #DC143C;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 3px;
            """)
            self.statusIndicator.setStyleSheet("color: #DC143C; font-size: 14px;")
            
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
            "STAND": "#00E676",
            "DOWN": "#404040",
            "WALK": "#FFFFFF",
            "RUN": "#FF9100",
            "IDLE": "#404040",
        }
        color = modeColors.get(mode, "#FFFFFF")
        self.modeLabel.setStyleSheet(f"""
            color: {color};
            font-size: 26px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
