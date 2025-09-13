# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Producto(db.Model):
    # Nombre de la tabla en la base de datos.
    __tablename__ = 'productos'
    
    # Columna 'id': Clave primaria, se autoincrementa.
    id = db.Column(db.Integer, primary_key=True)
    
    # Columna 'nombre': Cadena de 120 caracteres, única y no nula.
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    
    # Columna 'cantidad': Entero, no nulo, con un valor por defecto de 0.
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    
    # Columna 'precio': Número de punto flotante, no nulo, con valor por defecto 0.0.
    precio = db.Column(db.Float, nullable=False, default=0.0)
    
    def __repr__(self):
        """
        Método de representación para depuración.
        """
        return f'<Producto {self.id} {self.nombre}>'

    def to_tuple(self):
        """
        Convierte la información del producto a una tupla.
        Útil para la visualización o exportación de datos.
        """
        return (self.id, self.nombre, self.cantidad, self.precio)