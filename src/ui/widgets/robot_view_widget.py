"""
ロボットビューウィジェット

Go2の足接地状態と関節状態を視覚的に表示
Mission Impossible風タクティカルデザイン

主な機能:
- 4足の接地状態表示
- 関節角度の簡易表示
- トップダウンビュー
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPolygonF


class RobotViewWidget(QWidget):
    """
    ロボットビューウィジェット

    Go2のトップダウンビューで足の状態を表示
    """

    def __init__(self, parent=None):
        """
        ロボットビューウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("robotViewWidget")
        self.setMinimumSize(200, 200)
        
        # 足の状態 (FR, FL, RR, RL)
        self._footContacts = [False, False, False, False]
        self._footForces = [0.0, 0.0, 0.0, 0.0]
        
        # モーター温度（各足3関節 × 4足 = 12）
        self._motorTemps = [25.0] * 12
        
        self._setupUi()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # タイトル
        titleLabel = QLabel("◆ FOOT STATUS")
        titleLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(titleLabel)

        # 描画エリア
        layout.addStretch()

        # 凡例
        legendLayout = QGridLayout()
        legendLayout.setSpacing(8)
        
        legends = [
            ("FR", 0, 0), ("FL", 0, 1),
            ("RR", 1, 0), ("RL", 1, 1)
        ]
        
        self.legendLabels = {}
        for name, row, col in legends:
            label = QLabel(f"● {name}: ---")
            label.setStyleSheet("""
                color: #404040;
                font-size: 10px;
            """)
            self.legendLabels[name] = label
            legendLayout.addWidget(label, row, col)

        layout.addLayout(legendLayout)

    def paintEvent(self, event) -> None:
        """描画イベント"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        centerX = rect.width() / 2
        centerY = rect.height() / 2 - 20  # タイトル分オフセット
        
        # ロボット本体のサイズ
        bodyWidth = 80
        bodyHeight = 50
        legOffset = 50

        # 本体 - タクティカル風
        painter.setPen(QPen(QColor("#1A1A1A"), 2))
        painter.setBrush(QBrush(QColor("#0C0C0C")))
        
        bodyRect = QRectF(
            centerX - bodyWidth/2, centerY - bodyHeight/2,
            bodyWidth, bodyHeight
        )
        painter.drawRect(bodyRect)

        # 進行方向マーカー
        painter.setPen(QPen(QColor("#DC143C"), 2))
        painter.drawLine(
            int(centerX), int(centerY - bodyHeight/2),
            int(centerX), int(centerY - bodyHeight/2 - 15)
        )
        # 矢印
        arrowPoints = QPolygonF([
            QPointF(centerX, centerY - bodyHeight/2 - 20),
            QPointF(centerX - 6, centerY - bodyHeight/2 - 12),
            QPointF(centerX + 6, centerY - bodyHeight/2 - 12)
        ])
        painter.setBrush(QBrush(QColor("#DC143C")))
        painter.drawPolygon(arrowPoints)

        # 足の位置
        footPositions = [
            (centerX + legOffset, centerY - legOffset/1.5, "FR", 0),  # Front Right
            (centerX - legOffset, centerY - legOffset/1.5, "FL", 1),  # Front Left
            (centerX + legOffset, centerY + legOffset/1.5, "RR", 2),  # Rear Right
            (centerX - legOffset, centerY + legOffset/1.5, "RL", 3),  # Rear Left
        ]

        for x, y, name, idx in footPositions:
            contact = self._footContacts[idx]
            force = self._footForces[idx]
            
            # 足と本体を繋ぐ線
            painter.setPen(QPen(QColor("#1A1A1A"), 2))
            if idx in [0, 2]:  # 右側
                painter.drawLine(
                    int(centerX + bodyWidth/2), int(y),
                    int(x), int(y)
                )
            else:  # 左側
                painter.drawLine(
                    int(centerX - bodyWidth/2), int(y),
                    int(x), int(y)
                )
            
            # 足の描画
            footRadius = 15
            
            if contact:
                # 接地中
                color = QColor("#00E676")
                glowColor = QColor("#00E676")
                glowColor.setAlpha(80)
                
                # グロー効果
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(glowColor))
                painter.drawEllipse(QPointF(x, y), footRadius + 5, footRadius + 5)
            else:
                # 浮いている
                color = QColor("#DC143C")
            
            # 足本体
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color.darker(150)))
            painter.drawEllipse(QPointF(x, y), footRadius, footRadius)
            
            # 足ラベル
            painter.setPen(QPen(QColor("#FFFFFF")))
            font = QFont("JetBrains Mono", 8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                int(x - 8), int(y + 4),
                name
            )

        # ロボットラベル
        painter.setPen(QPen(QColor("#DC143C")))
        font = QFont("JetBrains Mono", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            int(centerX - 10), int(centerY + 5),
            "GO2"
        )

    def updateFootStates(
        self,
        contacts: list,
        forces: list = None
    ) -> None:
        """
        足の状態を更新

        Args:
            contacts: 接地状態リスト [FR, FL, RR, RL]
            forces: 接地力リスト [FR, FL, RR, RL] (N)
        """
        if len(contacts) >= 4:
            self._footContacts = contacts[:4]
        
        if forces and len(forces) >= 4:
            self._footForces = forces[:4]

        # 凡例更新
        names = ["FR", "FL", "RR", "RL"]
        for i, name in enumerate(names):
            if name in self.legendLabels:
                contact = self._footContacts[i]
                force = self._footForces[i] if forces else 0
                
                if contact:
                    status = f"● {name}: {force:.0f}N"
                    color = "#00E676"
                else:
                    status = f"○ {name}: AIR"
                    color = "#DC143C"
                
                self.legendLabels[name].setText(status)
                self.legendLabels[name].setStyleSheet(f"""
                    color: {color};
                    font-size: 10px;
                """)

        self.update()

    def updateMotorTemperatures(self, temps: list) -> None:
        """
        モーター温度を更新

        Args:
            temps: 温度リスト (12個)
        """
        if len(temps) >= 12:
            self._motorTemps = temps[:12]

