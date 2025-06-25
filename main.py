from flask import Flask, request, jsonify import smtplib, re from email.mime.text import MIMEText

app = Flask(name)

EMAIL_REMETENTE = "rianreblin@gmail.com" SENHA_APP = "jijbhqsgcsgywkgk"  # senha de app

usuarios = {}

def enviar_email(destino, assunto, corpo): if not EMAIL_REMETENTE or not SENHA_APP: return "⚠️ Variáveis de envio não configuradas corretamente." try: msg = MIMEText(corpo) msg['Subject'] = assunto msg['From'] = EMAIL_REMETENTE msg['To'] = destino

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_REMETENTE, SENHA_APP)
        smtp.send_message(msg)

    return True
except Exception as e:
    return f"❌ Erro ao enviar e-mail:\n{e}"

@app.route('/responder', methods=['POST']) def responder(): dados = request.get_json() query = dados.get("query", {}) msg = query.get("message", "").strip() num = query.get("sender") or query.get("number") or query.get("from") or "desconhecido"

if num == "desconhecido":
    return jsonify({"replies": [{"message": "⚠️ Erro: número do usuário não identificado."}]})

if num not in usuarios:
    usuarios[num] = {"estado": "inicial", "destino": "", "mensagem": "", "assunto": "Mensagem via WhatsApp"}

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
        resposta = f"✉️ Digite a mensagem que deseja enviar para {msg}."
    else:
        resposta = "⚠️ E-mail inválido. Digite um válido."
elif estado == "aguardando_mensagem":
    usuarios[num]["mensagem"] = msg
    usuarios[num]["estado"] = "confirmar_assunto"
    resposta = f"📝 Deseja alterar o assunto do e-mail? Responda com o novo assunto ou envie 'ok' para manter o padrão: '{usuarios[num]['assunto']}'."
elif estado == "confirmar_assunto":
    if msg.lower() != "ok":
        usuarios[num]["assunto"] = msg
    destino = usuarios[num]["destino"]
    assunto = usuarios[num]["assunto"]
    corpo = usuarios[num]["mensagem"]
    resultado = enviar_email(destino, assunto, corpo)
    resposta = f"✅ E-mail enviado com sucesso para {destino}!" if resultado is True else resultado
    usuarios[num] = {"estado": "inicial", "destino": "", "mensagem": "", "assunto": "Mensagem via WhatsApp"}

return jsonify({"replies": [{"message": resposta}]})

@app.route('/') def home(): return 'Servidor WhatsAuto ativo ✅'

if name == 'main': app.run(host='0.0.0.0', port=8000)

