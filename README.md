#запуск daemon
nohup python3 bot.py > bot.log 2>&1 &
#все команды в корне проекта

python -m venv venv 


pip install -r requirements.txt


python bot.py
