from flask_smorest import Blueprint,abort
from db import db
from flask.views import MethodView
from schemas import StoreSchema
from models import StoreModel
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from flask_jwt_extended import jwt_required, get_jwt

blp=Blueprint("store","store")

@blp.route("/store/<string:store_id>")
class Store(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store
    @jwt_required()
    def delete(self, store_id):
        claims = get_jwt()
        if claims.get("role") != "admin":
            abort(403, message="Admin privileges required to delete a store.")
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted"}, 200


@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @jwt_required()
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        claims = get_jwt()
        if claims.get("role") != "admin":
            abort(403, message="Admin privileges required to post a store.")
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(
                400,
                message="A store with that name already exists.",
            )
        except SQLAlchemyError:
            abort(500, message="An error occurred creating the store.")

        return store