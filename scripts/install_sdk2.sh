#!/bin/bash
# =============================================================================
# Unitree SDK2 Python インストールスクリプト（Mac用）
# =============================================================================

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Unitree SDK2 Python インストール                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 仮想環境のアクティベート確認
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  仮想環境がアクティベートされていません"
    echo "   以下のコマンドを実行してください:"
    echo ""
    echo "   source venv/bin/activate"
    echo ""
    exit 1
fi

echo "📦 CycloneDDS のインストール..."
pip install cyclonedds

echo ""
echo "📦 unitree_sdk2py のインストール..."

# PyPIから試行
pip install unitree_sdk2py 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  PyPIからのインストールに失敗しました"
    echo "   GitHubから直接インストールを試みます..."
    echo ""
    
    # GitHubから直接インストール
    pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# インストール確認
python -c "import cyclonedds; print('✅ CycloneDDS:', cyclonedds.__version__)" 2>/dev/null || echo "❌ CycloneDDS: インストール失敗"

python -c "
try:
    from unitree_sdk2py.core.channel import ChannelFactory
    print('✅ unitree_sdk2py: インストール成功')
except ImportError as e:
    print(f'⚠️  unitree_sdk2py: {e}')
    print('   シミュレーションモードで動作します')
"

echo ""
echo "インストール完了！"
echo ""
echo "次のステップ:"
echo "  1. ./scripts/setup_network.sh でネットワーク確認"
echo "  2. python main.py でアプリ起動"

