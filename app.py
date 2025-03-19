from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Bem-vindo à API Visioncine!"

@app.route('/html-visioncine')
def html_visioncine():
    url = "https://visioncine-1.com.br/movies"  # URL do Visioncine (ajuste conforme necessário)

    # Cabeçalhos que simulam uma requisição de um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Requisição com cabeçalhos personalizados
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Levanta um erro se a resposta for inválida (status diferente de 200)

        # Retorna o conteúdo HTML da página
        return Response(response.text, mimetype='text/html')

    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar o site: {e}"

if __name__ == '__main__':
    app.run(debug=True)
