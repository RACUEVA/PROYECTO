from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    #return "¡mi_proyecto_flask!"
    return render_template('index.html')

@app.route('/usuario/<nombre>')
def usuario(nombre):
    return f'Bienvenido, {nombre}!'

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacto')
def contacto():
    #return "bienvenido a la pagina de contactos"
    return render_template('contacto.html')

if __name__ == '__main__':
    app.run(debug=True)
