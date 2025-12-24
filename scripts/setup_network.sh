#!/bin/bash
# =============================================================================
# Unitree Go2 ネットワーク接続テストスクリプト
# =============================================================================

GO2_IP="192.168.123.161"
JETSON_IP="192.168.123.18"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Unitree Go2 ネットワーク接続テスト                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Go2 MCUへの接続テスト
echo "🤖 Go2 MCU (${GO2_IP}) への接続テスト..."
if ping -c 3 -t 2 $GO2_IP > /dev/null 2>&1; then
    echo "   ✅ Go2 MCU: 接続OK"
    GO2_OK=true
else
    echo "   ❌ Go2 MCU: 接続失敗"
    GO2_OK=false
fi

echo ""

# Jetsonへの接続テスト
echo "💻 Jetson (${JETSON_IP}) への接続テスト..."
if ping -c 3 -t 2 $JETSON_IP > /dev/null 2>&1; then
    echo "   ✅ Jetson: 接続OK"
    JETSON_OK=true
else
    echo "   ⚠️  Jetson: 接続失敗（オプション）"
    JETSON_OK=false
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$GO2_OK" = true ]; then
    echo "🎉 Go2への接続準備完了！"
    echo ""
    echo "アプリを起動してください:"
    echo "  python main.py"
    echo ""
    echo "IPアドレス: ${GO2_IP}"
else
    echo "⚠️  Go2に接続できません。以下を確認してください:"
    echo ""
    echo "1. Go2の電源がONになっていますか？"
    echo "2. 以下のいずれかで接続してください:"
    echo ""
    echo "   【方法A: WiFi接続】"
    echo "   - MacのWiFiで「Unitree_GoXXXX」に接続"
    echo "   - パスワード: Go2本体に記載"
    echo ""
    echo "   【方法B: 有線LAN接続】"
    echo "   - Go2背面のイーサネットポートに接続"
    echo "   - Macのネットワーク設定:"
    echo "     IP: 192.168.123.100"
    echo "     サブネット: 255.255.255.0"
    echo ""
fi

