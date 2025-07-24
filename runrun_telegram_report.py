import requests
from datetime import datetime, time
import pytz
import os

RUNRUN_APP_KEY = os.getenv("RUNRUN_APP_KEY")
RUNRUN_USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_CHAT_ID_SECUNDARIO = os.getenv("TELEGRAM_CHAT_ID_SECUNDARIO")

HEADERS = {
    "App-Key": RUNRUN_APP_KEY,
    "User-Token": RUNRUN_USER_TOKEN
}

def get_all_tasks():
    url = "https://api.runrun.it/v1.0/tasks"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print("Erro ao buscar tarefas:", resp.text)
        return []
    
    if isinstance(resp.json(), list):
        return resp.json()  # Caso venha como lista direta

    return resp.json().get("data", [])  # Caso venha como dict com "data"

def parse_iso_datetime(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception as e:
        print(f"Erro ao converter data: {date_str} - {e}")
        return None

def get_today_tasks():
    brt = pytz.timezone("America/Sao_Paulo")
    now_brt = datetime.now(tz=brt)
    today_brt = now_brt.date()

    # Limites do dia em Brasília convertidos para UTC
    start_of_day_brt = datetime.combine(today_brt, time.min).replace(tzinfo=brt)
    end_of_day_brt = datetime.combine(today_brt, time.max).replace(tzinfo=brt)
    start_utc = start_of_day_brt.astimezone(pytz.UTC)
    end_utc = end_of_day_brt.astimezone(pytz.UTC)

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

        if start_utc <= desired_date <= end_utc and task.get("status") != "delivered":
            filtered_tasks.append(task)

    print(f"Total tarefas filtradas para hoje: {len(filtered_tasks)}")
    return filtered_tasks

def format_task_message(task):
    name = task.get("name", "Sem nome")
    user_name = task.get("user_name", "Sem responsável")
    client_name = task.get("client_name", "Sem cliente")
    project_name = task.get("project_name", "Sem projeto")
    status = task.get("task_status_name", "Sem status")
    return f"📌 *{name}*\n👤 {user_name}\n🏢 {client_name}\n📁 {project_name}\n📊 Status: *{status}*\n"

def send_telegram_message(message, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Erro ao enviar mensagem para chat {chat_id}: {response.text}")
    else:
        print(f"Mensagem enviada para chat {chat_id} com sucesso.")

def main():
    tasks = get_today_tasks()
    if not tasks:
        mensagem = "✅ Nenhuma tarefa pendente para hoje!"
    else:
        mensagem = f"*Tarefas para hoje ({datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y')}):*\n\n"
        for task in tasks:
            mensagem += format_task_message(task) + "\n"

    send_telegram_message(mensagem, TELEGRAM_CHAT_ID)

    if TELEGRAM_CHAT_ID_SECUNDARIO:
        send_telegram_message(mensagem, TELEGRAM_CHAT_ID_SECUNDARIO)

if __name__ == "__main__":
    main()
