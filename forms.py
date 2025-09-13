# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired

class ProductoForm(FlaskForm):
    
    # Campo para el nombre del producto.
    # DataRequired: Asegura que el campo no esté vacío.
    # Length: Limita el nombre a un máximo de 120 caracteres.
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    
    # Campo para la cantidad del producto.
    # DataRequired: Asegura que el campo no esté vacío.
    # NumberRange: Valida que la cantidad sea un número entero no negativo.
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=0)])
    
    # Campo para el precio del producto.
    # DecimalField: Representa un número decimal.
    # places=2: Limita el valor a dos decimales.
    # NumberRange: Valida que el precio sea un número no negativo.
    precio = DecimalField('Precio', places=2, validators=[DataRequired(), NumberRange(min=0)])
    
    # Botón para enviar el formulario.
    submit = SubmitField('Guardar')