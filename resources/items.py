from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema
from flask_jwt_extended import jwt_required,get_jwt
blp=Blueprint("items","items")


@blp.route("/item/<string:item_id>")
class Item(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item

    @jwt_required()
    def delete(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        jti = get_jwt()
        if jti.get("role")=="admin":
            db.session.delete(item)
            db.session.commit()
            return {"message": "Item deleted."}
        return {"message":"Only admin can delete"}

    @jwt_required()
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get(item_id)
        jti = get_jwt()
        if jti.get("role")=="admin":
            if item:
                item.price = item_data["price"]
                item.name = item_data["name"]
            else:
                item = ItemModel(id=item_id, **item_data)

            db.session.add(item)
            db.session.commit()

            return item
        abort (401,message="Only admin can update")

@blp.route("/item")
class ItemList(MethodView):
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()

    @jwt_required()
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        item = ItemModel(**item_data)
        jti = get_jwt()
        if jti.get("role")=="admin":
            try:
                db.session.add(item)
                db.session.commit()
            except SQLAlchemyError:
                abort(500, message="An error occurred while inserting the item.")

            return item
    
        abort (401,message="Only admin can post")