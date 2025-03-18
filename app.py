from flask import Flask, Response, jsonify
import requests
from bs4 import BeautifulSoup
import html
import json
import re
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Iniciando carregamento dos filmes...")
        response = requests.get(url, timeout=10)  # Timeout de 10 segundos
        response.encoding = 'utf-8'

        if response.status_code != 200:
            logger.error(f"Erro ao carregar os filmes. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, "html.parser")
        filmes = soup.find_all("div", class_="swiper-slide item poster")

        if not filmes:
            logger.warning("Nenhum filme encontrado no HTML.")
            return

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

        logger.info(f"Carregados {len(filmes_globais)} filmes.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar filmes: {e}")

# Carregar os filmes ao iniciar o servidor
carregar_filmes()

# Rota para pegar todos os filmes (com autenticação por chave de API)
@app.route("/apikey=<apikey>/filmes", methods=["GET"])
def get_filmes(apikey):
    if apikey not in API_KEYS:
        logger.warning(f"Chave de API inválida: {apikey}")
        return jsonify({"error": "Chave de API inválida"}), 403

    if not filmes_globais:
        logger.error("Nenhum filme carregado.")
        return jsonify({"error": "Filmes não carregados. Tente novamente mais tarde."}), 503

    return Response(
        json.dumps(filmes_globais, ensure_ascii=False),
        mimetype="application/json"
    )

# Rota para pegar os detalhes de um filme específico (com autenticação por chave de API)
@app.route("/apikey=<apikey>/filmes/id=<int:filme_id>", methods=["GET"])
def get_detalhes_do_filme(apikey, filme_id):
    if apikey not in API_KEYS:
        logger.warning(f"Chave de API inválida: {apikey}")
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
        logger.error(f"Filme com ID {filme_id} não encontrado.")
        return {"error": "Filme não encontrado."}, 404

    url_filme = filme["link_assistir"]

    if url_filme == "Link não disponível":
        logger.error(f"Link de assistir não disponível para o filme ID {filme_id}.")
        return {"error": "Link de assistir não disponível."}, 404

    try:
        logger.info(f"Fazendo requisição para a página de detalhes: {url_filme}")
        response = requests.get(url_filme, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            logger.error(f"Erro ao acessar a página do filme. Status code: {response.status_code}")
            return {"error": "Erro ao acessar a página do filme."}, 500

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
            logger.info(f"Fazendo requisição para a página do player: {link_assistir}")
            response_player = requests.get(link_assistir, timeout=10)
            response_player.encoding = 'utf-8'

            if response_player.status_code != 200:
                logger.error(f"Erro ao acessar a página do player. Status code: {response_player.status_code}")
                return {"error": "Erro ao acessar a página do player."}, 500

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
        logger.error(f"Erro na requisição: {e}")
        return {"error": "Erro na requisição."}, 500
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return {"error": "Erro inesperado."}, 500

# Função para extrair o link do player
def extrair_link_player(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        scripts = soup.find_all("script")

        for script in scripts:
            script_content = script.string
            if script_content and "initializePlayer" in script_content:
                match = re.search(r"initializePlayer\('([^']+)'", script_content)
                if match:
                    return match.group(1)  # Retorna o link do player

        return "Link do player não encontrado."
    except Exception as e:
        logger.error(f"Erro ao extrair link do player: {e}")
        return "Link do player não encontrado."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
