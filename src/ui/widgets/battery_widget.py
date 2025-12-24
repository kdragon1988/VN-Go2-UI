"""
バッテリーウィジェット

Go2のバッテリー状態を視覚的に表示するウィジェット

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

    サイバーパンク風のネオングロー効果付きバッテリーインジケーター
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
        layout.setSpacing(12)

        # タイトル
        titleLayout = QHBoxLayout()
        
        titleLabel = QLabel("⚡ BATTERY")
        titleLabel.setObjectName("subtitleLabel")
        titleLabel.setStyleSheet("""
            color: #00ff88;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()
        
        # パーセント表示
        self.percentLabel = QLabel("0%")
        self.percentLabel.setStyleSheet("""
            color: #00ff88;
            font-size: 24px;
            font-weight: bold;
            font-family: "SF Mono", "Monaco", monospace;
        """)
        titleLayout.addWidget(self.percentLabel)
        
        layout.addLayout(titleLayout)

        # バッテリーバー
        self.batteryBar = QProgressBar()
        self.batteryBar.setRange(0, 100)
        self.batteryBar.setValue(0)
        self.batteryBar.setTextVisible(False)
        self.batteryBar.setFixedHeight(24)
        self.batteryBar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00ffaa);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.batteryBar)

        # 詳細情報
        detailsLayout = QHBoxLayout()
        detailsLayout.setSpacing(20)

        # 電圧
        voltageContainer = QVBoxLayout()
        voltageTitle = QLabel("VOLTAGE")
        voltageTitle.setStyleSheet("color: #8080a0; font-size: 9px; letter-spacing: 1px;")
        self.voltageLabel = QLabel("0.0V")
        self.voltageLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-family: "SF Mono", "Monaco", monospace;
        """)
        voltageContainer.addWidget(voltageTitle)
        voltageContainer.addWidget(self.voltageLabel)
        detailsLayout.addLayout(voltageContainer)

        # 電流
        currentContainer = QVBoxLayout()
        currentTitle = QLabel("CURRENT")
        currentTitle.setStyleSheet("color: #8080a0; font-size: 9px; letter-spacing: 1px;")
        self.currentLabel = QLabel("0.0A")
        self.currentLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-family: "SF Mono", "Monaco", monospace;
        """)
        currentContainer.addWidget(currentTitle)
        currentContainer.addWidget(self.currentLabel)
        detailsLayout.addLayout(currentContainer)

        # 温度
        tempContainer = QVBoxLayout()
        tempTitle = QLabel("TEMP")
        tempTitle.setStyleSheet("color: #8080a0; font-size: 9px; letter-spacing: 1px;")
        self.tempLabel = QLabel("0°C")
        self.tempLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 14px;
            font-family: "SF Mono", "Monaco", monospace;
        """)
        tempContainer.addWidget(tempTitle)
        tempContainer.addWidget(self.tempLabel)
        detailsLayout.addLayout(tempContainer)

        detailsLayout.addStretch()
        layout.addLayout(detailsLayout)

        # 警告ラベル
        self.warningLabel = QLabel("")
        self.warningLabel.setStyleSheet("""
            color: #ff3366;
            font-size: 11px;
            font-weight: bold;
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
            barStyle = """
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff3366, stop:1 #ff0044);
                    border-radius: 3px;
                }
            """
            self.percentLabel.setStyleSheet("""
                color: #ff3366;
                font-size: 24px;
                font-weight: bold;
                font-family: "SF Mono", "Monaco", monospace;
            """)
            self.warningLabel.setText("⚠️ LOW BATTERY - CRITICAL")
            self.warningLabel.show()
        elif self._level <= 30:
            barStyle = """
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ffff00, stop:1 #ffcc00);
                    border-radius: 3px;
                }
            """
            self.percentLabel.setStyleSheet("""
                color: #ffff00;
                font-size: 24px;
                font-weight: bold;
                font-family: "SF Mono", "Monaco", monospace;
            """)
            self.warningLabel.setText("⚠️ LOW BATTERY")
            self.warningLabel.setStyleSheet("color: #ffff00; font-size: 11px; font-weight: bold;")
            self.warningLabel.show()
        else:
            barStyle = """
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00ff88, stop:1 #00ffaa);
                    border-radius: 3px;
                }
            """
            self.percentLabel.setStyleSheet("""
                color: #00ff88;
                font-size: 24px;
                font-weight: bold;
                font-family: "SF Mono", "Monaco", monospace;
            """)
            self.warningLabel.hide()

        # バースタイル更新
        self.batteryBar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
            }}
            {barStyle}
        """)

    @property
    def level(self) -> int:
        """バッテリー残量を取得"""
        return self._level

