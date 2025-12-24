"""
IMUウィジェット

Go2のIMU（慣性計測装置）データを視覚的に表示するウィジェット
Mission Impossible風タクティカルデザイン

主な機能:
- Roll/Pitch/Yaw角度のゲージ表示
- 加速度・角速度の数値表示
- 3D姿勢インジケーター
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QFont


class AttitudeIndicator(QWidget):
    """
    姿勢インジケーター（人工水平儀）

    Roll/Pitchを視覚的に表示
    """

    def __init__(self, parent=None):
        """初期化"""
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.setMaximumSize(150, 150)
        
        self._roll = 0.0
        self._pitch = 0.0

    def setAttitude(self, roll: float, pitch: float) -> None:
        """
        姿勢を設定

        Args:
            roll: ロール角（度）
            pitch: ピッチ角（度）
        """
        self._roll = roll
        self._pitch = pitch
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

        # グリッド線
        painter.setPen(QPen(QColor("#111111"), 1))
        for i in range(-2, 3):
            y = centerY + i * radius / 3
            painter.drawLine(
                int(centerX - radius * 0.8), int(y),
                int(centerX + radius * 0.8), int(y)
            )

        # 姿勢表示
        painter.save()
        painter.translate(centerX, centerY)
        painter.rotate(-self._roll)

        # 地平線（ピッチに応じてオフセット）
        pitchOffset = self._pitch * radius / 45  # 45度で画面端
        
        # 地平線
        painter.setPen(QPen(QColor("#DC143C"), 2))
        painter.drawLine(int(-radius * 0.7), int(pitchOffset), int(radius * 0.7), int(pitchOffset))

        painter.restore()

        # センターマーク - クリムゾン
        painter.setPen(QPen(QColor("#DC143C"), 2))
        painter.drawLine(int(centerX - 20), int(centerY), int(centerX - 5), int(centerY))
        painter.drawLine(int(centerX + 5), int(centerY), int(centerX + 20), int(centerY))
        painter.drawLine(int(centerX), int(centerY - 5), int(centerX), int(centerY + 5))

        # 外枠
        painter.setPen(QPen(QColor("#DC143C"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(centerX, centerY), radius, radius)


class IMUWidget(QWidget):
    """
    IMUデータ表示ウィジェット

    Roll/Pitch/Yaw角度と加速度・角速度を表示
    """

    def __init__(self, parent=None):
        """
        IMUウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("imuWidget")
        
        self._roll = 0.0
        self._pitch = 0.0
        self._yaw = 0.0
        self._gyro = [0.0, 0.0, 0.0]
        self._accel = [0.0, 0.0, 0.0]
        
        self._setupUi()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # タイトル
        titleLabel = QLabel("◆ ATTITUDE SENSOR")
        titleLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(titleLabel)

        # メインコンテンツ
        contentLayout = QHBoxLayout()
        contentLayout.setSpacing(16)

        # 姿勢インジケーター
        self.attitudeIndicator = AttitudeIndicator()
        contentLayout.addWidget(self.attitudeIndicator)

        # 角度表示
        anglesLayout = QVBoxLayout()
        anglesLayout.setSpacing(6)

        # Roll
        rollContainer = self._createAngleDisplay("ROLL", "#DC143C")
        self.rollLabel = rollContainer.findChild(QLabel, "valueLabel")
        anglesLayout.addLayout(rollContainer)

        # Pitch
        pitchContainer = self._createAngleDisplay("PITCH", "#FFFFFF")
        self.pitchLabel = pitchContainer.findChild(QLabel, "valueLabel")
        anglesLayout.addLayout(pitchContainer)

        # Yaw
        yawContainer = self._createAngleDisplay("YAW", "#00E676")
        self.yawLabel = yawContainer.findChild(QLabel, "valueLabel")
        anglesLayout.addLayout(yawContainer)

        anglesLayout.addStretch()
        contentLayout.addLayout(anglesLayout)
        contentLayout.addStretch()

        layout.addLayout(contentLayout)

        # 詳細データ（角速度・加速度）
        detailsLayout = QGridLayout()
        detailsLayout.setSpacing(6)

        # 角速度
        gyroTitle = QLabel("GYROSCOPE (rad/s)")
        gyroTitle.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        detailsLayout.addWidget(gyroTitle, 0, 0, 1, 3)

        self.gyroLabels = []
        for i, axis in enumerate(["X", "Y", "Z"]):
            label = QLabel(f"{axis}: 0.00")
            label.setStyleSheet("""
                color: #FFFFFF;
                font-size: 10px;
            """)
            self.gyroLabels.append(label)
            detailsLayout.addWidget(label, 1, i)

        # 加速度
        accelTitle = QLabel("ACCELEROMETER (m/s²)")
        accelTitle.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        detailsLayout.addWidget(accelTitle, 2, 0, 1, 3)

        self.accelLabels = []
        for i, axis in enumerate(["X", "Y", "Z"]):
            label = QLabel(f"{axis}: 0.00")
            label.setStyleSheet("""
                color: #DC143C;
                font-size: 10px;
            """)
            self.accelLabels.append(label)
            detailsLayout.addWidget(label, 3, i)

        layout.addLayout(detailsLayout)

    def _createAngleDisplay(self, name: str, color: str) -> QHBoxLayout:
        """
        角度表示レイアウトを作成

        Args:
            name: 角度名
            color: 表示色

        Returns:
            QHBoxLayout: 作成されたレイアウト
        """
        layout = QHBoxLayout()
        layout.setSpacing(8)

        nameLabel = QLabel(name)
        nameLabel.setStyleSheet(f"color: #404040; font-size: 9px; min-width: 40px; letter-spacing: 1px;")
        layout.addWidget(nameLabel)

        valueLabel = QLabel("0.0°")
        valueLabel.setObjectName("valueLabel")
        valueLabel.setStyleSheet(f"""
            color: {color};
            font-size: 16px;
            font-weight: bold;
            min-width: 70px;
        """)
        layout.addWidget(valueLabel)

        return layout

    def updateIMU(
        self,
        roll: float,
        pitch: float,
        yaw: float,
        gyro: list = None,
        accel: list = None
    ) -> None:
        """
        IMUデータを更新

        Args:
            roll: ロール角（度）
            pitch: ピッチ角（度）
            yaw: ヨー角（度）
            gyro: 角速度 [x, y, z] (rad/s)
            accel: 加速度 [x, y, z] (m/s²)
        """
        self._roll = roll
        self._pitch = pitch
        self._yaw = yaw
        
        if gyro:
            self._gyro = gyro
        if accel:
            self._accel = accel

        # 姿勢インジケーター更新
        self.attitudeIndicator.setAttitude(roll, pitch)

        # 角度ラベル更新
        self.rollLabel.setText(f"{roll:+.1f}°")
        self.pitchLabel.setText(f"{pitch:+.1f}°")
        self.yawLabel.setText(f"{yaw:+.1f}°")

        # 角速度ラベル更新
        if gyro:
            for i, label in enumerate(self.gyroLabels):
                axis = ["X", "Y", "Z"][i]
                label.setText(f"{axis}:{gyro[i]:+.2f}")

        # 加速度ラベル更新
        if accel:
            for i, label in enumerate(self.accelLabels):
                axis = ["X", "Y", "Z"][i]
                label.setText(f"{axis}:{accel[i]:+.2f}")

