import requests
import os
from datetime import datetime, timedelta
import pytz  # IMPORTANTE: pip install pytz

APP_KEY = os.getenv("RUNRUN_APP_KEY")
USER_TOKEN = os.getenv("RUNRUN_USER_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Captura os chat IDs a partir de secrets
CHAT_ID_1 = os.getenv("TELEGRAM_CHAT_ID")
CHAT_ID_2 = os.getenv("TELEGRAM_CHAT_ID_2")

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
    users = users_data.get("data", []) if isinstance(users_data, dict) else users_data
    return {user["id"]: user["name"] for user in users}

def parse_iso_datetime(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(pytz.UTC) if dt.tzinfo else dt.replace(tzinfo=pytz.UTC)
    except:
        return None

def get_all_tasks():
    tasks, page, per_page = [], 1, 50
    while True:
        url = f"https://runrun.it/api/v1.0/tasks?page={page}&per_page={per_page}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Erro ao buscar tarefas na página {page}:", resp.text)
            break
        data = resp.json().get("data", [])
        if not data:
            break
        tasks.extend(data)
        page += 1
    return tasks

def get_today_tasks():
    brt = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz=brt)
    today, tomorrow = now.replace(hour=0,minute=0,second=0,microsecond=0), now.replace(hour=0,minute=0,second=0,microsecond=0) + timedelta(days=1)

    all_tasks = get_all_tasks()
    print(f"Total tarefas obtidas: {len(all_tasks)}")
    filtered = []
    for t in all_tasks:
        ds = parse_iso_datetime(t.get("desired_date") or "")
        if not ds:
            continue
        db = ds.astimezone(brt)
        if today <= db < tomorrow and t.get("status") != "delivered":
            filtered.append(t)
    print(f"Total tarefas filtradas para hoje: {len(filtered)}")
    return filtered

def send_to_all(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for cid in [CHAT_ID_1, CHAT_ID_2]:
        if not cid:
            continue
        resp = requests.post(url, json={"chat_id": cid, "text": message, "parse_mode": "HTML"})
        if resp.status_code != 200:
            print(f"❌ Erro ao enviar pra {cid}: {resp.text}")

def split_and_send(msg, max_len=4096):
    while len(msg) > max_len:
        idx = msg.rfind('\n', 0, max_len)
        if idx == -1:
            idx = max_len
        send_to_all(msg[:idx])
        msg = msg[idx:].lstrip()
    if msg:
        send_to_all(msg)

def main():
    if not all([APP_KEY, USER_TOKEN, BOT_TOKEN, CHAT_ID_1]):
        raise Exception("⚠️ Variável de ambiente faltando.")
    tasks = get_today_tasks()
    if not tasks:
        split_and_send("✅ Nenhuma tarefa agendada para hoje.")
        return

    msg = "<b>Tarefas para hoje:</b>\n\n"
    for t in tasks:
        title = t.get("title") or "Sem título"
        assigns = t.get("assignments") or []
        if assigns:
            resps = ", ".join(a.get("assignee_name","Desconhecido") for a in assigns)
        else:
            resps = t.get("responsible_name") or t.get("user_name") or "Desconhecido"
        proj = t.get("project_name") or "Projeto não identificado"
        url = t.get("id") and f"https://runrun.it/tasks/{t.get('id')}" or "URL indisponível"
        msg += f"📌 <b>{title}</b>\n👤 Responsável: {resps}\n📂 Projeto: {proj}\n🔗 <a href=\"{url}\">Abrir tarefa</a>\n\n"
    split_and_send(msg)

if __name__ == "__main__":
    main()
