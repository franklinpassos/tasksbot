import requests
import os
from datetime import datetime, timedelta, timezone

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

    users_data = response.json()
    if isinstance(users_data, dict):
        users = users_data.get("data", [])
    else:
        users = users_data

    return {user["id"]: user["name"] for user in users}

def parse_iso_datetime(date_str):
    # Tenta converter string ISO 8601 para datetime com timezone UTC
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None

def get_today_tasks():
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    url = f"https://runrun.it/api/v1.0/tasks"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("Erro ao buscar tarefas:", response.text)
        return []

    tasks_data = response.json()
    if isinstance(tasks_data, dict):
        tasks = tasks_data.get("data", [])
    else:
        tasks = tasks_data

    filtered_tasks = []
    for task in tasks:
        if task.get("status") == "delivered":
            continue
        desired_date_str = task.get("desired_date")
        if not desired_date_str:
            continue
        desired_date = parse_iso_datetime(desired_date_str)
        if not desired_date:
            continue
        # Filtra desired_date >= hoje 0h UTC e < amanhã 0h UTC
        if today <= desired_date < tomorrow:
            filtered_tasks.append(task)

    return filtered_tasks

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

def split_and_send_message(full_message, max_length=4096):
    while len(full_message) > max_length:
        split_point = full_message.rfind('\n', 0, max_length)
        if split_point == -1:
            split_point = max_length
        send_to_telegram(full_message[:split_point])
        full_message = full_message[split_point:].lstrip()
    if full_message:
        send_to_telegram(full_message)

def main():
    user_dict = get_users()
    tasks = get_today_tasks()

    if not tasks:
        send_to_telegram("✅ Nenhuma tarefa agendada para hoje.")
        return

    message = "<b>Tarefas para hoje:</b>\n\n"
    for task in tasks:
        title = task.get("name") or task.get("title") or "Sem título"
        responsible_id = task.get("user_id")
        responsible = user_dict.get(responsible_id, "Desconhecido")
        task_id = task.get("id")
        task_url = f"https://runrun.it/tasks/{task_id}" if task_id else "URL indisponível"
        message += f"📌 <b>{title}</b>\n👤 Responsável: {responsible}\n🔗 <a href=\"{task_url}\">Abrir tarefa</a>\n\n"

    split_and_send_message(message)

if __name__ == "__main__":
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    main()
