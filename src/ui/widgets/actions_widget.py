"""
特殊動作ウィジェット

Go2の特殊動作（バックフリップ、ダンス等）を実行するボタン群
Mission Impossible風タクティカルデザイン

主な機能:
- アクロバット動作（フリップ系）
- エモート動作（ダンス、挨拶等）
- 障害物回避トグル
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal


class ActionsWidget(QWidget):
    """
    特殊動作ウィジェット

    バックフリップ、ダンス等の特殊動作ボタンを提供

    Signals:
        actionTriggered(str): 動作名を送信
        obstacleAvoidChanged(bool): 障害物回避ON/OFF
    """

    # シグナル
    actionTriggered = Signal(str)
    obstacleAvoidChanged = Signal(bool)

    def __init__(self, parent=None):
        """
        ウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("actionsWidget")
        self._setupUi()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # タイトル
        titleLabel = QLabel("◆ SPECIAL PROTOCOLS")
        titleLabel.setStyleSheet("""
            color: #DC143C;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(titleLabel)

        # 障害物回避トグル
        avoidFrame = QFrame()
        avoidFrame.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 1px solid #DC143C;
            }
        """)
        avoidLayout = QHBoxLayout(avoidFrame)
        avoidLayout.setContentsMargins(12, 10, 12, 10)
        
        self.obstacleAvoidCheck = QCheckBox("OBSTACLE AVOIDANCE")
        self.obstacleAvoidCheck.setStyleSheet("""
            QCheckBox {
                color: #DC143C;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #DC143C;
                background-color: #050505;
            }
            QCheckBox::indicator:checked {
                background-color: #DC143C;
            }
        """)
        self.obstacleAvoidCheck.toggled.connect(self.obstacleAvoidChanged.emit)
        avoidLayout.addWidget(self.obstacleAvoidCheck)
        avoidLayout.addStretch()
        
        layout.addWidget(avoidFrame)

        # スクロールエリア
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #050505;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #DC143C;
                min-height: 20px;
            }
        """)
        
        scrollContent = QWidget()
        scrollLayout = QVBoxLayout(scrollContent)
        scrollLayout.setSpacing(12)

        # アクロバット
        scrollLayout.addWidget(self._createSection(
            "ACROBATICS",
            [
                ("バック宙返り", "backFlip", "#DC143C"),
                ("前宙返り", "frontFlip", "#FF1744"),
                ("左宙返り", "leftFlip", "#00E676"),
                ("右宙返り", "rightFlip", "#FFFFFF"),
                ("逆立ち", "handStand", "#FF9100"),
                ("前ジャンプ", "frontJump", "#FFFFFF"),
            ]
        ))

        # エモート
        scrollLayout.addWidget(self._createSection(
            "EMOTES",
            [
                ("ダンス1", "dance1", "#DC143C"),
                ("ダンス2", "dance2", "#FFFFFF"),
                ("お座り", "sit", "#00E676"),
                ("ストレッチ", "stretch", "#FF9100"),
                ("吠える", "bark", "#FF1744"),
                ("挨拶", "greeting", "#00E676"),
            ]
        ))

        # コミュニケーション
        scrollLayout.addWidget(self._createSection(
            "COMMUNICATION",
            [
                ("握手", "shakeHand", "#FFFFFF"),
                ("ハイタッチ", "highFive", "#FF9100"),
                ("手を振る", "waveHand", "#FFFFFF"),
                ("ハート", "fingerHeart", "#DC143C"),
                ("昼寝", "nap", "#404040"),
                ("お尻フリフリ", "wiggleHips", "#FF1744"),
            ]
        ))

        scrollLayout.addStretch()
        scrollArea.setWidget(scrollContent)
        layout.addWidget(scrollArea, 1)

    def _createSection(self, title: str, actions: list) -> QFrame:
        """
        アクションセクションを作成

        Args:
            title: セクションタイトル
            actions: [(表示名, 動作名, 色), ...]

        Returns:
            QFrame: セクションフレーム
        """
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 1px solid #1A1A1A;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # セクションタイトル
        titleLabel = QLabel(f"◆ {title}")
        titleLabel.setStyleSheet("""
            color: #404040;
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(titleLabel)

        # ボタングリッド
        grid = QGridLayout()
        grid.setSpacing(6)
        
        for i, (displayName, actionName, color) in enumerate(actions):
            btn = self._createActionButton(displayName, actionName, color)
            grid.addWidget(btn, i // 2, i % 2)
        
        layout.addLayout(grid)
        return frame

    def _createActionButton(self, displayName: str, actionName: str, color: str) -> QPushButton:
        """
        アクションボタンを作成

        Args:
            displayName: 表示名
            actionName: 動作名（シグナルで送信）
            color: ボタンの色

        Returns:
            QPushButton: 作成したボタン
        """
        btn = QPushButton(displayName)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0C0C0C;
                color: {color};
                border: 1px solid {color};
                padding: 8px 4px;
                font-size: 9px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #000000;
            }}
            QPushButton:pressed {{
                background-color: {color}88;
            }}
            QPushButton:disabled {{
                color: #303030;
                border-color: #1A1A1A;
            }}
        """)
        btn.setEnabled(False)  # 接続時に有効化
        btn.clicked.connect(lambda: self.actionTriggered.emit(actionName))
        return btn

    def setEnabled(self, enabled: bool) -> None:
        """
        全ボタンの有効/無効を切り替え

        Args:
            enabled: 有効状態
        """
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(enabled)
        self.obstacleAvoidCheck.setEnabled(enabled)

    def setObstacleAvoidState(self, enabled: bool) -> None:
        """
        障害物回避チェックボックスの状態を設定

        Args:
            enabled: チェック状態
        """
        self.obstacleAvoidCheck.blockSignals(True)
        self.obstacleAvoidCheck.setChecked(enabled)
        self.obstacleAvoidCheck.blockSignals(False)

