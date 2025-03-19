from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "Hello, World!"

@app.route('/api/filmes')
def filmes():
    filmes_data = [
        {
            "id": 1,
            "titulo": "Filme 1",
            "ano": 2023
        },
        {
            "id": 2,
            "titulo": "Filme 2",
            "ano": 2024
        }
    ]
    return jsonify(filmes_data)

if __name__ == '__main__':
    app.run(debug=True)
