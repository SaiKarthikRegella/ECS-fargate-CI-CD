from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity,get_jwt
from models import CartModel, CartItemModel, ItemModel
from db import db
from schemas import CartItemSchema, CartSchema

blp = Blueprint("cart", "cart", description="Operations on user carts")

@blp.route("/cart")
class CartView(MethodView):
    @jwt_required()
    @blp.response(200, CartSchema)
    def get(self):
        # Identity is stored as a string in the JWT (PyJWT requires `sub` to
        # be a string) — cast back to int to match the Integer column.
        user_id = int(get_jwt_identity())
        cart = CartModel.query.filter_by(user_id=user_id).first()
        if not cart:
            # No cart yet for this user — treat as an empty cart rather than
            # a 404, so client code doesn't need a special case for "new user".
            return {"id": None, "user_id": user_id, "items": []}
        return cart

@blp.route("/cart/add")
class CartAdd(MethodView):
    @jwt_required()
    @blp.arguments(CartItemSchema)
    def post(self, cart_item_data):
        user_id = int(get_jwt_identity())
        cart = CartModel.query.filter_by(user_id=user_id).first()

        # Create a new cart if it doesn't exist
        if not cart:
            cart = CartModel(user_id=user_id)
            db.session.add(cart)

        # Check if item exists
        item = ItemModel.query.get(cart_item_data["item_id"])
        if not item:
            abort(404, message="Item not found.")

        # Add item to the cart with specified quantity
        cart_item = CartItemModel(
            cart_id=cart.id, 
            item_id=cart_item_data["item_id"], 
            quantity=cart_item_data["quantity"]
        )
        db.session.add(cart_item)
        db.session.commit()

        return {"message": "Item added to cart."}, 201

@blp.route("/cart/remove/<int:item_id>")
class CartRemoveItem(MethodView):
    @jwt_required()
    def delete(self, item_id):
        user_id = int(get_jwt_identity())
        cart = CartModel.query.filter_by(user_id=user_id).first()
        if not cart:
            abort(404, message="Cart not found.")

        cart_item = CartItemModel.query.filter_by(
            cart_id=cart.id, item_id=item_id
        ).first()
        if not cart_item:
            abort(404, message="Item not found in cart.")

        db.session.delete(cart_item)
        db.session.commit()

        return {"message": "Item removed from cart."}, 200
    
@blp.route("/cart/checkout")
class CartCheckout(MethodView):
    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        cart = CartModel.query.filter_by(user_id=user_id).first()
        jti = get_jwt()
        if jti.get("role")=="guest":
            abort(400, message="You are a guest")
        if not cart or not cart.items:
            abort(400, message="Your cart is empty.")

        # Clear the cart after checkout
        db.session.delete(cart)
        db.session.commit()

        return {"message": "Checkout successful."}, 200
