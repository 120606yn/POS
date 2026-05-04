@echo off

chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
set FLASK_APP=app.py
set FLASK_ENV=development
docker exec -i restaurant-db mysql -u root -proot_password restaurant -e "
UPDATE staff SET password_hash = 'admin123' WHERE username = 'admin';
UPDATE staff SET password_hash = 'admin123' WHERE username = 'waiter1';
UPDATE staff SET password_hash = 'admin123' WHERE username = 'kitchen1';
\q
"

echo.
echo  =======================================
echo    OrderFlow Restaurant POS
echo    Dang khoi dong he thong...
echo  =======================================
echo.
echo  Web app: http://localhost:5000
echo  Nhan Ctrl+C de dung server
echo.

pip install -r requirements.txt -q

python -X utf8 app.py

pause
