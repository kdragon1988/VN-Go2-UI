"""
Unitree Go2 コマンド定数

ファームウェア v1.1.7+ (MCF統合モード) 対応

参考:
- https://github.com/legion1581/unitree_webrtc_connect
- Discord: TheRoboVerse community

MCFモード:
- v1.1.7からAIモードとノーマルモードが統合された
- トピック "SPORT_MOD" で制御可能
"""

from enum import IntEnum


class RtcTopic:
    """
    WebRTC データチャンネルトピック
    
    Go2との通信で使用するトピック名
    """
    SPORT_MOD = "rt/api/sport/request"           # スポーツモードAPI
    OBSTACLES_AVOID = "rt/api/obstacles_avoid/request"  # 障害物回避API
    LOW_STATE = "rt/lf/lowstate"                  # ローレベル状態
    SPORT_STATE = "rt/sportmodestate"             # スポーツモード状態
    LIDAR = "rt/utlidar/cloud"                    # LiDAR点群
    AUDIO = "rt/audio/pcm"                        # オーディオ


class SportCmd(IntEnum):
    """
    スポーツモードコマンドID (MCF対応)
    
    SPORT_MOD トピックで使用するapi_id
    
    参考: unitree_webrtc_connect/constants.py
    """
    # 基本動作
    DAMP = 0                  # 脱力モード
    BALANCE_STAND = 1         # バランススタンド
    STOP_MOVE = 2             # 移動停止
    STAND_UP = 3              # 立ち上がり
    STAND_DOWN = 4            # 伏せる
    RECOVERY_STAND = 5        # 転倒復帰
    
    # 移動
    MOVE = 1008               # 移動 (x, y, z)
    
    # 姿勢制御
    POSE = 1005               # ポーズモード開始（Euler前に必要）
    EULER = 1006              # 姿勢角度設定 (roll, pitch, yaw)
    BODY_HEIGHT = 1009        # 体高設定 (height)
    
    # 歩行モード
    SWITCH_GAIT = 1011        # 歩行切り替え
    SPEED_LEVEL = 1015        # 速度レベル設定
    
    # 特殊動作 - parameter: {"data": True} が必要
    FRONT_JUMP = 2001         # 前方ジャンプ
    FRONT_POUNCE = 2002       # 前方突進
    DANCE_1 = 2003            # ダンス1
    DANCE_2 = 2004            # ダンス2
    STRETCH = 2005            # ストレッチ
    SIT = 2006                # お座り
    PRONE = 2007              # 伏せ
    FRONT_FLIP = 2008         # 前方宙返り
    BACK_FLIP = 2009          # バック宙返り ★
    LEFT_FLIP = 2010          # 左宙返り
    RIGHT_FLIP = 2011         # 右宙返り
    BARK = 2012               # 吠える
    FINGER_HEART = 2020       # ハートマーク
    GREETING = 2022           # 挨拶
    HAND_STAND = 2023         # 逆立ち
    CROSS_STEP = 2024         # クロスステップ
    SHAKE_HAND = 2025         # 握手
    CROUCH = 2026             # しゃがむ
    HIGH_FIVE = 2027          # ハイタッチ
    WAVE_HAND = 2028          # 手を振る
    NAP = 2029                # 昼寝
    ZOMBIE = 2030             # ゾンビ
    WIGGLE_HIPS = 2031        # お尻フリフリ
    
    # MCF専用 (v1.1.7+)
    # AIモードとノーマルモードが統合
    
    
class ObstacleAvoidCmd(IntEnum):
    """
    障害物回避コマンドID
    
    OBSTACLES_AVOID トピックで使用するapi_id
    
    重要: 通常のMoveでは障害物回避が効かない！
          障害物回避を使う場合はこのトピックのMoveを使う
    """
    SWITCH = 1001             # 障害物回避ON/OFF {"enable": True/False}
    MOVE = 1002               # 障害物回避付き移動 {"x": 0, "y": 0, "z": 0}


class GaitType(IntEnum):
    """歩行タイプ"""
    IDLE = 0                  # アイドル
    WALK = 1                  # 歩行
    TROT = 2                  # トロット
    RUN = 3                   # 走行
    CLIMB = 4                 # 階段


class SpeedLevel(IntEnum):
    """速度レベル"""
    LOW = 0                   # 低速
    MEDIUM = 1                # 中速
    HIGH = 2                  # 高速


# コマンドパラメータのヘルパー

def move_params(x: float, y: float, yaw: float) -> dict:
    """移動パラメータを生成"""
    return {"x": x, "y": y, "z": yaw}

def euler_params(roll: float, pitch: float, yaw: float) -> dict:
    """姿勢パラメータを生成"""
    return {"roll": roll, "pitch": pitch, "yaw": yaw}

def special_action_params() -> dict:
    """特殊動作パラメータ（バックフリップ等に必要）"""
    return {"data": True}

def obstacle_avoid_params(enable: bool) -> dict:
    """障害物回避ON/OFFパラメータ"""
    return {"enable": enable}

