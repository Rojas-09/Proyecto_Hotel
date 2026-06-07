from marshmallow import Schema, fields, validate


class PagoGarantiaSchema(Schema):
    metodo = fields.String(required=True, validate=validate.Length(min=1))
    payment_method_id = fields.String(load_default=None)


class PagoLiquidacionSchema(Schema):
    metodo = fields.String(required=True, validate=validate.Length(min=1))
    payment_method_id = fields.String(load_default=None)
