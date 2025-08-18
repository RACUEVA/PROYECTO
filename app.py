from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "¡mi_proyecto_flask!"

@app.route('/usuarios/<nombre>')
def usuarios(andres):
    return f'Bienvenido, {andres}!'

@app.route('/contacto')
def contacto():
    return "bienvenido a la pagina de contactos"

if __name__ == '__main__':
    app.run(debug=True)
