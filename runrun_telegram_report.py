import requests
import os
from datetime import datetime, timezone

APP_KEY = os.getenv("RUNRUN_APP_KEY")
USER_TOKEN = os.getenv("USER_TOKEN")
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

def dividir_mensagem(texto, limite=4000):
    partes = []
    while len(texto) > limite:
        corte = texto.rfind("\n", 0, limite)
        if corte == -1:
            corte = limite
        partes.append(texto[:corte])
        texto = texto[corte:]
    partes.append(texto)
    return partes

def main():
    user_dict = get_users()
    tasks = get_today_tasks()

    # Filtrar tarefas com status diferente de "delivered" ou "completed"
    tarefas_nao_entregues = [
        task for task in tasks
        if task.get("status") not in ["delivered", "completed"]
    ]

    if not tarefas_nao_entregues:
        send_to_telegram("✅ Nenhuma tarefa *não entregue* agendada para hoje.")
        return

    message = "<b>Tarefas não entregues para hoje:</b>\n\n"
    for task in tarefas_nao_entregues:
        title = task.get("subject", "Sem título")

        responsible_id = task.get("responsible_id")
        responsible = user_dict.get(responsible_id, "Desconhecido")

        raw_due_date = task.get("due_date") or task.get("deadline")
        if raw_due_date:
            try:
                due_date = datetime.strptime(raw_due_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                due_date = raw_due_date
        else:
            due_date = "Sem data"

        message += f"📌 <b>{title}</b>\n👤 Responsável: {responsible}\n📅 Vencimento: {due_date}\n\n"

    partes = dividir_mensagem(message)
    for parte in partes:
        send_to_telegram(parte)

if __name__ == "__main__":
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    main()
