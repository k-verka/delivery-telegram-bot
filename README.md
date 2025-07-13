#запуск daemon
nohup python3 bot.py > bot.log 2>&1 &
#начало
python -m venv venv 
pip install -r requirements.txt
