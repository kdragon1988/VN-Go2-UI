"""
カメラウィジェット

Go2のカメラ映像をリアルタイム表示するウィジェット

主な機能:
- 映像フレームのリアルタイム表示
- スキャンライン効果
- オーバーレイ情報表示
"""

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont


class CameraWidget(QWidget):
    """
    カメラ映像表示ウィジェット

    Go2の前面カメラ映像をサイバーパンク風エフェクト付きで表示
    """

    def __init__(self, parent=None):
        """
        カメラウィジェットの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setObjectName("cameraWidget")
        
        self._frame = None
        self._recording = False
        self._fps = 0
        self._scanlineOffset = 0
        
        self._setupUi()
        self._startScanlineAnimation()

    def _setupUi(self) -> None:
        """UIコンポーネントの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダー
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(12, 8, 12, 8)
        
        titleLabel = QLabel("📹 LIVE FEED")
        titleLabel.setStyleSheet("""
            color: #00ffff;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 3px;
            background: transparent;
        """)
        headerLayout.addWidget(titleLabel)
        headerLayout.addStretch()

        # 録画インジケーター
        self.recLabel = QLabel("● REC")
        self.recLabel.setStyleSheet("""
            color: #ff3366;
            font-size: 10px;
            font-weight: bold;
            background: transparent;
        """)
        self.recLabel.hide()
        headerLayout.addWidget(self.recLabel)

        # FPS表示
        self.fpsLabel = QLabel("0 FPS")
        self.fpsLabel.setStyleSheet("""
            color: #8080a0;
            font-size: 10px;
            font-family: "SF Mono", monospace;
            background: transparent;
        """)
        headerLayout.addWidget(self.fpsLabel)

        layout.addLayout(headerLayout)

        # 映像表示エリア
        self.videoLabel = QLabel()
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setMinimumSize(320, 240)
        self.videoLabel.setStyleSheet("""
            background-color: #0a0a0f;
            border: none;
        """)
        
        layout.addWidget(self.videoLabel, 1)

        # フッター（オーバーレイ情報）
        footerLayout = QHBoxLayout()
        footerLayout.setContentsMargins(12, 8, 12, 8)
        
        self.timestampLabel = QLabel("--:--:--")
        self.timestampLabel.setStyleSheet("""
            color: #00ff88;
            font-size: 10px;
            font-family: "SF Mono", monospace;
            background: transparent;
        """)
        footerLayout.addWidget(self.timestampLabel)
        footerLayout.addStretch()

        self.resolutionLabel = QLabel("---x---")
        self.resolutionLabel.setStyleSheet("""
            color: #8080a0;
            font-size: 10px;
            font-family: "SF Mono", monospace;
            background: transparent;
        """)
        footerLayout.addWidget(self.resolutionLabel)

        layout.addLayout(footerLayout)
        
        # プレースホルダー表示（UIセットアップ完了後）
        self._showPlaceholder()

    def _showPlaceholder(self) -> None:
        """プレースホルダー表示"""
        # シンプルなプレースホルダー画像を作成
        width, height = 640, 480
        placeholder = np.zeros((height, width, 3), dtype=np.uint8)
        
        # グリッドパターン
        for y in range(0, height, 40):
            placeholder[y:y+1, :] = [20, 40, 40]
        for x in range(0, width, 40):
            placeholder[:, x:x+1] = [20, 40, 40]
        
        # 中央のボックス
        cx, cy = width // 2, height // 2
        boxW, boxH = 200, 60
        placeholder[cy-boxH//2:cy+boxH//2, cx-boxW//2:cx+boxW//2] = [30, 30, 50]
        
        self._setFrame(placeholder)
        self.resolutionLabel.setText("NO SIGNAL")

    def _startScanlineAnimation(self) -> None:
        """スキャンラインアニメーションを開始"""
        self._scanlineTimer = QTimer(self)
        self._scanlineTimer.timeout.connect(self._updateScanline)
        self._scanlineTimer.start(50)  # 20fps

    def _updateScanline(self) -> None:
        """スキャンラインオフセットを更新"""
        self._scanlineOffset = (self._scanlineOffset + 3) % 100

    def _setFrame(self, frame: np.ndarray) -> None:
        """
        フレームを設定して表示

        Args:
            frame: numpy配列 (RGB形式)
        """
        if frame is None:
            return

        height, width = frame.shape[:2]
        channels = frame.shape[2] if len(frame.shape) == 3 else 1

        if channels == 3:
            # RGB -> QImage
            bytesPerLine = 3 * width
            qImage = QImage(
                frame.data, width, height, bytesPerLine,
                QImage.Format_RGB888
            )
        else:
            # グレースケール
            bytesPerLine = width
            qImage = QImage(
                frame.data, width, height, bytesPerLine,
                QImage.Format_Grayscale8
            )

        # スケーリング
        labelSize = self.videoLabel.size()
        scaledPixmap = QPixmap.fromImage(qImage).scaled(
            labelSize,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.videoLabel.setPixmap(scaledPixmap)

    def updateFrame(self, frame: np.ndarray) -> None:
        """
        映像フレームを更新

        Args:
            frame: numpy配列 (BGR or RGB形式)
        """
        if frame is None:
            return

        self._frame = frame
        
        # BGR -> RGB 変換（OpenCV形式の場合）
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # BGRの場合はRGBに変換
            displayFrame = frame.copy()
        else:
            displayFrame = frame

        self._setFrame(displayFrame)

        # 解像度表示
        height, width = frame.shape[:2]
        self.resolutionLabel.setText(f"{width}x{height}")

    def updateTimestamp(self, timestamp: str) -> None:
        """
        タイムスタンプを更新

        Args:
            timestamp: 表示する時刻文字列
        """
        self.timestampLabel.setText(timestamp)

    def updateFps(self, fps: int) -> None:
        """
        FPSを更新

        Args:
            fps: フレームレート
        """
        self._fps = fps
        self.fpsLabel.setText(f"{fps} FPS")

    def setRecording(self, recording: bool) -> None:
        """
        録画状態を設定

        Args:
            recording: 録画中かどうか
        """
        self._recording = recording
        self.recLabel.setVisible(recording)

