"""
コントローラーウィジェット

Xbox互換コントローラーの入力状態を視覚的に表示

主な機能:
- スティック位置の表示
- ボタン押下状態の表示
- トリガー値の表示
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont


class StickIndicator(QWidget):
    """
    アナログスティックインジケーター

    スティックの傾きを視覚的に表示
    """

    def __init__(self, label: str = "L", parent=None):
        """
        初期化

        Args:
            label: スティックラベル（"L" or "R"）
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setMinimumSize(80, 80)
        self.setMaximumSize(100, 100)
        
        self._label = label
        self._x = 0.0
        self._y = 0.0
        self._pressed = False

    def setPosition(self, x: float, y: float, pressed: bool = False) -> None:
        """
        スティック位置を設定

        Args:
            x: X軸位置 (-1.0 ~ 1.0)
            y: Y軸位置 (-1.0 ~ 1.0)
            pressed: 押し込み状態
        """
        self._x = max(-1.0, min(1.0, x))
        self._y = max(-1.0, min(1.0, y))
        self._pressed = pressed
        self.update()

    def paintEvent(self, event) -> None:
        """描画イベント"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        centerX = rect.width() / 2
        centerY = rect.height() / 2
        radius = min(centerX, centerY) - 8

        # 背景円
        painter.setPen(QPen(QColor("#2a2a4a"), 2))
        painter.setBrush(QBrush(QColor("#0a0a0f")))
        painter.drawEllipse(QPointF(centerX, centerY), radius, radius)

        # グリッド線
        painter.setPen(QPen(QColor("#1a1a2e"), 1))
        painter.drawLine(int(centerX), int(centerY - radius), int(centerX), int(centerY + radius))
        painter.drawLine(int(centerX - radius), int(centerY), int(centerX + radius), int(centerY))

        # スティック位置
        stickX = centerX + self._x * (radius - 10)
        stickY = centerY + self._y * (radius - 10)
        
        # スティックの軌跡線
        painter.setPen(QPen(QColor("#00ffff"), 1, Qt.DashLine))
        painter.drawLine(int(centerX), int(centerY), int(stickX), int(stickY))

        # スティックノブ
        stickRadius = 12 if self._pressed else 10
        stickColor = QColor("#ff00ff") if self._pressed else QColor("#00ffff")
        
        painter.setPen(QPen(stickColor, 2))
        painter.setBrush(QBrush(stickColor.darker(150)))
        painter.drawEllipse(QPointF(stickX, stickY), stickRadius, stickRadius)

        # ラベル
        painter.setPen(QPen(QColor("#8080a0")))
        font = QFont("SF Mono", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(int(centerX - 5), int(centerY + radius + 15), self._label)


class ControllerWidget(QWidget):
    """
    コントローラー状態表示ウィジェット

    Xbox互換コントローラーの全入力状態を表示
    """

    def __init__(self, parent=None):
        """
        コントローラーウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("controllerWidget")
        
        self._connected = False
        self._controllerName = ""
        
        self._setupUi()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # タイトルと接続状態
        titleLayout = QHBoxLayout()
        
        titleLabel = QLabel("🎮 CONTROLLER")
        titleLabel.setStyleSheet("""
            color: #ffff00;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()

        self.statusLabel = QLabel("DISCONNECTED")
        self.statusLabel.setStyleSheet("""
            color: #ff3366;
            font-size: 10px;
            font-weight: bold;
        """)
        titleLayout.addWidget(self.statusLabel)

        layout.addLayout(titleLayout)

        # コントローラー名
        self.nameLabel = QLabel("")
        self.nameLabel.setStyleSheet("color: #8080a0; font-size: 10px;")
        layout.addWidget(self.nameLabel)

        # スティック
        sticksLayout = QHBoxLayout()
        sticksLayout.setSpacing(20)

        # 左スティック
        leftStickContainer = QVBoxLayout()
        self.leftStick = StickIndicator("L")
        leftStickContainer.addWidget(self.leftStick, alignment=Qt.AlignCenter)
        self.leftStickLabel = QLabel("0.00, 0.00")
        self.leftStickLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 10px;
            font-family: "SF Mono", monospace;
        """)
        self.leftStickLabel.setAlignment(Qt.AlignCenter)
        leftStickContainer.addWidget(self.leftStickLabel)
        sticksLayout.addLayout(leftStickContainer)

        # 右スティック
        rightStickContainer = QVBoxLayout()
        self.rightStick = StickIndicator("R")
        rightStickContainer.addWidget(self.rightStick, alignment=Qt.AlignCenter)
        self.rightStickLabel = QLabel("0.00, 0.00")
        self.rightStickLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 10px;
            font-family: "SF Mono", monospace;
        """)
        self.rightStickLabel.setAlignment(Qt.AlignCenter)
        rightStickContainer.addWidget(self.rightStickLabel)
        sticksLayout.addLayout(rightStickContainer)

        layout.addLayout(sticksLayout)

        # トリガー
        triggersLayout = QHBoxLayout()
        triggersLayout.setSpacing(12)

        # LT
        ltContainer = QVBoxLayout()
        ltLabel = QLabel("LT")
        ltLabel.setStyleSheet("color: #8080a0; font-size: 9px;")
        ltLabel.setAlignment(Qt.AlignCenter)
        ltContainer.addWidget(ltLabel)
        
        self.ltBar = QProgressBar()
        self.ltBar.setRange(0, 100)
        self.ltBar.setValue(0)
        self.ltBar.setTextVisible(False)
        self.ltBar.setFixedHeight(12)
        self.ltBar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #ff00ff;
                border-radius: 2px;
            }
        """)
        ltContainer.addWidget(self.ltBar)
        triggersLayout.addLayout(ltContainer)

        # RT
        rtContainer = QVBoxLayout()
        rtLabel = QLabel("RT")
        rtLabel.setStyleSheet("color: #8080a0; font-size: 9px;")
        rtLabel.setAlignment(Qt.AlignCenter)
        rtContainer.addWidget(rtLabel)
        
        self.rtBar = QProgressBar()
        self.rtBar.setRange(0, 100)
        self.rtBar.setValue(0)
        self.rtBar.setTextVisible(False)
        self.rtBar.setFixedHeight(12)
        self.rtBar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #ff00ff;
                border-radius: 2px;
            }
        """)
        rtContainer.addWidget(self.rtBar)
        triggersLayout.addLayout(rtContainer)

        layout.addLayout(triggersLayout)

        # ボタン表示
        buttonsLayout = QGridLayout()
        buttonsLayout.setSpacing(6)

        self.buttonLabels = {}
        buttons = [
            ("A", 0, 2, "#00ff88"),
            ("B", 0, 3, "#ff3366"),
            ("X", 1, 1, "#00aaff"),
            ("Y", 1, 2, "#ffff00"),
            ("LB", 0, 0, "#8080a0"),
            ("RB", 0, 4, "#8080a0"),
            ("BACK", 1, 0, "#8080a0"),
            ("START", 1, 4, "#8080a0"),
        ]

        for name, row, col, color in buttons:
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(40, 24)
            label.setStyleSheet(f"""
                background-color: #1a1a2e;
                color: #4a4a6a;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
            """)
            self.buttonLabels[name] = (label, color)
            buttonsLayout.addWidget(label, row, col)

        layout.addLayout(buttonsLayout)

    def updateControllerState(
        self,
        connected: bool,
        name: str = "",
        leftX: float = 0.0,
        leftY: float = 0.0,
        rightX: float = 0.0,
        rightY: float = 0.0,
        lt: float = 0.0,
        rt: float = 0.0,
        buttons: dict = None,
        leftPressed: bool = False,
        rightPressed: bool = False
    ) -> None:
        """
        コントローラー状態を更新

        Args:
            connected: 接続状態
            name: コントローラー名
            leftX: 左スティックX
            leftY: 左スティックY
            rightX: 右スティックX
            rightY: 右スティックY
            lt: 左トリガー (0-1)
            rt: 右トリガー (0-1)
            buttons: ボタン状態辞書
            leftPressed: 左スティック押し込み
            rightPressed: 右スティック押し込み
        """
        self._connected = connected
        self._controllerName = name

        # 接続状態
        if connected:
            self.statusLabel.setText("CONNECTED")
            self.statusLabel.setStyleSheet("""
                color: #00ff88;
                font-size: 10px;
                font-weight: bold;
            """)
            self.nameLabel.setText(name)
        else:
            self.statusLabel.setText("DISCONNECTED")
            self.statusLabel.setStyleSheet("""
                color: #ff3366;
                font-size: 10px;
                font-weight: bold;
            """)
            self.nameLabel.setText("")

        # スティック
        self.leftStick.setPosition(leftX, leftY, leftPressed)
        self.rightStick.setPosition(rightX, rightY, rightPressed)
        self.leftStickLabel.setText(f"{leftX:+.2f}, {leftY:+.2f}")
        self.rightStickLabel.setText(f"{rightX:+.2f}, {rightY:+.2f}")

        # トリガー
        self.ltBar.setValue(int(lt * 100))
        self.rtBar.setValue(int(rt * 100))

        # ボタン
        if buttons:
            buttonMap = {
                0: "A", 1: "B", 2: "X", 3: "Y",
                4: "LB", 5: "RB", 6: "BACK", 7: "START"
            }
            for btnId, btnName in buttonMap.items():
                if btnName in self.buttonLabels:
                    label, color = self.buttonLabels[btnName]
                    pressed = buttons.get(btnId, False)
                    if pressed:
                        label.setStyleSheet(f"""
                            background-color: {color};
                            color: #0a0a0f;
                            border: 1px solid {color};
                            border-radius: 4px;
                            font-size: 9px;
                            font-weight: bold;
                        """)
                    else:
                        label.setStyleSheet(f"""
                            background-color: #1a1a2e;
                            color: #4a4a6a;
                            border: 1px solid #2a2a4a;
                            border-radius: 4px;
                            font-size: 9px;
                            font-weight: bold;
                        """)

