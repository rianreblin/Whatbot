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
            resposta = "📧 Qual e-mail você deseja enviar?"
        elif msg.lower() == "b":
            resposta = "📚 Horário escolar:\nSeg-Sex: 08h às 17h"
    elif estado == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "confirmar_assunto"
            resposta = f"📌 Deseja alterar o assunto do e-mail?\nPadrão: 'Mensagem via WhatsApp'.\nDigite o novo assunto ou envie 'ok' para manter."
        else:
            resposta = "⚠️ E-mail inválido. Tente novamente."
    elif estado == "confirmar_assunto":
        if msg.lower() == "ok":
            usuarios[num]["assunto"] = "Mensagem via WhatsApp"
        else:
            usuarios[num]["assunto"] = msg
        usuarios[num]["estado"] = "aguardando_mensagem"
        resposta = f"✏️ Agora digite a mensagem que deseja enviar para {usuarios[num]['destino']}"
    elif estado == "aguardando_mensagem":
        destino = usuarios[num]["destino"]
        assunto = usuarios[num]["assunto"]
        resultado = enviar_email(destino, assunto, msg)
        if resultado is True:
            resposta = f"✅ E-mail enviado com sucesso para {destino}!"
        else:
            resposta = f"❌ Erro ao enviar e-mail:\n{resultado}"
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": ""}

    return jsonify({"replies": [{"message": resposta}]})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logado'] = True
            return redirect(url_for('painel'))
        return "Login inválido"
    return render_template_string('''
    <form method="post">
        <input name="username" placeholder="Usuário">
        <input name="password" placeholder="Senha" type="password">
        <button>Entrar</button>
    </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

@app.route('/painel')
def painel():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template_string('''
    <h1>Gerenciador de Tarefas</h1>
    <form method="post" action="/add_tarefa">
        <input name="texto" placeholder="Descrição da tarefa">
        <input name="dia" type="date">
        <button>Adicionar</button>
    </form>
    <ul>
        {% for tarefa in tarefas %}
        <li>{{tarefa.texto}} - {{tarefa.dia}} <a href="/remover_tarefa?texto={{tarefa.texto}}">Remover</a></li>
        {% endfor %}
    </ul>
    <h2>Histórico</h2>
    <ul>
        {% for h in historico[-20:] %}
        <li><b>{{h.numero}}</b>: {{h.mensagem}} ({{h.hora}})</li>
        {% endfor %}
    </ul>
    <a href="/logout">Sair</a>
    ''', tarefas=tarefas, historico=historico)

@app.route('/add_tarefa', methods=['POST'])
def add_tarefa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    texto = request.form['texto']
    dia = request.form['dia']
    tarefas.append({"texto": texto, "dia": dia})
    return redirect(url_for('painel'))

@app.route('/remover_tarefa')
def remover_tarefa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    texto = request.args.get("texto")
    global tarefas
    tarefas = [t for t in tarefas if t['texto'] != texto]
    return redirect(url_for('painel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
