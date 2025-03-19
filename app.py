import aiohttp
import asyncio
from flask import Flask, Response

app = Flask(__name__)

@app.route('/')
def home():
    return "Bem-vindo à API Visioncine!"

@app.route('/html-visioncine')
async def html_visioncine():
    url = "https://visioncine-1.com.br/movies"

    # Cabeçalhos para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://visioncine-1.com.br',  # Adicionando um cabeçalho de Referer
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return Response(html_content, mimetype='text/html')
                else:
                    return f"Erro ao acessar o site. Status code: {response.status}"

    except Exception as e:
        return f"Erro ao acessar o site: {e}"

if __name__ == '__main__':
    app.run(debug=True)
