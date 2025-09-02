from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URL do seu servidor WPPConnect no Render
WPP_URL = "https://seu-wppconnect.onrender.com/send-message"

@app.route("/")
def home():
    return "✅ Bot Python está rodando!"

# Rota de teste para enviar mensagem
@app.route("/teste", methods=["GET"])
def teste():
    numero = request.args.get("phone", "5511999999999")  # número padrão, pode passar pela URL
    mensagem = "Olá, teste do bot Python ✅"

    try:
        resp = requests.post(WPP_URL, json={"number": numero, "message": mensagem})
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)