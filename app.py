from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime
from models import db, Producto
from forms import ProductoForm
from inventario import Inventario

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

    if form.validate_on_submit(): # Added validation check
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

if __name__ == '__main__':
    app.run(debug=True)
    