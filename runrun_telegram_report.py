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
    users_data = response.json()
    # Se a resposta for um dict com chave 'data', use-a; senão, use a lista diretamente
    users_list = users_data.get("data", users_data) if isinstance(users_data, dict) else users_data
    return {user["id"]: user["name"] for user in users_list}

def get_today_tasks():
    url = "https://runrun.it/api/v1.0/tasks"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("Erro ao buscar tarefas:", response.text)
        return []

    tasks_data = response.json()
    tasks_list = tasks_data.get("data", tasks_data) if isinstance(tasks_data, dict) else tasks_data

    today = datetime.now(timezone.utc).date().isoformat()

    filtered_tasks = []
    for task in tasks_list:
        desired_date = task.get("desired_date")
        status = task.get("status")
        if desired_date == today and status != "delivered":
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
    # Divide a mensagem em blocos menores e envia um por um
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
        title = task.get("name") or "Sem título"
        responsible_id = task.get("user_id") or task.get("responsible_id")
        responsible = user_dict.get(responsible_id, "Desconhecido")
        task_id = task.get("id")
        url_task = f"https://app.runrun.it/tasks/{task_id}" if task_id else "URL indisponível"
        message += f"📌 <b>{title}</b>\n👤 Responsável: {responsible}\n🔗 <a href=\"{url_task}\">Ver Task</a>\n\n"

    split_and_send_message(message)

if __name__ == "__main__":
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    main()
