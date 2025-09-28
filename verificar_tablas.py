# verificar_tablas.py
from conexion.conexion import conexion, cerrar_conexion, verificar_tabla_usuarios
import mysql.connector

def verificar_base_datos():
    print("=== VERIFICACIÓN COMPLETA DE LA BASE DE DATOS ===")
    
    try:
        # Conexión sin especificar base de datos
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='uea2025'
        )
        
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SHOW DATABASES LIKE 'papeleria_cueva'")
        db_exists = cursor.fetchone()
        
        if db_exists:
            print("Base de datos 'papeleria_cueva' existe")
            
            # Usar la base de datos
            cursor.execute("USE papeleria_cueva")
            
            # Verificar todas las tablas
            cursor.execute("SHOW TABLES")
            tablas = cursor.fetchall()
            print("Tablas en la base de datos:", [tabla[0] for tabla in tablas])
            
            # Verificar estructura de tabla usuarios si existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'papeleria_cueva' 
                AND table_name = 'usuarios'
            """)
            usuarios_existe = cursor.fetchone()[0] > 0
            
            if usuarios_existe:
                print("Tabla 'usuarios' existe")
                cursor.execute("DESCRIBE usuarios")
                estructura = cursor.fetchall()
                print("Estructura de la tabla usuarios:")
                for columna in estructura:
                    print(f"   {columna[0]} - {columna[1]}")
            else:
                print("Tabla 'usuarios' NO existe")
                
        else:
            print("Base de datos 'papeleria_cueva' NO existe")
            
    except Exception as e:
        print(f"Error en la verificación: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def crear_tabla_usuarios_manual():
    print("\n=== CREACIÓN MANUAL DE TABLA USUARIOS ===")
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='uea2025',
            database='papeleria_cueva'
        )
        
        cursor = conn.cursor()
        
        sql = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(sql)
        conn.commit()
        print("Tabla 'usuarios' creada manualmente")
        
    except Exception as e:
        print(f"Error al crear tabla manualmente: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    verificar_base_datos()
    crear_tabla_usuarios_manual()
    verificar_base_datos()  # Verificar again después de la creación