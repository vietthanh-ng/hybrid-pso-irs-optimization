@echo off

echo [1/3] Kiem tra moi truong ao .venv...
if not exist ".venv" (
    echo Dang tao moi truong ao .venv...
    python -m venv .venv
)

echo [2/3] Kich hoat moi truong ao...
call .venv\Scripts\activate

echo [3/3] Kiem tra va cai dat thu vien...
pip install -q -r requirements.txt

echo ==========================================================
echo   Moi truong da san sang! Dang chay mo phong IRS...
echo ==========================================================
python hybrid_pso_nelder_mead_irs.py
pause
