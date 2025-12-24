"""
スピードウィジェット

Go2の現在速度を表示するウィジェット
Mission Impossible風タクティカルデザイン

主な機能:
- 前後・左右速度の表示
- 旋回速度の表示
- 速度ベクトルの視覚化
"""

import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF, QFont


class SpeedGauge(QWidget):
    """
    速度ゲージ（ベクトル表示）

    前後左右の速度をベクトルとして視覚化
    """

    def __init__(self, parent=None):
        """初期化"""
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(120, 120)
        
        self._vx = 0.0  # 前後速度
        self._vy = 0.0  # 左右速度
        self._maxSpeed = 1.5  # 最大速度 (m/s)

    def setVelocity(self, vx: float, vy: float) -> None:
        """
        速度を設定

        Args:
            vx: 前後速度 (m/s)
            vy: 左右速度 (m/s)
        """
        self._vx = vx
        self._vy = vy
        self.update()

    def paintEvent(self, event) -> None:
        """描画イベント"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        centerX = rect.width() / 2
        centerY = rect.height() / 2
        radius = min(centerX, centerY) - 10

        # 背景円 - タクティカル風
        painter.setPen(QPen(QColor("#1A1A1A"), 2))
        painter.setBrush(QBrush(QColor("#050505")))
        painter.drawEllipse(QPointF(centerX, centerY), radius, radius)

        # グリッド
        painter.setPen(QPen(QColor("#111111"), 1))
        # 十字線
        painter.drawLine(int(centerX), int(centerY - radius), int(centerX), int(centerY + radius))
        painter.drawLine(int(centerX - radius), int(centerY), int(centerX + radius), int(centerY))
        # 同心円
        for r in [radius * 0.33, radius * 0.66]:
            painter.drawEllipse(QPointF(centerX, centerY), r, r)

        # 速度ベクトル
        # Y軸は画面座標系と逆（上が正）
        vecX = centerX + (self._vy / self._maxSpeed) * (radius - 10)
        vecY = centerY - (self._vx / self._maxSpeed) * (radius - 10)  # 前進が上

        # ベクトル線
        if abs(self._vx) > 0.01 or abs(self._vy) > 0.01:
            painter.setPen(QPen(QColor("#DC143C"), 3))
            painter.drawLine(int(centerX), int(centerY), int(vecX), int(vecY))

            # 矢印の先端
            angle = math.atan2(vecY - centerY, vecX - centerX)
            arrowLen = 10
            arrowAngle = 0.5
            
            p1 = QPointF(
                vecX - arrowLen * math.cos(angle - arrowAngle),
                vecY - arrowLen * math.sin(angle - arrowAngle)
            )
            p2 = QPointF(
                vecX - arrowLen * math.cos(angle + arrowAngle),
                vecY - arrowLen * math.sin(angle + arrowAngle)
            )
            
            arrow = QPolygonF([QPointF(vecX, vecY), p1, p2])
            painter.setBrush(QBrush(QColor("#DC143C")))
            painter.drawPolygon(arrow)

        # 中心点
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(centerX, centerY), 4, 4)

        # 外枠
        painter.setPen(QPen(QColor("#DC143C"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(centerX, centerY), radius, radius)


class SpeedWidget(QWidget):
    """
    スピード表示ウィジェット

    現在の移動速度をゲージと数値で表示
    """

    def __init__(self, parent=None):
        """
        スピードウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("speedWidget")
        
        self._vx = 0.0
        self._vy = 0.0
        self._vyaw = 0.0
        
        self._setupUi()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # タイトル
        titleLabel = QLabel("◆ VELOCITY DATA")
        titleLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(titleLabel)

        # ゲージと数値
        contentLayout = QHBoxLayout()
        contentLayout.setSpacing(16)

        # 速度ゲージ
        self.speedGauge = SpeedGauge()
        contentLayout.addWidget(self.speedGauge)

        # 数値表示
        valuesLayout = QVBoxLayout()
        valuesLayout.setSpacing(6)

        # Vx (前後)
        vxContainer = QVBoxLayout()
        vxContainer.setSpacing(2)
        vxLabel = QLabel("Vx (FWD)")
        vxLabel.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        vxContainer.addWidget(vxLabel)
        
        self.vxValue = QLabel("0.00")
        self.vxValue.setStyleSheet("""
            color: #DC143C;
            font-size: 18px;
            font-weight: bold;
        """)
        vxContainer.addWidget(self.vxValue)
        
        vxUnit = QLabel("m/s")
        vxUnit.setStyleSheet("color: #404040; font-size: 9px;")
        vxContainer.addWidget(vxUnit)
        valuesLayout.addLayout(vxContainer)

        # Vy (左右)
        vyContainer = QVBoxLayout()
        vyContainer.setSpacing(2)
        vyLabel = QLabel("Vy (LAT)")
        vyLabel.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        vyContainer.addWidget(vyLabel)
        
        self.vyValue = QLabel("0.00")
        self.vyValue.setStyleSheet("""
            color: #FFFFFF;
            font-size: 18px;
            font-weight: bold;
        """)
        vyContainer.addWidget(self.vyValue)
        
        vyUnit = QLabel("m/s")
        vyUnit.setStyleSheet("color: #404040; font-size: 9px;")
        vyContainer.addWidget(vyUnit)
        valuesLayout.addLayout(vyContainer)

        # Vyaw (旋回)
        vyawContainer = QVBoxLayout()
        vyawContainer.setSpacing(2)
        vyawLabel = QLabel("Vyaw (ROT)")
        vyawLabel.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        vyawContainer.addWidget(vyawLabel)
        
        self.vyawValue = QLabel("0.00")
        self.vyawValue.setStyleSheet("""
            color: #FF9100;
            font-size: 18px;
            font-weight: bold;
        """)
        vyawContainer.addWidget(self.vyawValue)
        
        vyawUnit = QLabel("rad/s")
        vyawUnit.setStyleSheet("color: #404040; font-size: 9px;")
        vyawContainer.addWidget(vyawUnit)
        valuesLayout.addLayout(vyawContainer)

        valuesLayout.addStretch()
        contentLayout.addLayout(valuesLayout)
        contentLayout.addStretch()

        layout.addLayout(contentLayout)

    def updateVelocity(self, vx: float, vy: float, vyaw: float) -> None:
        """
        速度を更新

        Args:
            vx: 前後速度 (m/s)
            vy: 左右速度 (m/s)
            vyaw: 旋回速度 (rad/s)
        """
        self._vx = vx
        self._vy = vy
        self._vyaw = vyaw

        # ゲージ更新
        self.speedGauge.setVelocity(vx, vy)

        # 数値更新
        self.vxValue.setText(f"{vx:+.2f}")
        self.vyValue.setText(f"{vy:+.2f}")
        self.vyawValue.setText(f"{vyaw:+.2f}")

        # 色の更新（速度に応じて）
        vxColor = "#DC143C" if abs(vx) < 1.0 else "#FF9100"
        vyColor = "#FFFFFF" if abs(vy) < 0.3 else "#FF9100"
        vyawColor = "#FF9100" if abs(vyaw) < 1.0 else "#DC143C"

        self.vxValue.setStyleSheet(f"""
            color: {vxColor};
            font-size: 18px;
            font-weight: bold;
        """)
        self.vyValue.setStyleSheet(f"""
            color: {vyColor};
            font-size: 18px;
            font-weight: bold;
        """)
        self.vyawValue.setStyleSheet(f"""
            color: {vyawColor};
            font-size: 18px;
            font-weight: bold;
        """)

