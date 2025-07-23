import requests
import os
from datetime import datetime, timedelta
import pytz  # IMPORTANTE: pip install pytz

APP_KEY = os.getenv("RUNRUN_APP_KEY")
USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHAT_ID_SECUNDARIO = os.getenv("TELEGRAM_CHAT_ID_SECUNDARIO")

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
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt
    except Exception:
        return None

def get_all_tasks():
    tasks = []
    page = 1
    per_page = 50

    while True:
        url = f"https://runrun.it/api/v1.0/tasks?page={page}&per_page={per_page}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Erro ao buscar tarefas na página {page}:", response.text)
            break

        tasks_data = response.json()
        if isinstance(tasks_data, dict):
            data = tasks_data.get("data", [])
        else:
            data = tasks_data

        if not data:
            break

        tasks.extend(data)
        page += 1

    return tasks

def get_today_tasks():
    brt = pytz.timezone("America/Sao_Paulo")
    now_brt = datetime.now(tz=brt)
    today_date = now_brt.date()

    all_tasks = get_all_tasks()
    print(f"Total tarefas obtidas: {len(all_tasks)}")

    filtered_tasks = []
    for task in all_tasks:
        desired_date_str = task.get("desired_date")
        if not desired_date_str:
            continue
        desired_date = parse_iso_datetime(desired_date_str)
        if not desired_date:
            continue

        # Não converte para timezone novamente, só pega a data local do datetime com fuso
        desired_date_local = desired_date.date()

        if desired_date_local == today_date and task.get("status") != "delivered":
            filtered_tasks.append(task)

    print(f"Total tarefas filtradas para hoje: {len(filtered_tasks)}")
    return filtered_tasks

def send_to_telegram(message, chat_ids=None):
    if chat_ids is None:
        chat_ids = [CHAT_ID]
    elif isinstance(chat_ids, str):
        chat_ids = [chat_ids]

    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Erro ao enviar mensagem para o Telegram (chat_id: {chat_id}):", response.text)

def split_and_send_message(full_message, max_length=4096, chat_ids=None):
    while len(full_message) > max_length:
        split_point = full_message.rfind('\n', 0, max_length)
        if split_point == -1:
            split_point = max_length
        send_to_telegram(full_message[:split_point], chat_ids=chat_ids)
        full_message = full_message[split_point:].lstrip()
    if full_message:
        send_to_telegram(full_message, chat_ids=chat_ids)

def main():
    user_dict = get_users()
    tasks = get_today_tasks()

    if not tasks:
        send_to_telegram("✅ Nenhuma tarefa agendada para hoje.", chat_ids=[CHAT_ID, CHAT_ID_SECUNDARIO])
        return

    message = "<b>Tarefas para hoje:</b>\n\n"
    for task in tasks:
        title = task.get("title") or "Sem título"

        assignments = task.get("assignments") or []
        if assignments:
            responsible_names = ", ".join([a.get("assignee_name", "Desconhecido") for a in assignments])
        else:
            responsible_names = task.get("responsible_name") or task.get("user_name") or "Desconhecido"

        project_name = task.get("project_name") or "Projeto não identificado"
        task_id = task.get("id")
        task_url = f"https://runrun.it/tasks/{task_id}" if task_id else "URL indisponível"

        message += (
            f"📌 <b>{title}</b>\n"
            f"👤 Responsável: {responsible_names}\n"
            f"📂 Projeto: {project_name}\n"
            f"🔗 <a href=\"{task_url}\">Abrir tarefa</a>\n\n"
        )

    split_and_send_message(message, chat_ids=[CHAT_ID, CHAT_ID_SECUNDARIO])

if __name__ == "__main__":
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID, CHAT_ID_SECUNDARIO]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    main()
