import requests
from datetime import datetime
import os

RUNRUN_APP_KEY = os.getenv("RUNRUN_APP_KEY")
RUNRUN_USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([RUNRUN_APP_KEY, RUNRUN_USER_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise Exception("Algum token ou variável de ambiente está faltando!")

today = datetime.today().strftime('%Y-%m-%d')
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
tarefas_abertas = [t for t in tasks if not t.get("completed_at")]

def obter_responsavel(tarefa):
    # Tenta pegar o responsável por vários campos possíveis
    if tarefa.get("user") and tarefa["user"].get("name"):
        return tarefa["user"]["name"]
    elif tarefa.get("assignee") and tarefa["assignee"].get("name"):
        return tarefa["assignee"]["name"]
    elif tarefa.get("assigned_to") and tarefa["assigned_to"].get("name"):
        return tarefa["assigned_to"]["name"]
    elif tarefa.get("allocated_user") and tarefa["allocated_user"].get("name"):
        return tarefa["allocated_user"]["name"]
    else:
        return "Desconhecido"

if tarefas_abertas:
    mensagem = f"📋 *Tarefas com entrega para hoje ({today}):*\n\n"
    for t in tarefas_abertas:
        nome = t.get("name") or t.get("title") or "Sem nome"
        responsavel = obter_responsavel(t)
        mensagem += f"- {nome} (Responsável: {responsavel})\n"
else:
    mensagem = f"✅ Nenhuma tarefa com entrega para hoje ({today})."

MAX_TELEGRAM_MSG_LENGTH = 4000

def enviar_mensagem(texto):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }
    resp = requests.post(telegram_url, json=telegram_data)
    if resp.status_code != 200:
        raise Exception(f"Erro ao enviar mensagem no Telegram: {resp.text}")

def dividir_mensagem(texto, max_len=MAX_TELEGRAM_MSG_LENGTH):
    partes = []
    while len(texto) > max_len:
        corte = texto.rfind('\n', 0, max_len)
        if corte == -1:
            corte = max_len
        partes.append(texto[:corte])
        texto = texto[corte:].lstrip('\n')
    partes.append(texto)
    return partes

partes = dividir_mensagem(mensagem)
for i, parte in enumerate(partes):
    enviar_mensagem(parte)
    print(f"Enviada parte {i+1}/{len(partes)}")

print("Todas as mensagens enviadas com sucesso!")
