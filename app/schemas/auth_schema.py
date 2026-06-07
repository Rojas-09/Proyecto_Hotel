from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=100))
    apellido = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    telefono = fields.String(validate=validate.Length(max=20), load_default=None)
    documento_id = fields.String(validate=validate.Length(min=1, max=50), load_default=None)
    tipo_documento = fields.String(validate=validate.Length(max=10), load_default="CC")
    preferencias = fields.String(load_default=None)


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))
