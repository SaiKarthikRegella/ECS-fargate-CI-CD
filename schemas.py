from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    email=fields.Str(required=True)
    role=fields.Str()

class PlainStoreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()

class PlainItemSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)

class ItemSchema(PlainItemSchema):
    store_id = fields.Int(required=True, load_only=True)
    store = fields.Nested(PlainStoreSchema(), dump_only=True)

class StoreSchema(PlainStoreSchema):
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)

class ItemUpdateSchema(Schema):
    name = fields.Str()
    price = fields.Float()


class CartItemSchema(Schema):
    item_id = fields.Int(required=True)
    quantity = fields.Int(required=True)

class CartSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    items = fields.List(fields.Nested(CartItemSchema))



