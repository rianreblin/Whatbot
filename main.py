from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import smtplib, os, re
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'supersecreta'

# Dados fixos (você já me autorizou)
EMAIL_REMETENTE = "rianreblin@gmail.com"
SENHA_APP = "jijbhqsgcsgywkgk"

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
        print("❌ Erro ao enviar e-mail:", e)
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

    if num == "desconhecido":
        return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado. Verifique o JSON."}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": ""}

    estado = usuarios[num]["estado"]
    resposta = "👋 Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola"

    if estado == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
            resposta = "📧 Para qual e-mail você quer enviar a mensagem?"
        elif msg.lower() == "b":
            resposta = "📚 Horário escolar:\nSegunda a sexta: 08h às 17h"
        elif msg.lower() in ["oi", "olá", "menu"]:
            resposta = "👋 Olá! Escolha uma opção:\nA - Enviar e-mail\nB - Ver horário"
    elif estado == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "aguardando_assunto"
            resposta = "✏️ Qual será o assunto do e-mail?"
        else:
            resposta = "⚠️ E-mail inválido. Por favor, digite um e-mail válido."
    elif estado == "aguardando_assunto":
        usuarios[num]["assunto"] = msg
        usuarios[num]["estado"] = "aguardando_mensagem"
        resposta = "💬 Agora envie a mensagem que deseja mandar."
    elif estado == "aguardando_mensagem":
        destino = usuarios[num]["destino"]
        assunto = usuarios[num]["assunto"]
        resultado = enviar_email(destino, assunto, msg)
        if resultado == True:
            resposta = f"✅ E-mail enviado com sucesso para {destino}!"
        else:
            resposta = f"❌ Erro ao enviar o e-mail:\n{resultado}"
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": ""}

    return jsonify({"replies": [{"message": resposta}]})


# --- Interface Web ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get("usuario")
        senha = request.form.get("senha")
        if user == "admin" and senha == "admin":
            session["logado"] = True
            return redirect(url_for('painel'))
        return "❌ Login inválido"
    return render_template_string("""
    <h2>Login do Painel</h2>
    <form method="post">
        Usuário: <input name="usuario"><br>
        Senha: <input name="senha" type="password"><br>
        <button type="submit">Entrar</button>
    </form>
    """)

@app.route('/painel')
def painel():
    if not session.get("logado"):
        return redirect(url_for("login"))
    return "<h2>Painel do Bot</h2><p>✅ Bot rodando!</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
