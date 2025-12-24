#!/usr/bin/env python3
"""
Unitree Go2 WebSocket ブリッジサーバー

Jetson上で動作し、外部PC（Mac）からのWebSocket接続を受け付けて
SDK2経由でGo2を制御するブリッジサーバー

使用方法（Jetson上で実行）:
    python3 bridge_server.py

接続先:
    ws://192.168.123.18:8765

主な機能:
- WebSocket経由でのコマンド受信
- SDK2を使ったGo2制御
- ロボット状態のリアルタイム配信
- カメラ映像のストリーミング（オプション）

制限事項:
- Jetson上でのみ動作
- unitree_sdk2pyが必要
"""

import asyncio
import json
import time
import threading
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass, asdict
import struct

# WebSocket
try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("[Bridge] websocketsがインストールされていません: pip install websockets")

# Unitree SDK2
try:
    from unitree_sdk2py.core.channel import ChannelFactory, ChannelType
    from unitree_sdk2py.go2.sport.sport_client import SportClient
    from unitree_sdk2py.go2.video.video_client import VideoClient
    SDK2_AVAILABLE = True
except ImportError:
    SDK2_AVAILABLE = False
    print("[Bridge] unitree_sdk2pyが見つかりません。シミュレーションモードで起動します")

import numpy as np


# ============================================================================
# 設定
# ============================================================================

HOST = "0.0.0.0"  # すべてのインターフェースでリッスン
PORT = 8765
ROBOT_IP = "127.0.0.1"  # Jetsonからはlocalhostで接続


# ============================================================================
# ロボット状態
# ============================================================================

@dataclass
class RobotState:
    """ロボット状態データ"""
    timestamp: float = 0.0
    connected: bool = False
    mode: str = "UNKNOWN"
    batteryLevel: int = 0
    batteryVoltage: float = 0.0
    batteryCurrent: float = 0.0
    batteryTemperature: float = 25.0
    imuRoll: float = 0.0
    imuPitch: float = 0.0
    imuYaw: float = 0.0
    imuGyro: list = None
    imuAccel: list = None
    velocityX: float = 0.0
    velocityY: float = 0.0
    velocityYaw: float = 0.0
    footContacts: list = None
    footForces: list = None
    
    def __post_init__(self):
        if self.imuGyro is None:
            self.imuGyro = [0.0, 0.0, 0.0]
        if self.imuAccel is None:
            self.imuAccel = [0.0, 0.0, 9.81]
        if self.footContacts is None:
            self.footContacts = [False, False, False, False]
        if self.footForces is None:
            self.footForces = [0.0, 0.0, 0.0, 0.0]
    
    def toDict(self) -> dict:
        return asdict(self)


# ============================================================================
# ブリッジサーバー
# ============================================================================

class Go2BridgeServer:
    """
    Go2 WebSocketブリッジサーバー
    
    外部PCからのWebSocket接続を受け付け、SDK2経由でGo2を制御
    """
    
    def __init__(self, host: str = HOST, port: int = PORT):
        """
        ブリッジサーバーの初期化
        
        Args:
            host: リッスンするホスト
            port: リッスンするポート
        """
        self.host = host
        self.port = port
        
        # 接続クライアント
        self.clients: Set = set()
        
        # SDK2クライアント
        self.sportClient: Optional[Any] = None
        self.videoClient: Optional[Any] = None
        
        # 状態
        self.state = RobotState()
        self.running = False
        
        # スレッド
        self.stateThread: Optional[threading.Thread] = None
        self.videoThread: Optional[threading.Thread] = None
        
        # シミュレーションモード
        self.simulationMode = not SDK2_AVAILABLE

    async def start(self) -> None:
        """サーバーを開始"""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║     Unitree Go2 WebSocket Bridge Server                      ║
╚══════════════════════════════════════════════════════════════╝

   Mode: {"SIMULATION" if self.simulationMode else "SDK2"}
   Host: {self.host}
   Port: {self.port}
   URL:  ws://{self.host}:{self.port}

   Macから接続:
   - IPアドレス: 192.168.123.18
   - ポート: {self.port}
        """)
        
        # SDK2初期化
        if not self.simulationMode:
            self._initSdk2()
        
        # 状態更新スレッド開始
        self.running = True
        self.stateThread = threading.Thread(target=self._stateLoop, daemon=True)
        self.stateThread.start()
        
        # WebSocketサーバー開始
        async with serve(self._handleClient, self.host, self.port):
            print(f"[Bridge] サーバー起動完了 - ws://{self.host}:{self.port}")
            await asyncio.Future()  # 永久に実行

    def _initSdk2(self) -> None:
        """SDK2を初期化"""
        try:
            print("[Bridge] SDK2を初期化中...")
            
            ChannelFactory.Instance().Init(0, ROBOT_IP)
            
            self.sportClient = SportClient()
            self.sportClient.SetTimeout(5.0)
            self.sportClient.Init()
            
            self.state.connected = True
            print("[Bridge] SDK2初期化完了")
            
        except Exception as e:
            print(f"[Bridge] SDK2初期化エラー: {e}")
            self.simulationMode = True

    async def _handleClient(self, websocket) -> None:
        """
        クライアント接続を処理
        
        Args:
            websocket: WebSocket接続
        """
        clientAddr = websocket.remote_address
        print(f"[Bridge] クライアント接続: {clientAddr}")
        self.clients.add(websocket)
        
        try:
            # 接続確認メッセージ送信
            await websocket.send(json.dumps({
                "type": "connected",
                "simulationMode": self.simulationMode,
                "version": "1.0.0"
            }))
            
            # メッセージ受信ループ
            async for message in websocket:
                await self._handleMessage(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"[Bridge] クライアント切断: {clientAddr}")
        except Exception as e:
            print(f"[Bridge] エラー: {e}")
        finally:
            self.clients.discard(websocket)

    async def _handleMessage(self, websocket, message: str) -> None:
        """
        メッセージを処理
        
        Args:
            websocket: WebSocket接続
            message: 受信メッセージ
        """
        try:
            data = json.loads(message)
            msgType = data.get("type", "")
            
            if msgType == "move":
                # 移動コマンド
                vx = data.get("vx", 0.0)
                vy = data.get("vy", 0.0)
                vyaw = data.get("vyaw", 0.0)
                self._move(vx, vy, vyaw)
                
            elif msgType == "standUp":
                self._standUp()
                
            elif msgType == "standDown":
                self._standDown()
                
            elif msgType == "balanceStand":
                self._balanceStand()
                
            elif msgType == "recoveryStand":
                self._recoveryStand()
                
            elif msgType == "stopMove":
                self._stopMove()
                
            elif msgType == "damp":
                self._damp()
                
            elif msgType == "emergencyStop":
                self._emergencyStop()
                
            elif msgType == "getState":
                # 状態を返す
                await websocket.send(json.dumps({
                    "type": "state",
                    "data": self.state.toDict()
                }))
                
            elif msgType == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
                
        except json.JSONDecodeError:
            print(f"[Bridge] 無効なJSON: {message}")
        except Exception as e:
            print(f"[Bridge] メッセージ処理エラー: {e}")

    def _move(self, vx: float, vy: float, vyaw: float) -> None:
        """移動コマンド"""
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.Move(vx, vy, vyaw)
            except Exception as e:
                print(f"[Bridge] 移動エラー: {e}")
        
        # 状態更新
        self.state.velocityX = vx
        self.state.velocityY = vy
        self.state.velocityYaw = vyaw

    def _standUp(self) -> None:
        """立ち上がり"""
        print("[Bridge] コマンド: StandUp")
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.StandUp()
            except Exception as e:
                print(f"[Bridge] StandUpエラー: {e}")
        self.state.mode = "STAND"

    def _standDown(self) -> None:
        """伏せる"""
        print("[Bridge] コマンド: StandDown")
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.StandDown()
            except Exception as e:
                print(f"[Bridge] StandDownエラー: {e}")
        self.state.mode = "DOWN"

    def _balanceStand(self) -> None:
        """バランススタンド"""
        print("[Bridge] コマンド: BalanceStand")
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.BalanceStand()
            except Exception as e:
                print(f"[Bridge] BalanceStandエラー: {e}")

    def _recoveryStand(self) -> None:
        """リカバリースタンド"""
        print("[Bridge] コマンド: RecoveryStand")
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.RecoveryStand()
            except Exception as e:
                print(f"[Bridge] RecoveryStandエラー: {e}")

    def _stopMove(self) -> None:
        """移動停止"""
        print("[Bridge] コマンド: StopMove")
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.StopMove()
            except Exception as e:
                print(f"[Bridge] StopMoveエラー: {e}")
        self.state.velocityX = 0
        self.state.velocityY = 0
        self.state.velocityYaw = 0

    def _damp(self) -> None:
        """ダンプモード"""
        print("[Bridge] コマンド: Damp")
        if self.sportClient and not self.simulationMode:
            try:
                self.sportClient.Damp()
            except Exception as e:
                print(f"[Bridge] Dampエラー: {e}")
        self.state.mode = "IDLE"

    def _emergencyStop(self) -> None:
        """緊急停止"""
        print("[Bridge] ⚠️ 緊急停止!")
        self._stopMove()
        self._damp()

    def _stateLoop(self) -> None:
        """状態更新ループ"""
        import math
        
        while self.running:
            try:
                t = time.time()
                
                if self.simulationMode:
                    # シミュレーション用ダミーデータ
                    self.state.timestamp = t
                    self.state.connected = True
                    self.state.batteryLevel = max(20, 100 - int((t % 1000) / 10))
                    self.state.batteryVoltage = 25.0 + math.sin(t * 0.1) * 0.5
                    self.state.batteryCurrent = 2.0 + math.sin(t * 0.5) * 1.0
                    self.state.imuRoll = math.degrees(math.sin(t * 2) * 0.05)
                    self.state.imuPitch = math.degrees(math.sin(t * 1.5) * 0.03)
                    self.state.imuYaw = math.degrees(math.sin(t * 0.3) * 0.1)
                    self.state.imuGyro = [
                        math.cos(t * 2) * 0.1,
                        math.cos(t * 1.5) * 0.06,
                        math.cos(t * 0.3) * 0.2
                    ]
                    self.state.imuAccel = [
                        math.sin(t) * 0.5,
                        math.cos(t) * 0.3,
                        9.81 + math.sin(t * 3) * 0.1
                    ]
                    self.state.footContacts = [
                        (int(t * 2) + i) % 2 == 0 for i in range(4)
                    ]
                    self.state.footForces = [
                        50 + math.sin(t * 3 + i) * 20 if self.state.footContacts[i] else 0
                        for i in range(4)
                    ]
                else:
                    # 実際のSDK2から状態取得
                    self._updateRealState()
                
                # 接続中のクライアントに状態を配信
                asyncio.run(self._broadcastState())
                
                time.sleep(0.05)  # 20Hz
                
            except Exception as e:
                print(f"[Bridge] 状態更新エラー: {e}")
                time.sleep(0.1)

    def _updateRealState(self) -> None:
        """実際のSDK2から状態を取得"""
        # TODO: SDK2からの状態取得を実装
        pass

    async def _broadcastState(self) -> None:
        """全クライアントに状態を配信"""
        if not self.clients:
            return
        
        message = json.dumps({
            "type": "state",
            "data": self.state.toDict()
        })
        
        # 全クライアントに送信
        websockets_to_remove = set()
        for ws in self.clients:
            try:
                await ws.send(message)
            except:
                websockets_to_remove.add(ws)
        
        # 切断されたクライアントを削除
        self.clients -= websockets_to_remove


# ============================================================================
# メイン
# ============================================================================

def main():
    """メインエントリーポイント"""
    if not WEBSOCKETS_AVAILABLE:
        print("websocketsをインストールしてください: pip install websockets")
        return
    
    server = Go2BridgeServer()
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n[Bridge] サーバーを停止します...")


if __name__ == "__main__":
    main()

