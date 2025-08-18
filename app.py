from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "¡mi_proyecto_flask!"

@app.route('/usuario/<nombre>')
def usuario(nombre):
    return f'Bienvenido, {nombre}!'

if __name__ == '__main__':
    app.run(debug=True)
