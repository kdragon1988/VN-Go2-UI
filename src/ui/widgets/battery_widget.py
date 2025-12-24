"""
バッテリーウィジェット

Go2のバッテリー状態を視覚的に表示するウィジェット
Mission Impossible風タクティカルデザイン

主な機能:
- バッテリー残量のプログレスバー表示
- 電圧・電流の数値表示
- 低バッテリー警告
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QFont


class BatteryWidget(QWidget):
    """
    バッテリー状態表示ウィジェット

    タクティカルHUD風バッテリーインジケーター
    """

    def __init__(self, parent=None):
        """
        バッテリーウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("batteryWidget")
        
        # 状態値
        self._level = 0
        self._voltage = 0.0
        self._current = 0.0
        self._temperature = 0.0
        
        self._setupUi()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # タイトル
        titleLayout = QHBoxLayout()
        
        titleLabel = QLabel("◆ POWER SYSTEM")
        titleLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()
        
        # パーセント表示
        self.percentLabel = QLabel("0%")
        self.percentLabel.setStyleSheet("""
            color: #00E676;
            font-size: 22px;
            font-weight: bold;
        """)
        titleLayout.addWidget(self.percentLabel)
        
        layout.addLayout(titleLayout)

        # バッテリーバー
        self.batteryBar = QProgressBar()
        self.batteryBar.setRange(0, 100)
        self.batteryBar.setValue(0)
        self.batteryBar.setTextVisible(False)
        self.batteryBar.setFixedHeight(20)
        self.batteryBar.setStyleSheet("""
            QProgressBar {
                background-color: #111111;
                border: 1px solid #1A1A1A;
                border-radius: 0px;
            }
            QProgressBar::chunk {
                background-color: #00E676;
            }
        """)
        layout.addWidget(self.batteryBar)

        # 詳細情報
        detailsLayout = QHBoxLayout()
        detailsLayout.setSpacing(20)

        # 電圧
        voltageContainer = QVBoxLayout()
        voltageContainer.setSpacing(2)
        voltageTitle = QLabel("VOLTAGE")
        voltageTitle.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        self.voltageLabel = QLabel("0.0V")
        self.voltageLabel.setStyleSheet("""
            color: #FFFFFF;
            font-size: 14px;
            font-weight: bold;
        """)
        voltageContainer.addWidget(voltageTitle)
        voltageContainer.addWidget(self.voltageLabel)
        detailsLayout.addLayout(voltageContainer)

        # 電流
        currentContainer = QVBoxLayout()
        currentContainer.setSpacing(2)
        currentTitle = QLabel("CURRENT")
        currentTitle.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        self.currentLabel = QLabel("0.0A")
        self.currentLabel.setStyleSheet("""
            color: #FFFFFF;
            font-size: 14px;
            font-weight: bold;
        """)
        currentContainer.addWidget(currentTitle)
        currentContainer.addWidget(self.currentLabel)
        detailsLayout.addLayout(currentContainer)

        # 温度
        tempContainer = QVBoxLayout()
        tempContainer.setSpacing(2)
        tempTitle = QLabel("TEMP")
        tempTitle.setStyleSheet("color: #404040; font-size: 9px; letter-spacing: 1px;")
        self.tempLabel = QLabel("0°C")
        self.tempLabel.setStyleSheet("""
            color: #FFFFFF;
            font-size: 14px;
            font-weight: bold;
        """)
        tempContainer.addWidget(tempTitle)
        tempContainer.addWidget(self.tempLabel)
        detailsLayout.addLayout(tempContainer)

        detailsLayout.addStretch()
        layout.addLayout(detailsLayout)

        # 警告ラベル
        self.warningLabel = QLabel("")
        self.warningLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        self.warningLabel.setAlignment(Qt.AlignCenter)
        self.warningLabel.hide()
        layout.addWidget(self.warningLabel)

    def updateBattery(self, level: int, voltage: float, current: float, temperature: float = 25.0) -> None:
        """
        バッテリー情報を更新

        Args:
            level: バッテリー残量 (0-100%)
            voltage: 電圧 (V)
            current: 電流 (A)
            temperature: 温度 (℃)
        """
        self._level = max(0, min(100, level))
        self._voltage = voltage
        self._current = current
        self._temperature = temperature

        # UI更新
        self.batteryBar.setValue(self._level)
        self.percentLabel.setText(f"{self._level}%")
        self.voltageLabel.setText(f"{self._voltage:.1f}V")
        self.currentLabel.setText(f"{self._current:.1f}A")
        self.tempLabel.setText(f"{self._temperature:.0f}°C")

        # バッテリーレベルに応じた色変更
        if self._level <= 10:
            barColor = "#DC143C"
            self.percentLabel.setStyleSheet("""
                color: #DC143C;
                font-size: 22px;
                font-weight: bold;
            """)
            self.warningLabel.setText("⚠ CRITICAL - LOW POWER")
            self.warningLabel.show()
        elif self._level <= 30:
            barColor = "#FF9100"
            self.percentLabel.setStyleSheet("""
                color: #FF9100;
                font-size: 22px;
                font-weight: bold;
            """)
            self.warningLabel.setText("⚠ LOW BATTERY")
            self.warningLabel.setStyleSheet("color: #FF9100; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
            self.warningLabel.show()
        else:
            barColor = "#00E676"
            self.percentLabel.setStyleSheet("""
                color: #00E676;
                font-size: 22px;
                font-weight: bold;
            """)
            self.warningLabel.hide()

        # バースタイル更新
        self.batteryBar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #111111;
                border: 1px solid #1A1A1A;
                border-radius: 0px;
            }}
            QProgressBar::chunk {{
                background-color: {barColor};
            }}
        """)

    @property
    def level(self) -> int:
        """バッテリー残量を取得"""
        return self._level

