from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=0)])
    precio = DecimalField('Precio', validators=[DataRequired(), NumberRange(min=0)], places=2)
    submit = SubmitField('Guardar')

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(min=9, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Guardar')

# Nuevos formularios para login y registro
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegistroForm(FlaskForm):
    nombre = StringField('Nombre Completo', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')
    