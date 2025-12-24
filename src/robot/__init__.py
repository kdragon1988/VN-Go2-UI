"""
ロボット通信モジュール

Unitree Go2との通信を担当するモジュール

接続方式:
- WebRTCClient: 推奨！Jetson不要で直接接続
- WebSocketClient: Jetson経由のWebSocket接続
- Go2Client: SDK2直接接続（cyclonedds必要）
"""

from .go2_client import Go2Client
from .ws_client import WebSocketClient
from .webrtc_client import WebRTCClient, ConnectionMode
from .state import RobotState, MotorState, IMUState

__all__ = [
    "Go2Client",
    "WebSocketClient", 
    "WebRTCClient",
    "ConnectionMode",
    "RobotState",
    "MotorState",
    "IMUState"
]

