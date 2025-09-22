# models_user.py
from flask_login import UserMixin
from conexion.conexion import conexion, cerrar_conexion

class Usuario(UserMixin):
    def __init__(self, id, nombre, email, password):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def get(user_id):
        conn = conexion()
        if conn is None:
            print(f"No se pudo conectar para obtener usuario ID: {user_id}")
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                print(f"Usuario encontrado: ID {user_data['id']} - {user_data['email']}")
                return Usuario(
                    id=user_data['id'],
                    nombre=user_data['nombre'],
                    email=user_data['email'],
                    password=user_data['password']
                )
            print(f"Usuario no encontrado ID: {user_id}")
            return None
        except Exception as e:
            print(f"Error al obtener usuario ID {user_id}: {e}")
            return None
        finally:
            cerrar_conexion(conn)
    
    @staticmethod
    def get_by_email(email):
        conn = conexion()
        if conn is None:
            print(f"No se pudo conectar para obtener usuario email: {email}")
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                print(f"Usuario encontrado por email: {user_data['email']}")
                return Usuario(
                    id=user_data['id'],
                    nombre=user_data['nombre'],
                    email=user_data['email'],
                    password=user_data['password']
                )
            print(f"Usuario no encontrado email: {email}")
            return None
        except Exception as e:
            print(f"Error al obtener usuario por email {email}: {e}")
            return None
        finally:
            cerrar_conexion(conn)
            