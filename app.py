from flask import Flask, Response, jsonify
import requests
from bs4 import BeautifulSoup
import html
import json

app = Flask(__name__)

# Variável global para armazenar os filmes
filmes_globais = []

# Função para carregar os filmes
def carregar_filmes():
    global filmes_globais
    url = "https://visioncine-1.com.br/movies"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"Erro ao carregar a página: Status {response.status_code}")
            return

        soup = BeautifulSoup(response.content, "html.parser")
        filmes = soup.find_all("div", class_="swiper-slide item poster")

        # Limpa a lista antes de adicionar novos filmes
        filmes_globais.clear()

        if not filmes:
            print("Nenhum filme encontrado na página.")
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

        print(f"Carregados {len(filmes_globais)} filmes.")
    except Exception as e:
        print(f"Erro ao carregar filmes: {str(e)}")

# Carregar filmes ao iniciar o servidor
carregar_filmes()

# Função para carregar filmes ao acessar a raiz
@app.route("/", methods=["GET"])
def index():
    if filmes_globais:
        return jsonify(filmes_globais)
    else:
        return jsonify({"erro": "Falha ao carregar filmes. Tente novamente mais tarde."})

# Rota para pegar todos os filmes
@app.route("/filmes", methods=["GET"])
def get_filmes():
    if filmes_globais:
        return Response(
            json.dumps(filmes_globais, ensure_ascii=False),
            mimetype="application/json"
        )
    else:
        return jsonify({"erro": "Falha ao carregar filmes. Tente novamente mais tarde."})

# Rota para pegar os detalhes de um filme específico
@app.route("/filmes/id=<int:filme_id>", methods=["GET"])
def get_detalhes_do_filme(filme_id):
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

    if filme:
        url_filme = filme["link_assistir"]

        if url_filme == "Link não disponível":
            return {"error": "Link de assistir não disponível."}, 404

        try:
            # Primeira requisição: página de detalhes do filme
            response = requests.get(url_filme)
            response.encoding = 'utf-8'

            if response.status_code != 200:
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

            return {
                "titulo": html.unescape(titulo),
                "ano": html.unescape(ano),
                "duracao": html.unescape(duracao),
                "classificacao": html.unescape(classificacao),
                "imdb": html.unescape(imdb),
                "sinopse": html.unescape(sinopse),
                "generos": html.unescape(generos),
                "qualidade": html.unescape(qualidade),
                "player": link_assistir
            }
        except Exception as e:
            print(f"Erro ao carregar os detalhes do filme {filme_id}: {str(e)}")
            return {"error": "Erro ao acessar a página do filme."}, 500
    else:
        return {"error": "Filme não encontrado."}, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
