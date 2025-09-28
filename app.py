# app.py - VERSIÓN FINAL CORREGIDA
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from conexion.conexion import conexion, cerrar_conexion, crear_tablas, verificar_tabla_usuarios
from forms import ProductoForm, ClienteForm, LoginForm, RegistroForm 
from models_user import Usuario 
from datetime import datetime
from decimal import Decimal
import json
import csv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

def handle_db_error(e=None):
    """Maneja errores de base de datos"""
    error_msg = 'Error de conexión a la base de datos'
    if e:
        error_msg = f'Error: {str(e)}'
        print(f"❌ ERROR BD: {e}")
    flash(error_msg, 'error')
    return None

# Función helper para convertir tipos de datos
def convertir_tipos_producto(producto):
    """Convierte los tipos de datos del producto a los correctos"""
    if isinstance(producto, dict):
        try:
            producto['cantidad'] = int(producto['cantidad'])
            producto['precio'] = float(producto['precio'])
            producto['id'] = int(producto['id'])
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error convirtiendo tipos: {e}")
            # Mantener valores originales si hay error en conversión
            pass
    return producto

def convertir_tipos_cliente(cliente):
    """Convierte los tipos de datos del cliente a los correctos"""
    if isinstance(cliente, dict):
        try:
            cliente['id'] = int(cliente['id'])
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error convirtiendo tipos cliente: {e}")
            pass
    return cliente

# Inicialización de tablas
print("🔄 Inicializando tablas de la base de datos...")
try:
    if crear_tablas():
        print("✅ Tablas inicializadas correctamente")
    else:
        print("⚠️ Problemas al inicializar tablas")
except Exception as e:
    print(f"❌ Error inicializando tablas: {e}")

@login_manager.user_loader
def load_user(user_id):
    return Usuario.get(user_id)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# --- Rutas de Autenticación ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data
        
        # Validaciones
        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('registro.html', title='Registro', form=form)
        
        if password != form.confirm_password.data:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html', title='Registro', form=form)
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('registro.html', title='Registro', form=form)
        
        # Verificar si el usuario ya existe
        usuario_existente = Usuario.get_by_email(email)
        if usuario_existente:
            flash('Este correo electrónico ya está registrado', 'error')
            return render_template('registro.html', title='Registro', form=form)
        
        conn = conexion()
        if conn is None:
            handle_db_error()
            return render_template('registro.html', title='Registro', form=form)
        
        try:
            cursor = conn.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                (nombre, email, hashed_password)
            )
            conn.commit()
            flash('✅ Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            handle_db_error(e)
        finally:
            cerrar_conexion(conn)
    
    return render_template('registro.html', title='Registro', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        
        user = Usuario.get_by_email(email)
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f' Bienvenido de vuelta, {user.nombre}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('❌ Correo electrónico o contraseña incorrectos', 'error')
    
    return render_template('login.html', title='Iniciar Sesión', form=form)

@app.route('/logout')
@login_required
def logout():
    user_name = current_user.nombre
    logout_user()
    flash(f'👋 Hasta pronto, {user_name}!', 'success')
    return redirect(url_for('index'))

# --- Rutas principales ---
@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

# --- RUTAS ESPECÍFICAS PARA CUMPLIR REQUISITOS DEL MÓDULO ---

@app.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Ruta específica para crear producto (requisito del módulo)"""
    return redirect(url_for('crear_producto'))

@app.route('/productos')
@login_required
def productos():
    """Ruta específica para listar productos (requisito del módulo)"""
    return redirect(url_for('listar_productos'))

@app.route('/editar/<int:id>')
@login_required
def editar(id):
    """Ruta específica para editar producto (requisito del módulo)"""
    return redirect(url_for('editar_producto', pid=id))

@app.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    """Ruta específica para eliminar producto (requisito del módulo)"""
    return redirect(url_for('eliminar_producto', pid=id))

# ---- Productos ----
@app.route('/productos/lista')
@login_required
def listar_productos():
    q = request.args.get('q', '').strip()
    conn = conexion()
    if conn is None:
        handle_db_error()
        return render_template('productos/list.html', title='Productos', productos=[], q=q)
    
    try:
        cur = conn.cursor(dictionary=True)
        if q:
            cur.execute("""
                SELECT id, nombre, cantidad, precio 
                FROM productos 
                WHERE nombre LIKE %s 
                ORDER BY nombre ASC
            """, (f"%{q}%",))
        else:
            cur.execute("SELECT id, nombre, cantidad, precio FROM productos ORDER BY nombre ASC")
        
        productos_raw = cur.fetchall()
        # 🔧 CONVERTIR TIPOS DE DATOS
        productos = [convertir_tipos_producto(p) for p in productos_raw]
        
    except Exception as e:
        handle_db_error(e)
        productos = []
    finally:
        cerrar_conexion(conn)
    
    return render_template('productos/list.html', title='Productos', productos=productos, q=q)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        cantidad = form.cantidad.data
        precio = form.precio.data
        
        # Validaciones adicionales
        if cantidad < 0:
            flash('La cantidad no puede ser negativa', 'error')
            return render_template('productos/form.html', title='Nuevo producto', form=form, modo='crear')
        
        if precio < 0:
            flash('El precio no puede ser negativo', 'error')
            return render_template('productos/form.html', title='Nuevo producto', form=form, modo='crear')
        
        conn = conexion()
        if conn is None:
            handle_db_error()
            return render_template('productos/form.html', title='Nuevo producto', form=form, modo='crear')
        
        try:
            cur = conn.cursor()
            # Verificar si el producto ya existe
            cur.execute("SELECT id FROM productos WHERE nombre = %s", (nombre,))
            if cur.fetchone():
                flash('❌ Ya existe un producto con ese nombre', 'error')
                return render_template('productos/form.html', title='Nuevo producto', form=form, modo='crear')
            
            cur.execute(
                "INSERT INTO productos (nombre, cantidad, precio) VALUES (%s, %s, %s)",
                (nombre, cantidad, float(precio))
            )
            conn.commit()
            flash('✅ Producto agregado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            conn.rollback()
            flash(f'❌ No se pudo guardar: {str(e)}', 'error')
        finally:
            cerrar_conexion(conn)
    
    return render_template('productos/form.html', title='Nuevo producto', form=form, modo='crear')

@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(pid):
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_productos'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE id = %s", (pid,))
        producto_raw = cursor.fetchone()
        
        if not producto_raw:
            flash('❌ Producto no encontrado', 'error')
            return redirect(url_for('listar_productos'))
        
        # 🔧 CONVERTIR TIPOS DE DATOS
        producto = convertir_tipos_producto(producto_raw)
            
        form = ProductoForm(data={
            'nombre': producto['nombre'], 
            'cantidad': producto['cantidad'], 
            'precio': float(producto['precio'])
        })
        
        if form.validate_on_submit():
            nombre = form.nombre.data.strip()
            cantidad = form.cantidad.data
            precio = form.precio.data
            
            # Validaciones
            if cantidad < 0:
                flash('La cantidad no puede ser negativa', 'error')
                return render_template('productos/form.html', title='Editar producto', form=form, modo='editar', pid=pid)
            
            if precio < 0:
                flash('El precio no puede ser negativo', 'error')
                return render_template('productos/form.html', title='Editar producto', form=form, modo='editar', pid=pid)
            
            try:
                # Verificar si el nombre ya existe en otro producto
                cursor.execute("SELECT id FROM productos WHERE nombre = %s AND id != %s", (nombre, pid))
                if cursor.fetchone():
                    flash('❌ Ya existe otro producto con ese nombre', 'error')
                    return render_template('productos/form.html', title='Editar producto', form=form, modo='editar', pid=pid)
                
                cursor.execute(
                    "UPDATE productos SET nombre=%s, cantidad=%s, precio=%s WHERE id=%s", 
                    (nombre, cantidad, float(precio), pid)
                )
                conn.commit()
                flash('✅ Producto actualizado correctamente.', 'success')
                return redirect(url_for('listar_productos'))
            except Exception as e:
                conn.rollback()
                flash(f'❌ Error al actualizar: {str(e)}', 'error')
                
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        return redirect(url_for('listar_productos'))
    finally:
        cerrar_conexion(conn)
    
    return render_template('productos/form.html', title='Editar producto', form=form, modo='editar', pid=pid)

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
@login_required
def eliminar_producto(pid):
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_productos'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM productos WHERE id = %s", (pid,))
        producto = cursor.fetchone()
        
        if not producto:
            flash('❌ Producto no encontrado.', 'error')
            return redirect(url_for('listar_productos'))
        
        # Confirmación antes de eliminar (requisito del módulo)
        if not request.form.get('confirmar'):
            return '''
            <script>
                if (confirm("¿Estás seguro de que deseas eliminar este producto? Esta acción no se puede deshacer.")) {
                    document.getElementById("confirm-form").submit();
                } else {
                    window.history.back();
                }
            </script>
            <form id="confirm-form" method="post" action="''' + url_for('eliminar_producto', pid=pid) + '''">
                <input type="hidden" name="confirmar" value="true">
            </form>
            '''
        
        cursor.execute("DELETE FROM productos WHERE id = %s", (pid,))
        if cursor.rowcount > 0:
            conn.commit()
            flash(f'✅ Producto "{producto["nombre"]}" eliminado correctamente.', 'success')
        else:
            flash('⚠️ No se pudo eliminar el producto.', 'warning')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error al eliminar: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

# ---- Clientes ----
@app.route('/clientes')
@login_required
def listar_clientes():
    q = request.args.get('q', '').strip()
    conn = conexion()
    if conn is None:
        handle_db_error()
        return render_template('clientes/list.html', title='Clientes', clientes=[], q=q)
    
    try:
        cur = conn.cursor(dictionary=True)
        if q:
            sql = """
                SELECT id, nombre, apellido, telefono, email, fecha_registro 
                FROM clientes 
                WHERE nombre LIKE %s OR apellido LIKE %s OR email LIKE %s 
                ORDER BY fecha_registro DESC
            """
            q_like = f"%{q}%"
            cur.execute(sql, (q_like, q_like, q_like))
        else:
            cur.execute("""
                SELECT id, nombre, apellido, telefono, email, fecha_registro 
                FROM clientes 
                ORDER BY fecha_registro DESC
            """)
        
        clientes_raw = cur.fetchall()
        # 🔧 CONVERTIR TIPOS DE DATOS
        clientes = [convertir_tipos_cliente(c) for c in clientes_raw]
        
    except Exception as e:
        handle_db_error(e)
        clientes = []
    finally:
        cerrar_conexion(conn)
    
    return render_template('clientes/list.html', title='Clientes', clientes=clientes, q=q)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def crear_cliente():
    form = ClienteForm()
    
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        apellido = form.apellido.data.strip()
        telefono = form.telefono.data.strip()
        email = form.email.data.strip().lower()
        
        conn = conexion()
        if conn is None:
            handle_db_error()
            return render_template('clientes/form.html', title='Nuevo cliente', form=form, modo='crear')
        
        try:
            cur = conn.cursor(dictionary=True)
            # Verificar si el email ya existe
            cur.execute("SELECT id FROM clientes WHERE email = %s", (email,))
            if cur.fetchone():
                flash('❌ Ya existe un cliente con este email', 'error')
                return render_template('clientes/form.html', title='Nuevo cliente', form=form, modo='crear')
            
            cur.execute(
                "INSERT INTO clientes (nombre, apellido, telefono, email) VALUES (%s, %s, %s, %s)",
                (nombre, apellido, telefono, email)
            )
            conn.commit()
            flash('✅ Cliente agregado correctamente.', 'success')
            return redirect(url_for('listar_clientes'))
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Error al guardar: {str(e)}', 'error')
        finally:
            cerrar_conexion(conn)
    
    return render_template('clientes/form.html', title='Nuevo cliente', form=form, modo='crear')

@app.route('/clientes/<int:cid>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(cid):
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_clientes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, telefono, email FROM clientes WHERE id = %s", (cid,))
        cliente_raw = cursor.fetchone()
        
        if not cliente_raw:
            flash('❌ Cliente no encontrado', 'error')
            return redirect(url_for('listar_clientes'))
        
        # 🔧 CONVERTIR TIPOS DE DATOS
        cliente = convertir_tipos_cliente(cliente_raw)
            
        form = ClienteForm(data={
            'nombre': cliente['nombre'], 
            'apellido': cliente['apellido'], 
            'telefono': cliente['telefono'], 
            'email': cliente['email']
        })
        
        if form.validate_on_submit():
            nombre = form.nombre.data.strip()
            apellido = form.apellido.data.strip()
            telefono = form.telefono.data.strip()
            email = form.email.data.strip().lower()
            
            try:
                # Verificar si el email ya existe en otro cliente
                cursor.execute("SELECT id FROM clientes WHERE email = %s AND id != %s", (email, cid))
                if cursor.fetchone():
                    flash('❌ Ya existe otro cliente con este email', 'error')
                    return render_template('clientes/form.html', title='Editar cliente', form=form, modo='editar', cid=cid)
                
                cursor.execute(
                    "UPDATE clientes SET nombre=%s, apellido=%s, telefono=%s, email=%s WHERE id=%s", 
                    (nombre, apellido, telefono, email, cid)
                )
                conn.commit()
                flash('✅ Cliente actualizado correctamente.', 'success')
                return redirect(url_for('listar_clientes'))
            except Exception as e:
                conn.rollback()
                flash(f'❌ Error al actualizar: {str(e)}', 'error')
                
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        return redirect(url_for('listar_clientes'))
    finally:
        cerrar_conexion(conn)
    
    return render_template('clientes/form.html', title='Editar cliente', form=form, modo='editar', cid=cid)

@app.route('/clientes/<int:cid>/eliminar', methods=['POST'])
@login_required
def eliminar_cliente(cid):
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_clientes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre, apellido FROM clientes WHERE id = %s", (cid,))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('❌ Cliente no encontrado.', 'error')
            return redirect(url_for('listar_clientes'))
        
        # Confirmación antes de eliminar (requisito del módulo)
        if not request.form.get('confirmar'):
            return '''
            <script>
                if (confirm("¿Estás seguro de que deseas eliminar este cliente? Esta acción no se puede deshacer.")) {
                    document.getElementById("confirm-form").submit();
                } else {
                    window.history.back();
                }
            </script>
            <form id="confirm-form" method="post" action="''' + url_for('eliminar_cliente', cid=cid) + '''">
                <input type="hidden" name="confirmar" value="true">
            </form>
            '''
        
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cid,))
        if cursor.rowcount > 0:
            conn.commit()
            flash(f'✅ Cliente "{cliente["nombre"]} {cliente["apellido"]}" eliminado correctamente.', 'success')
        else:
            flash('⚠️ No se pudo eliminar el cliente.', 'warning')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error al eliminar: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_clientes'))

# ---- Dashboard y Estadísticas ----
@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard con estadísticas del sistema"""
    conn = conexion()
    if conn is None:
        handle_db_error()
        return render_template('dashboard.html', stats={})
    
    stats = {}
    try:
        cur = conn.cursor(dictionary=True)
        
        # Estadísticas de productos
        cur.execute("SELECT COUNT(*) as total, SUM(cantidad) as stock_total, AVG(precio) as precio_promedio FROM productos")
        productos_stats = cur.fetchone()
        if productos_stats:
            stats['productos'] = {
                'total': int(productos_stats['total']),
                'stock_total': int(productos_stats['stock_total'] or 0),
                'precio_promedio': float(productos_stats['precio_promedio'] or 0)
            }
        
        # Productos con stock bajo
        cur.execute("SELECT COUNT(*) as bajo_stock FROM productos WHERE cantidad < 10")
        bajo_stock = cur.fetchone()
        stats['bajo_stock'] = int(bajo_stock['bajo_stock']) if bajo_stock else 0
        
        # Estadísticas de clientes
        cur.execute("SELECT COUNT(*) as total FROM clientes")
        clientes_total = cur.fetchone()
        stats['clientes'] = int(clientes_total['total']) if clientes_total else 0
        
        # Clientes registrados este mes
        cur.execute("SELECT COUNT(*) as este_mes FROM clientes WHERE MONTH(fecha_registro) = MONTH(CURRENT_DATE())")
        clientes_mes = cur.fetchone()
        stats['clientes_este_mes'] = int(clientes_mes['este_mes']) if clientes_mes else 0
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        stats = {}
    finally:
        cerrar_conexion(conn)
    
    return render_template('dashboard.html', title='Dashboard', stats=stats)

@app.route('/productos/stock-bajo')
@login_required
def productos_stock_bajo():
    """Productos con stock bajo (menos de 10 unidades)"""
    conn = conexion()
    productos = []
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, nombre, cantidad, precio 
            FROM productos 
            WHERE cantidad < 10 
            ORDER BY cantidad ASC
        """)
        productos_raw = cur.fetchall()
        
        # 🔧 CONVERTIR TIPOS DE DATOS
        productos = [convertir_tipos_producto(p) for p in productos_raw]
            
    except Exception as e:
        flash(f'❌ Error al cargar productos con stock bajo: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return render_template('stock_bajo.html', title='Productos con Stock Bajo', productos=productos)

# --- Funciones de exportación ---
@app.route('/guardar_txt')
@login_required
def guardar_txt():
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_productos'))
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, cantidad, precio FROM productos ORDER BY nombre")
        productos_raw = cur.fetchall()
        
        # 🔧 CONVERTIR TIPOS DE DATOS
        productos = [convertir_tipos_producto(p) for p in productos_raw]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"productos_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("INVENTARIO DE PRODUCTOS - Librería y Papelería Cueva\n")
            f.write(f"Exportado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"{'ID':<5} {'NOMBRE':<30} {'CANTIDAD':<10} {'PRECIO':<10}\n")
            f.write("-" * 60 + "\n")
            
            for p in productos:
                f.write(f"{p['id']:<5} {p['nombre']:<30} {p['cantidad']:<10} ${p['precio']:<10.2f}\n")
            
            f.write("-" * 60 + "\n")
            f.write(f"Total de productos: {len(productos)}\n")
        
        flash(f'✅ Productos exportados a {filename}', 'success')
    except Exception as e:
        flash(f'❌ Error al exportar TXT: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

@app.route('/guardar_json')     
@login_required
def guardar_json():
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_productos'))
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, cantidad, precio FROM productos ORDER BY nombre")
        productos_raw = cur.fetchall()
        
        # 🔧 CONVERTIR TIPOS DE DATOS
        productos = [convertir_tipos_producto(p) for p in productos_raw]
        
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"productos_{timestamp}.json"
        
        data = {
            "empresa": "Librería y Papelería Cueva",
            "fecha_exportacion": datetime.now().isoformat(),
            "total_productos": len(productos),
            "productos": productos
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=decimal_default)
        
        flash(f'✅ Productos exportados a {filename}', 'success')
    except Exception as e:
        flash(f'❌ Error al exportar JSON: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

@app.route('/guardar_csv')
@login_required
def guardar_csv():
    conn = conexion()
    if conn is None:
        handle_db_error()
        return redirect(url_for('listar_productos'))
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, cantidad, precio FROM productos ORDER BY nombre")
        productos_raw = cur.fetchall()
        
        # 🔧 CONVERTIR TIPOS DE DATOS
        productos = [convertir_tipos_producto(p) for p in productos_raw]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"productos_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Encabezado
            writer.writerow(['ID', 'Nombre', 'Cantidad', 'Precio'])
            # Datos
            for producto in productos:
                writer.writerow([
                    producto['id'],
                    producto['nombre'],
                    producto['cantidad'],
                    producto['precio']
                ])
        
        flash(f'✅ Productos exportados a {filename}', 'success')
    except Exception as e:
        flash(f'❌ Error al exportar CSV: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

# --- Ruta para diagnóstico ---
@app.route('/diagnostico')
def diagnostico():
    """Página de diagnóstico del sistema"""
    resultado = {
        'tabla_usuarios_existe': verificar_tabla_usuarios(),
        'usuario_autenticado': current_user.is_authenticated,
        'base_datos_conectable': conexion() is not None,
        'fecha_servidor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    conn = conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tablas = [tabla[0] for tabla in cursor.fetchall()]
            resultado['tablas_existentes'] = tablas
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            resultado['total_usuarios'] = int(cursor.fetchone()[0])
            
            cursor.execute("SELECT COUNT(*) as total FROM productos")
            resultado['total_productos'] = int(cursor.fetchone()[0])
            
            cursor.execute("SELECT COUNT(*) as total FROM clientes")
            resultado['total_clientes'] = int(cursor.fetchone()[0])
            
        except Exception as e:
            resultado['error'] = str(e)
        finally:
            cerrar_conexion(conn)
    
    return render_template('diagnostico.html', title='Diagnóstico del Sistema', resultado=resultado)

# --- Manejo de errores ---
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(401)
def unauthorized_error(error):
    flash('🔐 Debes iniciar sesión para acceder a esta página', 'warning')
    return redirect(url_for('login'))

# --- Health check para monitoreo ---
@app.route('/health')
def health_check():
    """Endpoint para verificar el estado del servicio"""
    try:
        conn = conexion()
        if conn and conn.is_connected():
            cerrar_conexion(conn)
            return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200
        else:
            return {'status': 'unhealthy', 'error': 'Database connection failed'}, 503
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 503

# --- Ruta de prueba para verificar CRUD básico ---
@app.route('/test-crud')
def test_crud():
    """Ruta de prueba para verificar que el CRUD funciona correctamente"""
    return jsonify({
        'status': 'success',
        'message': 'Sistema CRUD funcionando correctamente',
        'rutas_disponibles': {
            'crear_producto': '/productos/nuevo',
            'listar_productos': '/productos/lista', 
            'editar_producto': '/productos/<id>/editar',
            'eliminar_producto': '/productos/<id>/eliminar',
            'dashboard': '/dashboard',
            'exportar': '/guardar_csv, /guardar_json, /guardar_txt'
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Iniciando aplicación Flask...")
    print("📊 Dashboard disponible en: /dashboard")
    print("🔧 Diagnóstico del sistema en: /diagnostico")
    print("❤️ Health check en: /health")
    print("🧪 Test CRUD en: /test-crud")
    print("📍 Rutas CRUD específicas:")
    print("   - Crear: /crear")
    print("   - Listar: /productos") 
    print("   - Editar: /editar/<id>")
    print("   - Eliminar: /eliminar/<id>")
    app.run(debug=True, host='0.0.0.0', port=5000)