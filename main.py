from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session import smtplib import os import re from email.mime.text import MIMEText

app = Flask(name) app.secret_key = 'segredo_teste_123'

EMAIL_REMETENTE = "rianreblin@gmail.com" SENHA_APP = "jijbhqsgcsgywkgk"

usuarios = {} tarefas = []  # Lista para armazenar tarefas

def enviar_email(destino, assunto, corpo): if not EMAIL_REMETENTE or not SENHA_APP: return "⚠️ Variáveis de envio não configuradas corretamente." try: msg = MIMEText(corpo) msg['Subject'] = assunto msg['From'] = EMAIL_REMETENTE msg['To'] = destino with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: smtp.login(EMAIL_REMETENTE, SENHA_APP) smtp.send_message(msg) return True except Exception as e: return f"❌ Erro ao enviar o e-mail:\n{e}"

@app.route('/responder', methods=['POST']) def responder(): dados = request.get_json() query = dados.get("query", {}) msg = query.get("message", "").strip() num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido"

if num == "desconhecido":
    return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

if msg.lower() == "/tarefa":
    if tarefas:
        lista = "\n".join([f"- {t}" for t in tarefas])
        return jsonify({"replies": [{"message": f"📋 Tarefas atuais:\n{lista}"}]})
    else:
        return jsonify({"replies": [{"message": "📭 Nenhuma tarefa cadastrada."}]})

if num not in usuarios:
    usuarios[num] = {"estado": "inicial", "destino": "", "assunto": "Mensagem via WhatsApp"}

estado = usuarios[num]["estado"]
resposta = "👋 Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola\n/tarefa - Ver tarefas"

if estado == "inicial":
    if msg.lower() == "a":
        usuarios[num]["estado"] = "aguardando_email"
        resposta = "📧 Para qual e-mail você quer enviar a mensagem?"
    elif msg.lower() == "b":
        resposta = "📚 Horário escolar:\nSegunda a sexta: 08h às 17h"
    elif msg.lower() in ["oi", "olá", "menu"]:
        resposta = "👋 Olá! Escolha:\nA - Enviar e-mail\nB - Ver horário\n/tarefa - Ver tarefas"
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

============================ INTERFACE WEB COM LOGIN E TAREFAS ============================

LOGIN_TEMPLATE = '''

<form method="post">
  <h2>Login</h2>
  <input name="usuario" placeholder="Usuário"><br>
  <input name="senha" placeholder="Senha" type="password"><br>
  <button type="submit">Entrar</button>
</form>
'''PAINEL_TEMPLATE = '''

<h2>Painel do Bot</h2>
<p>Seu bot está online ✅</p>
<h3>📋 Tarefas cadastradas:</h3>
<ul>
  {% for tarefa in tarefas %}<li>{{ tarefa }}</li>{% else %}<li>Nenhuma tarefa</li>{% endfor %}
</ul>
<form method="post" action="/adicionar">
  <input name="nova" placeholder="Nova tarefa">
  <button type="submit">Adicionar</button>
</form>
<form method="post" action="/remover">
  <input name="indice" placeholder="Nº da tarefa para remover">
  <button type="submit">Remover</button>
</form>
<a href="/logout">Sair</a>
'''@app.route("/login", methods=["GET", "POST"]) def login(): if request.method == "POST": if request.form['usuario'] == "admin" and request.form['senha'] == "admin": session['logado'] = True return redirect(url_for('painel')) return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout") def logout(): session.pop('logado', None) return redirect(url_for('login'))

@app.route("/painel") def painel(): if not session.get('logado'): return redirect(url_for('login')) return render_template_string(PAINEL_TEMPLATE, tarefas=tarefas)

@app.route("/adicionar", methods=["POST"]) def adicionar(): if not session.get('logado'): return redirect(url_for('login')) nova = request.form.get("nova") if nova: tarefas.append(nova.strip()) return redirect(url_for('painel'))

@app.route("/remover", methods=["POST"]) def remover(): if not session.get('logado'): return redirect(url_for('login')) try: idx = int(request.form.get("indice")) if 0 <= idx < len(tarefas): tarefas.pop(idx) except: pass return redirect(url_for('painel'))

@app.route('/') def home(): return 'Servidor WhatsAuto ativo ✅'

if name == 'main': app.run(host='0.0.0.0', port=8000)

