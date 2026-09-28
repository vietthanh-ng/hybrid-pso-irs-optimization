#!/bin/bash
# -----------------------------------------------------------------------------
# Tự động khởi tạo môi trường ảo (Virtual Environment) và chạy dự án
# -----------------------------------------------------------------------------

set -e

# Kiểm tra python3 hoặc python
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[Lỗi] Không tìm thấy Python trên máy tính. Vui lòng cài đặt Python 3.8+."
    exit 1
fi

# Tạo môi trường ảo .venv nếu chưa tồn tại
if [ ! -d ".venv" ]; then
    echo "[1/3] Đang khởi tạo môi trường ảo .venv..."
    $PY_CMD -m venv .venv
else
    echo "[1/3] Đã phát hiện môi trường ảo .venv."
fi

# Kích hoạt môi trường ảo
echo "[2/3] Kích hoạt môi trường ảo..."
source .venv/bin/activate

# Cài đặt thư viện cần thiết
echo "[3/3] Kiểm tra và cài đặt thư viện từ requirements.txt..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "=========================================================="
echo "  Môi trường đã sẵn sàng! Đang khởi chạy mô phỏng IRS...  "
echo "=========================================================="
python hybrid_pso_nelder_mead_irs.py
