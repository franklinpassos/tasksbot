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
    users = users_data.get("data", users_data) if isinstance(users_data, dict) else users_data
    return {user["id"]: user["name"] for user in users}

def parse_iso_datetime(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(pytz.UTC) if dt.tzinfo else dt.replace(tzinfo=pytz.UTC)
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
        data = tasks_data.get("data", tasks_data) if isinstance(tasks_data, dict) else tasks_data
        if not data:
            break
        tasks.extend(data)
        page += 1
    return tasks

def get_today_tasks():
    brt = pytz.timezone("America/Sao_Paulo")
    now_brt = datetime.now(tz=brt)
    today = now_brt.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    all_tasks = get_all_tasks()
    print(f"Total tarefas obtidas: {len(all_tasks)}")

    filtered_tasks = []
    for task in all_tasks:
        desired_date_str = task.get("desired_date_with_time")
        if not desired_date_str:
            continue
        desired_date = parse_iso_datetime(desired_date_str)
        if not desired_date:
            continue
        desired_date_brt = desired_date.astimezone(brt)
        if today <= desired_date_brt < tomorrow and task.get("task_status_name", "").lower() != "delivered":
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
            "parse_mode": "HTML",
            "disable_web_page_preview": True
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

def format_task_message(task):
    title = task.get("title") or "Sem título"
    assignments = task.get("assignments") or []
    responsible_names = ", ".join([a.get("assignee_name", "Desconhecido") for a in assignments]) if assignments else (
        task.get("responsible_name") or task.get("user_name") or "Desconhecido")
    project_name = task.get("project_name") or "Projeto não identificado"
    task_id = task.get("id")
    task_url = f"https://runrun.it/tasks/{task_id}" if task_id else "URL indisponível"
    status = task.get("task_status_name", "Status desconhecido")

    return (
        f"📌 <b>{title}</b>\n"
        f"👤 Responsável: {responsible_names}\n"
        f"📂 Projeto: {project_name}\n"
        f"⚙️ Status: {status}\n"
        f"🔗 <a href=\"{task_url}\">Abrir tarefa</a>\n\n"
    )

def main():
    user_dict = get_users()
    tasks = get_today_tasks()
    tasks.sort(key=lambda t: t.get("project_name") or "")

    if not tasks:
        send_to_telegram("✅ Nenhuma tarefa agendada para hoje.", chat_ids=[CHAT_ID, CHAT_ID_SECUNDARIO])
        return

    solicitado_tasks = [t for t in tasks if "prazo solicitado" in t.get("task_status_name", "").lower()]
    outras_tasks = [t for t in tasks if t not in solicitado_tasks]

    message = "<b>Tarefas para hoje:</b>\n\n"

    if solicitado_tasks:
        message += "<b>⏳ Tarefas com Prazo Solicitado:</b>\n\n"
        for task in solicitado_tasks:
            message += format_task_message(task)

    if outras_tasks:
        message += "<b>📋 Outras tarefas:</b>\n\n"
        for task in outras_tasks:
            message += format_task_message(task)

    split_and_send_message(message.strip(), chat_ids=[CHAT_ID, CHAT_ID_SECUNDARIO])
    print(f"Total tarefas incluídas na mensagem: {len(solicitado_tasks) + len(outras_tasks)}")

if __name__ == "__main__":
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID, CHAT_ID_SECUNDARIO]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    main()
