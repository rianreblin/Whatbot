from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session import smtplib, os, re from email.mime.text import MIMEText from datetime import datetime

app = Flask(name) app.secret_key = 'chave_secreta'

EMAIL_REMETENTE = "rianreblin@gmail.com" SENHA_APP = "jijb hqsg csgy wkgk"

usuarios = {} tarefas = [] historico = []

HTML simples para painel web

PAINEL_HTML = """

<!DOCTYPE html><html>
<head><title>Painel do Bot</title></head>
<body>
  <h2>Bem-vindo ao Painel</h2>
  <form method="post" action="/adicionar">
    <input name="texto" placeholder="Texto da tarefa" required>
    <input name="dia" placeholder="Dia da semana (ex: segunda)" required>
    <button type="submit">Adicionar Tarefa</button>
  </form>
  <ul>
    {% for t in tarefas %}
      <li>{{t['texto']}} ({{t['dia']}}) <a href="/excluir/{{loop.index0}}">Excluir</a></li>
    {% endfor %}
  </ul>
  <hr>
  <h3>Histórico de uso do bot</h3>
  <ul>
    {% for h in historico %}
      <li>{{ h }}</li>
    {% endfor %}
  </ul>
  <a href="/logout">Logout</a>
</body>
</html>
"""LOGIN_HTML = """

<form method="post">
  <input name="username" placeholder="Usuário">
  <input name="password" placeholder="Senha" type="password">
  <button type="submit">Entrar</button>
</form>
"""@app.route('/') def home(): return 'Servidor WhatsAuto ativo ✅'

@app.route('/login', methods=['GET', 'POST']) def login(): if request.method == 'POST': if request.form['username'] == 'admin' and request.form['password'] == 'admin': session['logado'] = True return redirect(url_for('painel')) return render_template_string(LOGIN_HTML)

@app.route('/logout') def logout(): session.pop('logado', None) return redirect(url_for('login'))

@app.route('/painel') def painel(): if not session.get('logado'): return redirect(url_for('login')) return render_template_string(PAINEL_HTML, tarefas=tarefas, historico=historico)

@app.route('/adicionar', methods=['POST']) def adicionar(): if not session.get('logado'): return redirect(url_for('login')) tarefas.append({"texto": request.form['texto'], "dia": request.form['dia'].lower()}) return redirect(url_for('painel'))

@app.route('/excluir/int:indice') def excluir(indice): if not session.get('logado'): return redirect(url_for('login')) if 0 <= indice < len(tarefas): tarefas.pop(indice) return redirect(url_for('painel'))

def enviar_email(destino, assunto, corpo): try: msg = MIMEText(corpo) msg['Subject'] = assunto msg['From'] = EMAIL_REMETENTE msg['To'] = destino with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: smtp.login(EMAIL_REMETENTE, SENHA_APP) smtp.send_message(msg) return True except Exception as e: return str(e)

@app.route('/responder', methods=['POST']) def responder(): dados = request.get_json() query = dados.get("query", {}) msg = query.get("message", "").strip() num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido" historico.append(f"{datetime.now().strftime('%d/%m %H:%M')} - {num}: {msg}")

if num == "desconhecido":
    return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

if msg == "/tarefa":
    dia_atual = datetime.now().strftime('%A').lower()
    tarefas_do_dia = [t['texto'] for t in tarefas if t['dia'] == dia_atual]
    resposta = '\n'.join(tarefas_do_dia) if tarefas_do_dia else "📭 Nenhuma tarefa para hoje."
    return jsonify({"replies": [{"message": resposta}]})

if num not in usuarios:
    usuarios[num] = {"estado": "inicial", "destino": "", "assunto": ""}

estado = usuarios[num]["estado"]
resposta = "👋 Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola\n/tarefa - Ver tarefas do dia"

if estado == "inicial":
    if msg.lower() == "a":
        usuarios[num]["estado"] = "aguardando_email"
        resposta = "📧 Para qual e-mail você quer enviar a mensagem?"
    elif msg.lower() == "b":
        resposta = "📚 Horário escolar:\nSegunda a sexta: 08h às 17h"
    elif msg.lower() in ["oi", "olá", "menu"]:
        resposta = resposta
elif estado == "aguardando_email":
    if re.match(r"[^@]+@[^@]+\\.[^@]+", msg):
        usuarios[num]["destino"] = msg
        usuarios[num]["estado"] = "aguardando_assunto"
        resposta = "✏️ Qual será o assunto do e-mail?"
    else:
        resposta = "⚠️ E-mail inválido. Por favor, digite um e-mail válido."
elif estado == "aguardando_assunto":
    usuarios[num]["assunto"] = msg
    usuarios[num]["estado"] = "aguardando_mensagem"
    resposta = "📝 Agora digite a mensagem que deseja enviar."
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

if name == 'main': app.run(host='0.0.0.0', port=8000)

