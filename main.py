#!/usr/bin/env python3
"""
Unitree Go2 Controller for macOS

サイバーパンク風UIを搭載したUnitree Go2制御アプリケーション

主な機能:
- Xbox互換コントローラーによる直感的操作
- リアルタイム機体情報表示（バッテリー、IMU、関節状態）
- カメラ映像のライブストリーミング
- 同一LAN経由でのGo2との通信
- サイバーパンク風ダッシュボードUI

使用方法:
    python main.py

制限事項:
- Go2 EDUエディション専用
- macOS 12.0以上
- Python 3.10以上
- 同一LANネットワーク接続が必要

依存パッケージ:
- PySide6
- pygame
- unitree_sdk2py
- opencv-python
- numpy
"""

import sys
import os

# パスの追加（srcモジュールをインポート可能にする）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    """
    メインエントリーポイント

    Returns:
        int: 終了コード（0: 正常終了, 1: エラー終了）
    """
    try:
        # 環境変数設定（macOSでのOpenGL問題回避）
        os.environ["QT_MAC_WANTS_LAYER"] = "1"
        
        # アプリケーション作成
        from src.app import createApplication
        app, controllerApp = createApplication()

        # 初期化
        if not controllerApp.initialize():
            print("[Error] アプリケーションの初期化に失敗しました")
            return 1

        # 実行
        exitCode = controllerApp.run()
        if exitCode != 0:
            return exitCode

        # イベントループ開始
        result = app.exec()

        # クリーンアップ
        controllerApp.cleanup()

        return result

    except ImportError as e:
        print(f"[Error] 必要なモジュールがインストールされていません: {e}")
        print("\n以下のコマンドで依存パッケージをインストールしてください:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"[Error] 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

