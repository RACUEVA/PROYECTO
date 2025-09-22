# conexion.py
import mysql.connector
from mysql.connector import Error

def conexion():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='papeleria_cueva',
            user='root',
            password='uea2025'
        )
        if conn.is_connected():
            print("✓ Conexión exitosa a la base de datos")
            return conn
    except Error as e:
        print(f"✗ Error al conectar a MySQL: {e}")
        return None

def cerrar_conexion(conn):
    if conn and conn.is_connected():
        conn.close()
        print("✓ Conexión a la base de datos cerrada.")

def crear_tablas():
    conn = None
    try:
        conn = conexion()
        if conn is None:
            print("No se pudo conectar a la base de datos")
            return False
            
        cursor = conn.cursor()
        
        # Tabla de productos
        sql_productos = """
        CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL UNIQUE,
            cantidad INT NOT NULL DEFAULT 0,
            precio DECIMAL(10, 2) NOT NULL DEFAULT 0.0
        );
        """
        
        # Tabla de clientes
        sql_clientes = """
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL,
            apellido VARCHAR(120) NOT NULL,
            telefono VARCHAR(20) NOT NULL,
            email VARCHAR(120) UNIQUE,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Tabla de usuarios (para el sistema de login)
        sql_usuarios = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        print("Verificando/Creando tabla 'productos'...")
        cursor.execute(sql_productos)
        
        print("Verificando/Creando tabla 'clientes'...")
        cursor.execute(sql_clientes)
        
        print("Verificando/Creando tabla 'usuarios'...")
        cursor.execute(sql_usuarios)
        
        conn.commit()
        print("Todas las tablas verificadas/creadas correctamente.")
        
        # Verificar que las tablas existen
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        print("Tablas en la base de datos:", [tabla[0] for tabla in tablas])
        
        return True
        
    except Error as e:
        print(f"Error al crear tablas: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cerrar_conexion(conn)

if __name__ == '__main__':
    crear_tablas()