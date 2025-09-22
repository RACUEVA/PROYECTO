from conexion.conexion import conexion, cerrar_conexion

def test_conexion():
    conn = conexion()
    if conn:
        print("✓ Conexión exitosa")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        print("Tablas en la base de datos:", tablas)
        cerrar_conexion(conn)
    else:
        print("✗ Error de conexión")

if __name__ == '__main__':
    test_conexion()