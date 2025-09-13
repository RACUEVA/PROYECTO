from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime
from models import db, Producto
from forms import ProductoForm
from inventario import Inventario
import json
import csv
import os

app = Flask(__name__)
# Configuración de la base de datos SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventario.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Clave secreta para la seguridad de sesiones y formularios.
app.config['SECRET_KEY'] = 'dev-secret-key'

# Inicializa la aplicación Flask con la base de datos.
db.init_app(app)

@app.context_processor
def inject_now():
    # Inyecta la fecha y hora actual en las plantillas HTML.
    return {'now': datetime.utcnow}

with app.app_context():
    # Crea las tablas de la base de datos si no existen.
    db.create_all()
    try:
        # Carga el inventario desde la base de datos al iniciar.
        inventario = Inventario.cargar_desde_bd()
    except Exception as e:
        print(f"Error al cargar inventario desde BD: {e}. Inicializando inventario vacío.")
        inventario = Inventario()

# Asegura que la carpeta 'datos' exista.
os.makedirs('datos', exist_ok=True)

# --- Rutas de la aplicación ---
@app.route('/')
def index():
    # Ruta para la página de inicio.
    return render_template('index.html', title='Inicio')

@app.route('/usuario/<nombre>')
def usuario(nombre):
    # Ruta de ejemplo que muestra el nombre del usuario.
    return f'Bienvenido, {nombre}!'

@app.route('/about')
def about():
    # Ruta para la página "Acerca de".
    return render_template('about.html', title='Acerca de')

# --- Rutas de Productos (CRUD) ---
@app.route('/productos')
def listar_productos():
    # Ruta para listar todos los productos o buscar por nombre.
    q = request.args.get('q', '').strip()
    productos = inventario.buscar_por_nombre(q) if q else inventario.listar_todos()
    return render_template('products/list.html', title='Productos', productos=productos, q=q)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    # Ruta para crear un nuevo producto.
    form = ProductoForm()
    if form.validate_on_submit():
        try:
            inventario.agregar(
                nombre=form.nombre.data,
                cantidad=form.cantidad.data,
                precio=form.precio.data
            )
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except ValueError as e:
            form.nombre.errors.append(str(e))
        except Exception as e:
            flash(f'Error al agregar producto: {e}', 'danger')
    return render_template('products/form.html', title='Nuevo producto', form=form, modo='crear')

@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    # Ruta para editar un producto existente.
    prod = Producto.query.get_or_404(pid)
    form = ProductoForm(obj=prod)

    if form.validate_on_submit():
        try:
            inventario.actualizar(
                id=pid,
                nombre=form.nombre.data,
                cantidad=form.cantidad.data,
                precio=form.precio.data
            )
            flash('Producto actualizado.', 'success')
            return redirect(url_for('listar_productos'))
        except ValueError as e:
            form.nombre.errors.append(str(e))
        except Exception as e:
            flash(f'Error al actualizar producto: {e}', 'danger')

    return render_template('products/form.html', title='Editar producto', form=form, modo='editar')

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    # Ruta para eliminar un producto.
    # Solo acepta peticiones POST para evitar eliminaciones accidentales.
    ok = inventario.eliminar(pid)
    flash('Producto eliminado.' if ok else 'Producto no encontrado.', 'info' if ok else 'warning')
    return redirect(url_for('listar_productos'))

# --- Rutas para Persistencia con Archivos ---
@app.route('/guardar-txt', methods=['GET', 'POST'])
def guardar_txt():
    data_to_save = "Nuevo registro guardado."
    with open('datos/datos.txt', 'a') as f:
        f.write(data_to_save + '\n')
    flash('Datos guardados en datos.txt', 'success')
    return redirect(url_for('index'))

@app.route('/leer-txt')
def leer_txt():
    try:
        with open('datos/datos.txt', 'r') as f:
            datos = f.readlines()
        return render_template('datos.html', title='Datos TXT', datos=datos)
    except FileNotFoundError:
        flash('El archivo datos.txt no existe.', 'danger')
        return redirect(url_for('index'))

@app.route('/guardar-json', methods=['GET', 'POST'])
def guardar_json():
    productos_json = [{'id': p.id, 'nombre': p.nombre, 'cantidad': p.cantidad, 'precio': p.precio}
                      for p in inventario.listar_todos()]
    with open('datos/datos.json', 'w') as f:
        json.dump(productos_json, f, indent=4)
    flash('Datos guardados en datos.json', 'success')
    return redirect(url_for('listar_productos'))

@app.route('/leer-json')
def leer_json():
    try:
        with open('datos/datos.json', 'r') as f:
            datos = json.load(f)
        return render_template('datos_json.html', title='Datos JSON', datos=datos)
    except (FileNotFoundError, json.JSONDecodeError):
        flash('Error al leer el archivo JSON.', 'danger')
        return redirect(url_for('index'))

@app.route('/guardar-csv', methods=['GET', 'POST'])
def guardar_csv():
    header = ['id', 'nombre', 'cantidad', 'precio']
    productos_csv = [p.to_tuple() for p in inventario.listar_todos()]
    with open('datos/datos.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(productos_csv)
    flash('Datos guardados en datos.csv', 'success')
    return redirect(url_for('listar_productos'))

@app.route('/leer-csv')
def leer_csv():
    try:
        with open('datos/datos.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            datos = [dict(zip(header, row)) for row in reader]
        return render_template('datos_csv.html', title='Datos CSV', datos=datos)
    except (FileNotFoundError, StopIteration):
        flash('Error al leer el archivo CSV.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)