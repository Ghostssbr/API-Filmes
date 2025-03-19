from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Bem-vindo à API Visioncine!"

@app.route('/html-visioncine')
def html_visioncine():
    url = "https://visioncine-1.com.br/movies"  # URL do Visioncine (ajuste conforme necessário)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Levanta um erro se a resposta for inválida (status diferente de 200)

        # Retorna o conteúdo HTML da página
        return Response(response.text, mimetype='text/html')

    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar o site: {e}"

if __name__ == '__main__':
    app.run(debug=True)
