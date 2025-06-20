from flask import Flask, request, jsonify
import smtplib, os, re
from email.mime.text import MIMEText

app = Flask(__name__)

EMAIL_REMETENTE = os.getenv("rianreblin@gmail.com")
SENHA_APP = os.getenv("sckt ujqr fkcu oujq")

# Guarda os estados de conversa de cada número
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
    num = dados.get("number", "")  # <- WhatsAuto envia isso, certifique-se de que está vindo!

    if not num:
        return jsonify({"replies": [{"message": "Erro: número não informado."}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": ""}

    estado = usuarios[num]["estado"]
    resposta = "Envie 'A' para enviar e-mail ou 'B' para ver horário."

    if estado == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
            resposta = "Para qual e-mail você quer enviar a mensagem?"
        elif msg.lower() == "b":
            resposta = "Horário da escola: Segunda a sexta, das 8h às 17h."
        elif msg.lower() in ["oi", "olá"]:
            resposta = "Olá! Escolha uma opção:\nA - Enviar e-mail\nB - Ver horário"
    elif estado == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "aguardando_mensagem"
            resposta = f"Ok! Agora digite a mensagem que deseja enviar para {msg}."
        else:
            resposta = "E-mail inválido. Por favor, digite um e-mail válido."
    elif estado == "aguardando_mensagem":
        destino = usuarios[num]["destino"]
        sucesso = enviar_email(destino, "Mensagem via WhatsApp", msg)
        if sucesso:
            resposta = f"E-mail enviado com sucesso para {destino}!"
        else:
            resposta = "Erro ao enviar o e-mail. Tente novamente mais tarde."
        usuarios[num] = {"estado": "inicial", "destino": ""}

    return jsonify({"replies": [{"message": resposta}]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
