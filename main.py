from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import smtplib
import os
import re
import sqlite3
from datetime import datetime
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'segredo'

EMAIL_REMETENTE = "rianreblin@gmail.com"
SENHA_APP = "jijbhqsgcsgywkgk"

# Inicializa o banco de dados
conn = sqlite3.connect('dados.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tarefas (id INTEGER PRIMARY KEY, texto TEXT, data TEXT, materia TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, numero TEXT, mensagem TEXT, hora TEXT)''')
conn.commit()

materias_lista = sorted([
    "Artes", "Biologia", "Educação Física", "Empreendedorismo", "Filosofia",
    "Física", "Geografia", "Gestão De Pessoas", "Gestão De Qualidade",
    "História", "Língua Inglesa", "Língua Portuguêsa", "Marketing",
    "Matemática", "Projeto De Vida", "Química", "Sociologia"
])

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

    c.execute("INSERT INTO historico (numero, mensagem, hora) VALUES (?, ?, ?)",
              (num, msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()

    if num == "desconhecido":
        return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

    if msg == "/tarefa":
        c.execute("SELECT texto, data, materia FROM tarefas")
        tarefas = c.fetchall()
        if tarefas:
            resposta = "📝 Tarefas:\n" + "\n".join([f"📌 {t[0]} - {t[1]} ({t[2]})" for t in tarefas])
        else:
            resposta = "📭 Nenhuma tarefa registrada."
        return jsonify({"replies": [{"message": resposta}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": ""}

    estado = usuarios[num]["estado"]
    resposta = "👋 Envie:\nA - Enviar e-mail\nB - Ver horário\n/tarefa - Ver tarefas"

    if estado == "inicial":
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

    c.execute("SELECT texto, data, materia FROM tarefas")
    tarefas = c.fetchall()
    c.execute("SELECT numero, mensagem, hora FROM historico ORDER BY id DESC LIMIT 20")
    historico = c.fetchall()

    return render_template_string('''
        <h1>Gerenciador de Tarefas</h1>
        <form method="post" action="/add_tarefa">
            <input name="texto" placeholder="Descrição da tarefa">
            <input name="data" type="date" placeholder="Data">
            <select name="materia">
                {% for m in materias %}<option value="{{m}}">{{m}}</option>{% endfor %}
            </select>
            <button>Adicionar</button>
        </form>
        <ul>
            {% for t in tarefas %}
                <li>{{t[0]}} - {{t[1]}} ({{t[2]}}) <a href="/remover_tarefa?texto={{t[0]}}">Remover</a></li>
            {% endfor %}
        </ul>
        <h2>Histórico</h2>
        <ul>
            {% for h in historico %}
                <li><b>{{h[0]}}</b>: {{h[1]}} ({{h[2]}})</li>
            {% endfor %}
        </ul>
        <a href="/logout">Sair</a>
    ''', tarefas=tarefas, historico=historico, materias=materias_lista)

@app.route('/add_tarefa', methods=['POST'])
def add_tarefa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    texto = request.form['texto']
    data = request.form['data']
    materia = request.form['materia']
    c.execute("INSERT INTO tarefas (texto, data, materia) VALUES (?, ?, ?)", (texto, data, materia))
    conn.commit()
    return redirect(url_for('painel'))

@app.route('/remover_tarefa')
def remover_tarefa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    texto = request.args.get("texto")
    c.execute("DELETE FROM tarefas WHERE texto = ?", (texto,))
    conn.commit()
    return redirect(url_for('painel'))

usuarios = {}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
