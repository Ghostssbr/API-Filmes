from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Bem-vindo à API cine!"

@app.route('/html-visioncine')
def html_visioncine():
    url = "https://visioncine-1.com.br/movies"

    # Usar uma sessão para persistir cookies
    session = requests.Session()

    # Cabeçalhos para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://visioncine-1.com.br',  # Adicionando um cabeçalho de Referer
    }

    # Tentando pegar o conteúdo da página
    try:
        # Requisição com a sessão
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Levanta erro se a resposta não for 200

        # Retornar o conteúdo HTML da página
        return Response(response.text, mimetype='text/html')

    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar o site: {e}"

if __name__ == '__main__':
    app.run(debug=True)
