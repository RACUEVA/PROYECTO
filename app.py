# app.py sin sqlalchemy, se va a conectar a mysql.connector via conexion/conexion.py
from flask import Flask, render_template, request, redirect, url_for, flash 
from conexion.conexion import conexion, cerrar_conexion, crear_tablas
from forms import ProductoForm, ClienteForm
from datetime import datetime
from decimal import Decimal
import json
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# Inicializar tablas al iniciar la aplicación
crear_tablas()

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# --- Rutas principales ---
@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/about/')
def about():
    return render_template('about.html', title='Acerca de')

# ---- Productos ----
@app.route('/productos')
def listar_productos():
    q = request.args.get('q', '').strip()
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return render_template('products/list.html', title='Productos', productos=[], q=q)
    
    cur = conn.cursor(dictionary=True)
    try:
        if q:
            cur.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE nombre LIKE %s", (f"%{q}%",))
        else:
            cur.execute("SELECT id, nombre, cantidad, precio FROM productos")
        productos = cur.fetchall()
        print(f"DEBUG: {len(productos)} productos encontrados en BD")
    except Exception as e:
        print(f"Error al consultar productos: {e}")
        productos = []
    finally:
        cerrar_conexion(conn)
    
    return render_template('products/list.html', title='Productos', productos=productos, q=q)

@app.route('/productos/nuevo', methods=['GET', 'POST'])
def crear_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        conn = conexion()
        if conn is None:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('products/form.html', title='Nuevo producto', form=form, modo='crear')
        
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO productos (nombre, cantidad, precio) VALUES (%s, %s, %s)",
                (form.nombre.data, form.cantidad.data, float(form.precio.data))
            )
            conn.commit()
            flash('Producto agregado correctamente.', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            conn.rollback()
            flash(f'No se pudo guardar: {str(e)}', 'error')
        finally:
            cerrar_conexion(conn)
    
    return render_template('products/form.html', title='Nuevo producto', form=form, modo='crear')

@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_productos'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE id = %s", (pid,))
        producto = cursor.fetchone()
        
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('listar_productos'))
            
        form = ProductoForm(data={
            'nombre': producto['nombre'], 
            'cantidad': producto['cantidad'], 
            'precio': float(producto['precio'])
        })
        
        if form.validate_on_submit():
            try:
                cursor.execute(
                    "UPDATE productos SET nombre=%s, cantidad=%s, precio=%s WHERE id=%s", 
                    (form.nombre.data, form.cantidad.data, float(form.precio.data), pid)
                )
                conn.commit()
                flash('Producto actualizado correctamente.', 'success')
                return redirect(url_for('listar_productos'))
            except Exception as e:
                conn.rollback()
                flash(f'Error al actualizar: {str(e)}', 'error')
                
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('listar_productos'))
    finally:
        cerrar_conexion(conn)
    
    return render_template('products/form.html', title='Editar producto', form=form, modo='editar', pid=pid)

@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_productos'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = %s", (pid,))
        if cursor.rowcount > 0:
            conn.commit()
            flash('Producto eliminado correctamente.', 'success')
        else:
            flash('Producto no encontrado.', 'warning')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

# ---- Clientes ----
@app.route('/clientes')
def listar_clientes():
    clientes = []  # Inicializar con lista vacía por defecto
    
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return render_template('clientes/list.html', title='Clientes', clientes=clientes)
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, apellido, telefono, email, fecha_registro FROM clientes ORDER BY id DESC")
        clientes = cur.fetchall()
        print(f"DEBUG: {len(clientes)} clientes encontrados en BD")
        
    except Exception as e:
        print(f"Error al consultar clientes: {e}")
        flash('Error al cargar los clientes', 'error')
        clientes = []  # Asegurar que siempre sea una lista
        
    finally:
        cerrar_conexion(conn)
    
    return render_template('clientes/list.html', title='Clientes', clientes=clientes)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
def crear_cliente():
    form = ClienteForm()
    
    if form.validate_on_submit():
        conn = conexion()
        if conn is None:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('clientes/form.html', title='Nuevo cliente', form=form, modo='crear')
        
        try:
            cur = conn.cursor(dictionary=True)
            # Verificar si el email ya existe
            cur.execute("SELECT id FROM clientes WHERE email = %s", (form.email.data,))
            if cur.fetchone():
                flash('Ya existe un cliente con este email', 'error')
                return render_template('clientes/form.html', title='Nuevo cliente', form=form, modo='crear')
            
            # Insertar nuevo cliente
            cur.execute(
                "INSERT INTO clientes (nombre, apellido, telefono, email) VALUES (%s, %s, %s, %s)",
                (form.nombre.data, form.apellido.data, form.telefono.data, form.email.data)
            )
            conn.commit()
            
            # Verificar que se insertó correctamente
            cur.execute("SELECT LAST_INSERT_ID() as id")
            nuevo_id = cur.fetchone()['id']
            print(f"DEBUG: Cliente insertado con ID: {nuevo_id}")
            
            flash('Cliente agregado correctamente.', 'success')
            return redirect(url_for('listar_clientes'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error al guardar: {str(e)}', 'error')
        finally:
            cerrar_conexion(conn)
    
    return render_template('clientes/form.html', title='Nuevo cliente', form=form, modo='crear')

@app.route('/clientes/<int:cid>/editar', methods=['GET', 'POST'])
def editar_cliente(cid):
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_clientes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, telefono, email FROM clientes WHERE id = %s", (cid,))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('Cliente no encontrado', 'error')
            return redirect(url_for('listar_clientes'))
            
        form = ClienteForm(data={
            'nombre': cliente['nombre'], 
            'apellido': cliente['apellido'], 
            'telefono': cliente['telefono'], 
            'email': cliente['email']
        })
        
        if form.validate_on_submit():
            try:
                # Verificar si el email ya existe en otro cliente
                cursor.execute("SELECT id FROM clientes WHERE email = %s AND id != %s", (form.email.data, cid))
                if cursor.fetchone():
                    flash('Ya existe otro cliente con este email', 'error')
                    return render_template('clientes/form.html', title='Editar cliente', form=form, modo='editar', cid=cid)
                
                cursor.execute(
                    "UPDATE clientes SET nombre=%s, apellido=%s, telefono=%s, email=%s WHERE id=%s", 
                    (form.nombre.data, form.apellido.data, form.telefono.data, form.email.data, cid)
                )
                conn.commit()
                flash('Cliente actualizado correctamente.', 'success')
                return redirect(url_for('listar_clientes'))
            except Exception as e:
                conn.rollback()
                flash(f'Error al actualizar: {str(e)}', 'error')
                
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('listar_clientes'))
    finally:
        cerrar_conexion(conn)
    
    return render_template('clientes/form.html', title='Editar cliente', form=form, modo='editar', cid=cid)

@app.route('/clientes/<int:cid>/eliminar', methods=['POST'])
def eliminar_cliente(cid):
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_clientes'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cid,))
        if cursor.rowcount > 0:
            conn.commit()
            flash('Cliente eliminado correctamente.', 'success')
        else:
            flash('Cliente no encontrado.', 'warning')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_clientes'))

# --- Funciones de exportación ---
@app.route('/guardar_txt')
def guardar_txt():
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_productos'))
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, cantidad, precio FROM productos")
        productos = cur.fetchall()
        
        with open('productos.txt', 'w', encoding='utf-8') as f:
            for p in productos:
                f.write(f"{p['id']}, {p['nombre']}, {p['cantidad']}, {p['precio']}\n")
        
        flash('Productos guardados en productos.txt', 'success')
    except Exception as e:
        flash(f'Error al guardar TXT: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

@app.route('/guardar_json')     
def guardar_json():
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_productos'))
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, cantidad, precio FROM productos")
        productos = cur.fetchall()
        
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        with open('productos.json', 'w', encoding='utf-8') as f:
            json.dump(productos, f, ensure_ascii=False, indent=4, default=decimal_default)
        
        flash('Productos guardados en productos.json', 'success')
    except Exception as e:
        flash(f'Error al guardar JSON: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

@app.route('/guardar_csv')
def guardar_csv():
    conn = conexion()
    if conn is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('listar_productos'))
    
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nombre, cantidad, precio FROM productos")
        productos = cur.fetchall()
        
        with open('productos.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'nombre', 'cantidad', 'precio'])
            writer.writeheader()
            writer.writerows(productos)
        
        flash('Productos guardados en productos.csv', 'success')
    except Exception as e:
        flash(f'Error al guardar CSV: {str(e)}', 'error')
    finally:
        cerrar_conexion(conn)
    
    return redirect(url_for('listar_productos'))

# --- Ejecutar la app ---
if __name__ == '__main__':
    app.run(debug=True)