def main():
    # Obtém o dicionário de usuários (id -> nome)
    user_dict = get_users()

    # Recupera todas as tarefas com desired_date para hoje
    tasks = get_today_tasks()

    # Ordena as tarefas por nome do projeto (para organização visual)
    tasks.sort(key=lambda t: t.get("project_name") or "")

    # Se não houver tarefas para hoje, envia uma mensagem informando isso
    if not tasks:
        send_to_telegram("✅ Nenhuma tarefa agendada para hoje.", chat_ids=[CHAT_ID, CHAT_ID_SECUNDARIO])
        return

    # Inicializa os blocos de mensagem
    # Um para tarefas com status "Prazo Solicitado" e outro para as demais
    message_prazo_solicitado = "<b>⚠️ Tarefas com 'Prazo Solicitado':</b>\n\n"
    message_outras = "<b>📋 Outras tarefas para hoje:</b>\n\n"

    # Itera por todas as tarefas filtradas
    for task in tasks:
        title = task.get("title") or "Sem título"

        # Define o(s) responsável(is) pela tarefa
        assignments = task.get("assignments") or []
        if assignments:
            responsible_names = ", ".join([a.get("assignee_name", "Desconhecido") for a in assignments])
        else:
            responsible_names = task.get("responsible_name") or task.get("user_name") or "Desconhecido"

        # Informações adicionais da tarefa
        project_name = task.get("project_name") or "Projeto não identificado"
        task_id = task.get("id")
        task_url = f"https://runrun.it/tasks/{task_id}" if task_id else "URL indisponível"
        status = task.get("task_status_name", "Status desconhecido")

        # Monta o bloco de texto HTML para a tarefa
        task_block = (
            f"📌 <b>{title}</b>\n"
            f"👤 Responsável: {responsible_names}\n"
            f"📂 Projeto: {project_name}\n"
            f"⚙️ Status: {status}\n"
            f"🔗 <a href=\"{task_url}\">Abrir tarefa</a>\n\n"
        )

        # Direciona para o grupo correto dependendo do status
        if status.lower() == "prazo solicitado":
            message_prazo_solicitado += task_block
        else:
            message_outras += task_block

    # Junta os blocos em uma única mensagem, com separação clara
    full_message = ""
    if message_prazo_solicitado.strip() != "<b>⚠️ Tarefas com 'Prazo Solicitado':</b>":
        full_message += message_prazo_solicitado
    if message_outras.strip() != "<b>📋 Outras tarefas para hoje:</b>":
        if full_message:
            full_message += "\n"  # separador visual entre os blocos
        full_message += message_outras

    # Envia a mensagem final para os chats configurados, dividindo caso ultrapasse o limite do Telegram
    split_and_send_message(full_message.strip(), chat_ids=[CHAT_ID, CHAT_ID_SECUNDARIO])
