from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session import smtplib, os, re from email.mime.text import MIMEText

app = Flask(name) app.secret_key = 'segredo_teste_123'  # Necessário para sessões de login

Informações fixas do e-mail (por enquanto)

EMAIL_REMETENTE = "rianreblin@gmail.com" SENHA_APP = "jijbhqsgcsgywkgk"

usuarios = {}

Função para enviar e-mail

def enviar_email(destino, assunto, corpo): if not EMAIL_REMETENTE or not SENHA_APP: return "⚠️ Variáveis de ambiente não configuradas corretamente." try: msg = MIMEText(corpo) msg['Subject'] = assunto msg['From'] = EMAIL_REMETENTE msg['To'] = destino with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: smtp.login(EMAIL_REMETENTE, SENHA_APP) smtp.send_message(msg) return True except Exception as e: return str(e)

@app.route('/responder', methods=['POST']) def responder(): dados = request.get_json() query = dados.get("query", {}) msg = query.get("message", "").strip() num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido"

if num == "desconhecido":
    return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

if num not in usuarios:
    usuarios[num] = {"estado": "inicial", "destino": "", "assunto": "Mensagem via WhatsApp"}

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
        usuarios[num]["estado"] = "aguardando_mensagem"
        resposta = f"✉️ Agora digite a mensagem que deseja enviar para {msg}."
    else:
        resposta = "⚠️ E-mail inválido. Por favor, digite um e-mail válido."
elif estado == "aguardando_mensagem":
    usuarios[num]["mensagem"] = msg
    usuarios[num]["estado"] = "aguardando_assunto"
    resposta = "📌 Deseja alterar o assunto do e-mail? Digite o novo assunto ou 'ok' para manter."
elif estado == "aguardando_assunto":
    if msg.lower() != "ok":
        usuarios[num]["assunto"] = msg
    destino = usuarios[num]["destino"]
    assunto = usuarios[num]["assunto"]
    corpo = usuarios[num]["mensagem"]
    resultado = enviar_email(destino, assunto, corpo)
    if resultado is True:
        resposta = f"✅ E-mail enviado com sucesso para {destino}!"
    else:
        resposta = f"❌ Erro ao enviar o e-mail:\n{resultado}"
    usuarios[num] = {"estado": "inicial", "destino": "", "assunto": "Mensagem via WhatsApp"}

return jsonify({"replies": [{"message": resposta}]})

============================ INTERFACE WEB COM LOGIN ============================

LOGIN_TEMPLATE = '''

<form method="post">
  <h2>Login</h2>
  <input name="usuario" placeholder="Usuário"><br>
  <input name="senha" placeholder="Senha" type="password"><br>
  <button type="submit">Entrar</button>
</form>
'''PAINEL_TEMPLATE = '''

<h2>Bem-vindo ao Painel!</h2>
<p>Seu bot está online ✅</p>
<a href="/logout">Sair</a>
'''@app.route("/login", methods=["GET", "POST"]) def login(): if request.method == "POST": if request.form['usuario'] == "admin" and request.form['senha'] == "admin": session['logado'] = True return redirect(url_for('painel')) return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout") def logout(): session.pop('logado', None) return redirect(url_for('login'))

@app.route("/painel") def painel(): if not session.get('logado'): return redirect(url_for('login')) return render_template_string(PAINEL_TEMPLATE)

@app.route('/') def home(): return 'Servidor WhatsAuto ativo ✅'

if name == 'main': app.run(host='0.0.0.0', port=8000)

