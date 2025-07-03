from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import smtplib
import os
import re
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'chave-secreta-teste'

EMAIL_REMETENTE = "rianreblin@gmail.com"
SENHA_APP = "jijb hqsg csgy wkgk"  # Substituir sempre que trocar a senha de app

tarefas = []
usuarios = {}

def enviar_email(destino, assunto, corpo):
    if not EMAIL_REMETENTE or not SENHA_APP:
        return "\u274c Variáveis de ambiente não configuradas corretamente."
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

    if num == "desconhecido":
        return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

    if num not in usuarios:
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": "Mensagem via WhatsApp"}

    estado = usuarios[num]["estado"]
    resposta = "👋 Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola\n/tarefa - Ver tarefas"

    if msg.lower() == "/tarefa":
        if tarefas:
            resposta = "📋 Tarefas:\n" + "\n".join(f"- {t}" for t in tarefas)
        else:
            resposta = "📋 Nenhuma tarefa cadastrada."

    elif estado == "inicial":
        if msg.lower() == "a":
            usuarios[num]["estado"] = "aguardando_email"
            resposta = "📧 Qual e-mail você quer usar como destino?"
        elif msg.lower() == "b":
            resposta = "📚 Horário escolar:\nSegunda a sexta: 08h às 17h"
        elif msg.lower() in ["oi", "olá", "menu"]:
            resposta = resposta

    elif estado == "aguardando_email":
        if re.match(r"[^@]+@[^@]+\.[^@]+", msg):
            usuarios[num]["destino"] = msg
            usuarios[num]["estado"] = "confirmar_assunto"
            resposta = f"✉️ Deseja mudar o assunto do e-mail? Responda com o novo assunto ou digite 'padrão'."
        else:
            resposta = "⚠️ E-mail inválido. Por favor, digite um e-mail válido."

    elif estado == "confirmar_assunto":
        if msg.lower() == "padrão":
            usuarios[num]["estado"] = "aguardando_mensagem"
        else:
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
        usuarios[num] = {"estado": "inicial", "destino": "", "assunto": "Mensagem via WhatsApp"}

    return jsonify({"replies": [{"message": resposta}]})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['usuario'] == 'admin' and request.form['senha'] == 'admin':
            session['logado'] = True
            return redirect(url_for('painel'))
        return '❌ Login inválido'

    return render_template_string('''
        <form method="post">
            <h2>Login</h2>
            Usuário: <input name="usuario"><br>
            Senha: <input name="senha" type="password"><br>
            <button type="submit">Entrar</button>
        </form>
    ''')

@app.route('/painel')
def painel():
    if not session.get('logado'):
        return redirect(url_for('login'))

    lista = "<ul>" + "".join(f"<li>{t} <a href='/remover_tarefa?texto={t}'>❌</a></li>" for t in tarefas) + "</ul>"
    return render_template_string(f'''
        <h2>Painel de Tarefas</h2>
        <form method="post" action="/add_tarefa">
            Nova tarefa: <input name="texto">
            <button type="submit">Adicionar</button>
        </form>
        {lista}
        <a href="/logout">Sair</a>
    ''')

@app.route('/add_tarefa', methods=['POST'])
def add_tarefa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    texto = request.form.get('texto', '').strip()
    if texto:
        tarefas.append(texto)
    return redirect(url_for('painel'))

@app.route('/remover_tarefa')
def remover_tarefa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    texto = request.args.get('texto')
    if texto in tarefas:
        tarefas.remove(texto)
    return redirect(url_for('painel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
