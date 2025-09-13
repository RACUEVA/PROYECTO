from models import db, Producto

class Inventario:

    def __init__(self, productos_dict=None):
        # Diccionario para almacenar objetos Producto, con la clave siendo el ID del producto.
        self.productos = productos_dict or {}  # dict[int, Producto]
        # Conjunto para almacenar los nombres de productos en minúsculas.
        # Permite verificar si un nombre ya existe en tiempo O(1).
        self.nombres = set(p.nombre.lower() for p in self.productos.values())

    @classmethod
    def cargar_desde_bd(cls):
    
        productos = Producto.query.all()              # Obtiene una lista de todos los objetos Producto de la BD.
        productos_dict = {p.id: p for p in productos} # Convierte la lista en un diccionario por ID.
        return cls(productos_dict)

    # --- Operaciones CRUD ---
    def agregar(self, nombre: str, cantidad: int, precio: float) -> Producto:
    
        if nombre.lower() in self.nombres:
            raise ValueError('Ya existe un producto con ese nombre.')
        
        # Crea una nueva instancia de Producto.
        p = Producto(nombre=nombre.strip(), cantidad=int(cantidad), precio=float(precio))
        
        # Agrega el nuevo producto a la sesión de la base de datos y lo guarda.
        db.session.add(p)
        db.session.commit()
        
        # Actualiza el inventario en memoria.
        self.productos[p.id] = p
        self.nombres.add(p.nombre.lower())
        return p

    def eliminar(self, id: int) -> bool:
        
        #Elimina un producto de la base de datos y del inventario.
        
        # Busca el producto en el diccionario o en la base de datos.
        p = self.productos.get(id) or Producto.query.get(id)
        if not p:
            return False
            
        # Elimina el producto de la sesión de la base de datos y guarda.
        db.session.delete(p)
        db.session.commit()
        
        # Elimina el producto del inventario en memoria.
        self.productos.pop(id, None)
        self.nombres.discard(p.nombre.lower())
        return True

    def actualizar(self, id: int, nombre=None, cantidad=None, precio=None) -> Producto | None:
        
        #Actualiza los datos de un producto existente en la base de datos y en el inventario.
        
        p = self.productos.get(id) or Producto.query.get(id)
        if not p:
            return None
            
        # Actualiza el nombre si se proporciona, validando duplicados.
        if nombre is not None:
            nuevo = nombre.strip()
            if nuevo.lower() != p.nombre.lower() and nuevo.lower() in self.nombres:
                raise ValueError('Ya existe otro producto con ese nombre.')
            self.nombres.discard(p.nombre.lower())
            p.nombre = nuevo
            self.nombres.add(p.nombre.lower())
        
        # Actualiza la cantidad y el precio si se proporcionan.
        if cantidad is not None:
            p.cantidad = int(cantidad)
        if precio is not None:
            p.precio = float(precio)
            
        # Guarda los cambios en la base de datos.
        db.session.commit()
        
        # Actualiza el diccionario en memoria.
        self.productos[p.id] = p
        return p

    # --- Consultas con colecciones ---
    def buscar_por_nombre(self, q: str):

        q = q.lower()
        # Filtra los valores del diccionario de productos.
        return sorted([p for p in self.productos.values() if q in p.nombre.lower()],
                        key=lambda x: x.nombre)

    def listar_todos(self):
        #Devuelve una lista de todos los productos en el inventario, ordenados por nombre.
        return sorted(self.productos.values(), key=lambda x: x.nombre)