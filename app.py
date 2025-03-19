from flask import Flask, Response, jsonify
import requests
from bs4 import BeautifulSoup
import html
import json
import re
import time

app = Flask(__name__)

# Variável global para armazenar os filmes
filmes_globais = []

# Chaves de API válidas
API_KEYS = {
    "0a9f1e3b-7c2d-4d8a-bf23-6d5e9a8c4f12": "Usuário 1"
}

# Função para carregar os filmes ao iniciar o servidor
def carregar_filmes():
    global filmes_globais
    url = "https://visioncine-1.com.br/movies"

    try:
        response = requests.get(url, timeout=10)  # Timeout de 10 segundos
        response.encoding = 'utf-8'

        if response.status_code == 503:
            print("Erro 503: Servidor temporariamente indisponível.")
            return {"error": "Servidor temporariamente indisponível. Tente novamente mais tarde."}, 503

        if response.status_code != 200:
            print(f"Erro ao carregar os filmes. Status code: {response.status_code}")
            return {"error": f"Erro ao carregar os filmes. Status code: {response.status_code}"}, response.status_code

        soup = BeautifulSoup(response.content, "html.parser")
        filmes = soup.find_all("div", class_="swiper-slide item poster")

        if not filmes:
            print("Nenhum filme encontrado no HTML.")
            return {"error": "Nenhum filme encontrado no HTML."}, 404

        for filme in filmes:
            titulo_tag = filme.find("h6")
            titulo = titulo_tag.text.strip() if titulo_tag else "Desconhecido"

            ano_tag = filme.find("span", string=lambda x: x and "2025" in x)
            ano = ano_tag.text.strip() if ano_tag else "Desconhecido"

            imagem_tag = filme.find("div", class_="content")
            imagem = imagem_tag["style"].split("url(")[1].split(")")[0] if imagem_tag else "Imagem não disponível"

            link_assistir_tag = filme.find("a", href=True)
            link_assistir = link_assistir_tag["href"] if link_assistir_tag else "Link não disponível"

            filmes_globais.append({
                "id": len(filmes_globais) + 1,
                "titulo": html.unescape(titulo),
                "ano": html.unescape(ano),
                "imagem": imagem,
                "link_assistir": link_assistir
            })

        print(f"Carregados {len(filmes_globais)} filmes.")
        return {"message": f"Carregados {len(filmes_globais)} filmes."}, 200

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return {"error": f"Erro na requisição: {e}"}, 500

# Carregar os filmes ao iniciar o servidor
carregar_filmes()

# Rota para pegar todos os filmes (com autenticação por chave de API)
@app.route("/apikey=<apikey>/filmes", methods=["GET"])
def get_filmes(apikey):
    if apikey not in API_KEYS:
        return jsonify({"error": "Chave de API inválida"}), 403

    if not filmes_globais:
        return jsonify({"error": "Filmes não carregados. Tente novamente mais tarde."}), 503

    return Response(
        json.dumps(filmes_globais, ensure_ascii=False),
        mimetype="application/json"
    )

# Rota para pegar os detalhes de um filme específico (com autenticação por chave de API)
@app.route("/apikey=<apikey>/filmes/id=<int:filme_id>", methods=["GET"])
def get_detalhes_do_filme(apikey, filme_id):
    if apikey not in API_KEYS:
        return jsonify({"error": "Chave de API inválida"}), 403

    detalhes = pegar_detalhes_do_filme(filme_id, filmes_globais)

    if isinstance(detalhes, tuple):
        return jsonify(detalhes[0]), detalhes[1]

    return Response(
        json.dumps(detalhes, ensure_ascii=False),
        mimetype="application/json"
    )

# Função para pegar os detalhes de um filme específico
def pegar_detalhes_do_filme(filme_id, filmes_info):
    filme = next((f for f in filmes_info if f["id"] == filme_id), None)

    if not filme:
        return {"error": "Filme não encontrado."}, 404

    url_filme = filme["link_assistir"]

    if url_filme == "Link não disponível":
        return {"error": "Link de assistir não disponível."}, 404

    try:
        # Primeira requisição: página de detalhes do filme
        print(f"Fazendo requisição para a página de detalhes: {url_filme}")
        response = requests.get(url_filme, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code == 503:
            return {"error": "Servidor temporariamente indisponível. Tente novamente mais tarde."}, 503

        if response.status_code != 200:
            print(f"Erro ao acessar a página do filme. Status code: {response.status_code}")
            return {"error": f"Erro ao acessar a página do filme. Status code: {response.status_code}"}, response.status_code

        soup = BeautifulSoup(response.content, "html.parser")

        titulo = soup.select_one("h1.fw-bolder.mb-0")
        titulo = titulo.text.strip() if titulo else "Título não disponível"

        log_info = soup.select_one("p.log")
        if log_info:
            spans = log_info.find_all("span")
            if len(spans) >= 3:
                duracao = spans[0].text.strip() if spans[0] else "Duração não disponível"
                ano = spans[1].text.strip() if spans[1] else "Ano não disponível"
                classificacao = spans[2].text.strip() if spans[2] else "Classificação não disponível"
            else:
                duracao = "Duração não disponível"
                ano = "Ano não disponível"
                classificacao = "Classificação não disponível"
        else:
            duracao = "Duração não disponível"
            ano = "Ano não disponível"
            classificacao = "Classificação não disponível"

        imdb = soup.select_one("p.log > span:nth-of-type(5)")
        imdb = imdb.text.strip() if imdb else "IMDb não disponível"

        sinopse = soup.select_one("p.small.linefive")
        sinopse = sinopse.text.strip() if sinopse else "Sinopse não disponível"

        generos = soup.select_one("p.lineone > span:nth-of-type(2)")
        generos = ", ".join([span.text.strip() for span in generos.select("span")]) if generos else "Gêneros não disponíveis"

        qualidade = soup.select_one("p.log > span:nth-of-type(4)")
        qualidade = qualidade.text.strip() if qualidade else "Qualidade não disponível"

        # Extrair o link do botão "ASSISTIR"
        link_assistir = soup.select_one("a.btn.free.fw-bold:has(i.far.fa-play)")
        link_assistir = link_assistir["href"] if link_assistir else "Link de assistir não disponível"

        # Segunda requisição: página do player
        if link_assistir != "Link de assistir não disponível":
            print(f"Fazendo requisição para a página do player: {link_assistir}")
            response_player = requests.get(link_assistir, timeout=10)
            response_player.encoding = 'utf-8'

            if response_player.status_code == 503:
                return {"error": "Servidor temporariamente indisponível. Tente novamente mais tarde."}, 503

            if response_player.status_code != 200:
                print(f"Erro ao acessar a página do player. Status code: {response_player.status_code}")
                return {"error": f"Erro ao acessar a página do player. Status code: {response_player.status_code}"}, response_player.status_code

            # Extrair o link do player
            link_player = extrair_link_player(response_player.text)
        else:
            link_player = "Link do player não encontrado."

        return {
            "titulo": html.unescape(titulo),
            "ano": html.unescape(ano),
            "duracao": html.unescape(duracao),
            "classificacao": html.unescape(classificacao),
            "imdb": html.unescape(imdb),
            "sinopse": html.unescape(sinopse),
            "generos": html.unescape(generos),
            "qualidade": html.unescape(qualidade),
            "player": link_player
        }

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return {"error": f"Erro na requisição: {e}"}, 500

def extrair_link_player(html_content):
    # Procurar pelo script que contém o link do player
    soup = BeautifulSoup(html_content, "html.parser")
    scripts = soup.find_all("script")

    for script in scripts:
        script_content = script.string
        if script_content and "initializePlayer" in script_content:
            print("Script encontrado com 'initializePlayer':")
            print(script_content)
            # Usar expressão regular para extrair o link
            match = re.search(r"initializePlayer\('([^']+)'", script_content)
            if match:
                return match.group(1)  # Retorna o link do player

    return "Link do player não encontrado."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
