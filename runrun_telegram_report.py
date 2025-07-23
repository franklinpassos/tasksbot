import requests
import os
from datetime import datetime, timezone

APP_KEY = os.getenv("RUNRUN_APP_KEY")
USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "App-Key": APP_KEY,
    "User-Token": USER_TOKEN,
    "Content-Type": "application/json"
}

def get_users():
    url = "https://runrun.it/api/v1.0/users"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("Erro ao buscar usuários:", response.text)
        return {}
    users = response.json()
    return {user["id"]: user["name"] for user in users}

def get_today_tasks():
    today = datetime.now(timezone.utc).date().isoformat()
    url = f"https://runrun.it/api/v1.0/tasks?due_date={today}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("Erro ao buscar tarefas:", response.text)
        return []
    return response.json()

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("Erro ao enviar mensagem para o Telegram:", response.text)

def main():
    user_dict = get_users()
    tasks = get_today_tasks()

    if not tasks:
        send_to_telegram("✅ Nenhuma tarefa agendada para hoje.")
        return

    message = "<b>Tarefas para hoje:</b>\n\n"
    for task in tasks:
        title = task.get("name", "Sem título")
        responsible_id = task.get("responsible_id")
        responsible = user_dict.get(responsible_id, "Desconhecido")
        due_date = task.get("due_date", "Sem data")
        message += f"📌 <b>{title}</b>\n👤 Responsável: {responsible}\n📅 Vencimento: {due_date}\n\n"

    send_to_telegram(message)

if __name__ == "__main__":
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    main()
