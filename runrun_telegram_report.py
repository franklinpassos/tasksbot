import requests
from datetime import datetime, timedelta
import pytz
import os

RUNRUN_APP_KEY = os.getenv("RUNRUN_APP_KEY")
RUNRUN_USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "App-Key": RUNRUN_APP_KEY,
    "User-Token": RUNRUN_USER_TOKEN
}

def get_all_tasks():
    tasks = []
    page = 1
    per_page = 50

    while True:
        url = f"https://runrun.it/api/v1.0/tasks?page={page}&per_page={per_page}"
        resp = requests.get(url, headers=HEADERS)

        if resp.status_code != 200:
            print(f"Erro ao buscar tarefas na página {page}:", resp.text)
            break

        response_data = resp.json()

        if isinstance(response_data, dict) and "data" in response_data:
            data = response_data["data"]
        elif isinstance(response_data, list):
            data = response_data
        else:
            print(f"Formato inesperado de resposta na página {page}: {response_data}")
            break

        if not data:
            break

        tasks.extend(data)
        page += 1

    return tasks

def get_today_tasks():
    tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz).date()
    tomorrow = now + timedelta(days=1)

    all_tasks = get_all_tasks()

    today_tasks = []
    for task in all_tasks:
        if task.get("desired_date"):
            task_date = datetime.strptime(task["desired_date"], "%Y-%m-%d").date()
            if task_date < tomorrow:
                today_tasks.append(task)
    return today_tasks

def format_task(task):
    title = task.get("title", "Sem título")
    responsaveis = [r.get("name", "Desconhecido") for r in task.get("responsibles", [])]
    responsavel_str = ", ".join(responsaveis) if responsaveis else "Desconhecido"
    projeto = task.get("project", {}).get("name", "Desconhecido")
    link = f'https://runrun.it/tasks/{task.get("id")}'
    
    return f"📌 {title}\n👤 Responsável: {responsavel_str}\n📂 Projeto: {projeto}\n🔗 [Abrir tarefa]({link})"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        print("Erro ao enviar mensagem para o Telegram:", resp.text)

def main():
    tasks = get_today_tasks()
    if not tasks:
        send_to_telegram("✅ Nenhuma tarefa prevista para hoje.")
    else:
        mensagens = [format_task(task) for task in tasks]
        mensagem_final = "\n\n".join(mensagens)
        send_to_telegram(f"📋 *Tarefas previstas até hoje:*\n\n{mensagem_final}")

if __name__ == "__main__":
    main()
