from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return 'Servidor WhatsAuto ativo ✅'

@app.route('/responder', methods=['POST'])
def responder():
    dados = request.get_json()
    print("📥 DADOS RECEBIDOS:", dados)

    query = dados.get("query", {})  # pegar o campo query
    msg = query.get("message", "").strip()
    numero = query.get("sender") or query.get("number") or "desconhecido"

    if numero == "desconhecido":
        return jsonify({
            "replies": [{
                "message": "⚠️ Erro: número do usuário não identificado.\n\nVerifique o JSON enviado."
            }]
        })

    if msg.upper() == "A":
        return jsonify({
            "replies": [{
                "message": "📧 Para qual e-mail você quer enviar?"
            }]
        })

    elif msg.upper() == "B":
        return jsonify({
            "replies": [{
                "message": "🕒 Horário da escola:\nSeg-Sex: 07h às 18h\nSábado: 08h às 12h"
            }]
        })

    elif "@" in msg and "." in msg:
        return jsonify({
            "replies": [{
                "message": f"✅ E-mail '{msg}' recebido! Agora envie a mensagem que deseja mandar."
            }]
        })

    else:
        return jsonify({
            "replies": [{
                "message": "👋 Olá! Envie:\nA - Para enviar um e-mail\nB - Para ver o horário da escola"
            }]
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
