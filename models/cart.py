from db import db
from sqlalchemy.orm import relationship
from flask_jwt_extended import get_jwt_identity

class CartModel(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)  # Each user has one cart
    items = relationship("CartItemModel", back_populates="cart", cascade="all, delete")

class CartItemModel(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cart = relationship("CartModel", back_populates="items")
    item = relationship("ItemModel")
