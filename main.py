from flask import Flask, request, jsonify
import smtplib, os, re
from email.mime.text import MIMEText

app = Flask(__name__)

EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")

usuarios = {}

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
        print("Erro ao enviar e-mail:", e)
        return False

@app.route('/responder', methods=['POST'])
def responder():
    dados = request.get_json()
    msg = dados.get("message", "").strip()
    num = dados.get("number", "")
    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": ""}
    est = usuarios[num]["estado"]
    r = "Envie 'A' para enviar e-mail ou 'B' para ver horário."
    if est == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
            r = "Para qual e-mail deseja enviar a mensagem?"
        elif msg.lower() == "b":
            r = "Horário: Segunda a sexta, das 8h às 17h."
        elif msg.lower() in ["oi", "olá"]:
            r = "Olá! Escolha uma opção:\nA - Enviar e-mail\nB - Ver horário"
    elif est == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "aguardando_mensagem"
            r = f"Ok! Agora digite a mensagem que deseja enviar para {msg}"
        else:
            r = "E-mail inválido. Por favor, digite um e-mail válido."
    else:
        destino = usuarios[num]["destino"]
        sucesso = enviar_email(destino, "Mensagem via WhatsApp", msg)
        if sucesso:
            r = f"Mensagem enviada com sucesso para {destino}!"
        else:
            r = "Erro ao enviar o e-mail. Tente novamente mais tarde."
        usuarios[num] = {"estado": "inicial", "destino": ""}
    return jsonify({"replies": [{"message": r}]})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
