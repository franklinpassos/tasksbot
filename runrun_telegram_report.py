import requests
from datetime import datetime
import os

# Pega tokens e chat id dos secrets / variáveis ambiente
RUNRUN_APP_KEY = os.getenv("RUNRUN_APP_KEY")
RUNRUN_USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([RUNRUN_APP_KEY, RUNRUN_USER_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise Exception("Algum token ou variável de ambiente está faltando!")

# Data de hoje (formato ISO yyyy-mm-dd)
today = datetime.today().strftime('%Y-%m-%d')

# URL da API Runrun.it com filtro de data de entrega igual a hoje
url = f"https://runrun.it/api/v1.0/tasks?due_date={today}"

headers = {
    "App-Key": RUNRUN_APP_KEY,
    "User-Token": RUNRUN_USER_TOKEN,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise Exception(f"Erro ao buscar tarefas: {response.status_code} - {response.text}")

tasks = response.json()

# Filtrar tarefas abertas (exemplo: sem 'completed_at')
tarefas_abertas = [t for t in tasks if not t.get("completed_at")]

if tarefas_abertas:
    mensagem = f"📋 *Tarefas com entrega para hoje ({today}):*\n\n"
    for t in tarefas_abertas:
        nome = t.get("name") or t.get("title") or "Sem nome"
        responsavel = t.get("user", {}).get("name", "Desconhecido")
        mensagem += f"- {nome} (Responsável: {responsavel})\n"
else:
    mensagem = f"✅ Nenhuma tarefa com entrega para hoje ({today})."

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
telegram_data = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": mensagem,
    "parse_mode": "Markdown"
}

telegram_response = requests.post(telegram_url, json=telegram_data)

if telegram_response.status_code != 200:
    raise Exception(f"Erro ao enviar mensagem no Telegram: {telegram_response.text}")

print("Mensagem enviada com sucesso!")
