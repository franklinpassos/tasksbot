import requests
import os
import json
from datetime import datetime

RUNRUN_APP_KEY = os.getenv('RUNRUN_APP_KEY')
RUNRUN_USER_TOKEN = os.getenv('RUNRUN_USER_TOKEN')

today = datetime.today().strftime('%Y-%m-%d')
url = f'https://runrun.it/api/v1.0/tasks?due_date={today}'

headers = {
    'App-Key': RUNRUN_APP_KEY,
    'User-Token': RUNRUN_USER_TOKEN,
    'Content-Type': 'application/json'
}

response = requests.get(url, headers=headers)
response.raise_for_status()
tasks = response.json()

if tasks:
    print('JSON completo da primeira tarefa:')
    print(json.dumps(tasks[0], indent=2, ensure_ascii=False))
else:
    print('Nenhuma tarefa encontrada para hoje.')
