import requests
from datetime import datetime
import os

# Tokens de ambiente (setar no GitHub Secrets depois)
RUNRUN_APP_KEY = os.getenv("RUNRUN_APP_KEY")
RUNRUN_USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Data de hoje no formato ISO
today = datetime.today().strftime('%Y-%m-%d')

# Endpoint de tasks com filtro por data de entrega
url = f"https://runrun.it/api/v1.0/tasks?due_date={today}"

headers = {
    "App-Key": RUNRUN_APP_KEY,
    "User-Token": RUNRUN_USER_TOKEN,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise Exception(f"Erro ao buscar tarefas: {response.status_code}")

tasks = response.json()

# Filtrar tarefas que estão abertas (status_id ≠ finalizado, por exemplo)
tarefas_abertas = [t for t in tasks if not t.get("completed_at")]

# Montar a mensagem
if tarefas_abertas:
    mensagem = f"📋 *Tarefas com entrega hoje ({today}):*\n\n"
    for t in tarefas_abertas:
        mensagem += f"- {t['name']} (Responsável: {t.get('user', {}).get('name', 'Desconhecido')})\n"
else:
    mensagem = f"✅ Nenhuma tarefa com entrega para hoje ({today})."

# Enviar para o Telegram
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

telegram_data = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": mensagem,
    "parse_mode": "Markdown"
}

telegram_response = requests.post(telegram_url, json=telegram_data)

if telegram_response.status_code != 200:
    raise Exception(f"Erro ao enviar mensagem no Telegram: {telegram_response.text}")
