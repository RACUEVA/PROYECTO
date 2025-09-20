from models import db, Producto
import csv

class Inventario:

    def __init__(self, productos_dict=None):
        self.productos = productos_dict or {}
        self.nombres = set(p.nombre.lower() for p in self.productos.values())

    @classmethod
    def cargar_desde_bd(cls):
        productos = Producto.query.all()
        productos_dict = {p.id: p for p in productos}
        return cls(productos_dict)

    # --- Operaciones CRUD ---
    def agregar(self, nombre: str, cantidad, precio) -> Producto:
        if nombre.lower() in self.nombres:
            raise ValueError('Ya existe un producto con ese nombre.')
        
        # Convierte la cantidad a entero y el precio a flotante
        try:
            cantidad_num = int(cantidad)
            precio_num = float(precio)
        except (ValueError, TypeError):
            raise TypeError("La cantidad y el precio deben ser números.")

        p = Producto(nombre=nombre.strip(), cantidad=cantidad_num, precio=precio_num)
        
        db.session.add(p)
        db.session.commit()
        
        self.productos[p.id] = p
        self.nombres.add(p.nombre.lower())
        return p

    def eliminar(self, id: int) -> bool:
        p = self.productos.pop(id, None) or Producto.query.get(id)
        if p:
            db.session.delete(p)
            db.session.commit()
            if p.nombre.lower() in self.nombres:
                self.nombres.discard(p.nombre.lower())
            return True
        return False

    def actualizar(self, id: int, nombre=None, cantidad=None, precio=None) -> Producto:
        p = self.productos.get(id) or Producto.query.get(id)
        if not p:
            return None
            
        if nombre is not None:
            nuevo = nombre.strip()
            if nuevo.lower() != p.nombre.lower() and nuevo.lower() in self.nombres:
                raise ValueError('Ya existe otro producto con ese nombre.')
            self.nombres.discard(p.nombre.lower())
            p.nombre = nuevo
            self.nombres.add(p.nombre.lower())
        
        # Convierte la cantidad a entero y el precio a flotante si se proporcionan
        if cantidad is not None:
            try:
                p.cantidad = int(cantidad)
            except (ValueError, TypeError):
                raise TypeError("La cantidad debe ser un número.")
        if precio is not None:
            try:
                p.precio = float(precio)
            except (ValueError, TypeError):
                raise TypeError("El precio debe ser un número.")
            
        db.session.commit()
        
        self.productos[p.id] = p
        return p

    # --- Consultas con colecciones ---
    def buscar_por_nombre(self, q: str):
        q = q.lower()
        return sorted([p for p in self.productos.values() if q in p.nombre.lower()],
                        key=lambda x: x.nombre)

    def listar_todos(self):
        return sorted(self.productos.values(), key=lambda p: p.nombre)

    @classmethod
    def cargar_desde_csv(cls, filepath):
        productos = {}
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                p = Producto(
                    nombre=row['nombre'],
                    cantidad=int(row['cantidad']),
                    precio=float(row['precio'])
                )
                productos[len(productos) + 1] = p
        return cls(productos)

    @classmethod
    def cargar_desde_json(cls, filepath):
        pass # Implementar lógica para cargar desde JSON
    
    @classmethod
    def guardar_en_json(cls, filepath, productos):
        pass # Implementar lógica para guardar en JSON

    @classmethod
    def guardar_en_csv(cls, filepath, productos):
        pass # Implementar lógica para guardar en CSV
