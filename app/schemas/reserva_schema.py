from marshmallow import Schema, fields


class CrearReservaSchema(Schema):
    id_habitacion = fields.Integer(required=True, strict=True)
    fecha_entrada = fields.Date(required=True, format="%Y-%m-%d")
    fecha_salida = fields.Date(required=True, format="%Y-%m-%d")
    id_huesped = fields.Integer(strict=True, load_default=None)
