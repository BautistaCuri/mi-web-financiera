from flask import Flask

app = Flask(__name__)

@app.route('/')
def inicio():
    return "<h1>¡Tu sitio web financiero está vivo!</h1><p>Próximamente verás aquí las herramientas de cálculo.</p>"

if __name__ == '__main__':
    app.run(debug=True)
