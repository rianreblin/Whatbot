from flask import Flask, request, jsonify
import smtplib, os, re
from email.mime.text import MIMEText

app = Flask(__name__)

# Variáveis de ambiente (defina no sistema ou substitua por valores diretos)
EMAIL_REMETENTE = os.getenv("rianreblin@gmail.com")  # Ex: "seuemail@gmail.com"
SENHA_APP = os.getenv("sckt ujqr fkcu oujq")              # Ex: senha gerada pelo Google

# Controle de estado por usuário
usuarios = {}

# Função para enviar o e-mail
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
        print("❌ Erro ao enviar e-mail:", e)
        return False

# Rota principal do bot
@app.route('/responder', methods=['POST'])
def responder():
    dados = request.get_json()
    print("📥 JSON recebido:", dados)

    query = dados.get("query", {})
    msg = query.get("message", "").strip()
    num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido"

    if num == "desconhecido":
        return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado. Verifique o JSON enviado."}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": ""}

    estado = usuarios[num]["estado"]
    resposta = "👋 Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola"

    if estado == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
            resposta = "📧 Para qual e-mail você quer enviar a mensagem?"
        elif msg.lower() == "b":
            resposta = "📚 Horário escolar:\nSegunda a sexta: 08h às 17h"
        elif msg.lower() in ["oi", "olá", "menu"]:
            resposta = "👋 Bem-vindo! Escolha uma opção:\nA - Enviar e-mail\nB - Ver horário"
    elif estado == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "aguardando_mensagem"
            resposta = f"✉️ Agora digite a mensagem que deseja enviar para {msg}."
        else:
            resposta = "⚠️ E-mail inválido. Por favor, digite um e-mail válido."
    elif estado == "aguardando_mensagem":
        destino = usuarios[num]["destino"]
        sucesso = enviar_email(destino, "Mensagem via WhatsApp", msg)
        if sucesso:
            resposta = f"✅ E-mail enviado com sucesso para {destino}!"
        else:
            resposta = "❌ Ocorreu um erro ao enviar o e-mail. Tente novamente mais tarde."
        usuarios[num] = {"estado": "inicial", "destino": ""}

    return jsonify({"replies": [{"message": resposta}]})

# Rota simples para saber se o servidor está ativo
@app.route('/')
def home():
    return 'Servidor WhatsAuto ativo ✅'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
