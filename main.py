from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import smtplib
import os
import re
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo'

# Dados do e-mail
EMAIL_REMETENTE = "rianreblin@gmail.com"
SENHA_APP = "jijbhqsgcsgywkgk"

usuarios = {}
tarefas = []
historico = []

# Função para enviar e-mail
def enviar_email(destino, assunto, corpo):
    try:
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destino
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP)
            smtp.send_message(msg)
        return True
    except Exception as e:
        return str(e)

@app.route('/')
def home():
    return 'Servidor WhatsAuto ativo ✅'

@app.route('/responder', methods=['POST'])
def responder():
    dados = request.get_json()
    query = dados.get("query", {})
    msg = query.get("message", "").strip()
    num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido"

    historico.append({"numero": num, "mensagem": msg, "hora": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

    if num == "desconhecido":
        return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": ""}

    estado = usuarios[num]["estado"]
    resposta = "👋 Envie:\nA - Enviar e-mail\nB - Ver horário\n/tarefa - Ver tarefas"

    if msg == "/tarefa":
        if tarefas:
            resposta = "📝 Tarefas:\n" + "\n".join([f"📌 {t['texto']} - {t['dia']}" for t in tarefas])
        else:
            resposta = "📭 Nenhuma tarefa registrada."
    elif estado == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
