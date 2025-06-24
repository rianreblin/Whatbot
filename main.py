from flask import Flask, request, jsonify
import smtplib, re
from email.mime.text import MIMEText

app = Flask(__name__)

# 📧 Informações fixas para envio via Gmail SMTP
EMAIL_REMETENTE = "rianreblin@gmail.com"
SENHA_APP = "jijbhqsgcsgywkgk"  # senha de app (sem espaços)

usuarios = {}

def enviar_email(destino, assunto, corpo):
    if not EMAIL_REMETENTE or not SENHA_APP:
        return "⚠️ Variáveis de envio não configuradas corretamente."
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
        return f"❌ Erro ao enviar e-mail:\n{e}"

@app.route('/responder', methods=['POST'])
def responder():
    dados = request.get_json()
    query = dados.get("query", {})
    msg = query.get("message", "").strip()
    num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido"

    if num == "desconhecido":
        return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": ""}

    estado = usuarios[num]["estado"]
    resposta = "👋 Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola"

    if estado == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
            resposta = "📧 Qual e-mail de destino?"
        elif msg.lower() == "b":
            resposta = "📚 Horário escolar:\nSegunda a sexta: 08h às 17h"
        elif msg.lower() in ["oi", "olá", "menu"]:
            resposta = "👋 Olá! Escolha:\nA - Enviar e-mail\nB - Ver horário"
    elif estado == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "aguardando_mensagem"
            resposta = f"✉️ Digite a mensagem para enviar para {msg}."
        else:
            resposta = "⚠️ E-mail inválido. Digite um válido."
    elif estado == "aguardando_mensagem":
        destino = usuarios[num]["destino"]
        resultado = enviar_email(destino, "Mensagem via WhatsApp", msg)
        if resultado == True:
            resposta = f"✅ E-mail enviado com sucesso para {destino}!"
        else:
            resposta = resultado
        usuarios[num] = {"estado": "inicial", "destino": ""}

    return jsonify({"replies": [{"message": resposta}]})

@app.route('/')
def home():
    return 'Servidor WhatsAuto ativo ✅'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
