import os
from flask_smorest import Blueprint,abort
from flask import jsonify
from db import db
from flask.views import MethodView
from models import Usermodel,LogModel
from schemas import UserSchema
from blocklist import BlockList
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,get_jwt
)
from passlib.hash import pbkdf2_sha256
from cryptography.fernet import Fernet


userblp=Blueprint("user","user")
# Dev-only fallback so `pytest` works with zero setup. In ECS this comes from
# the task definition / Secrets Manager, same as JWT_SECRET_KEY in app.py.
encryption_key = os.environ.get(
    "CART_ENCRYPTION_KEY", "n_tN5SpiJIvaJIi_jVg-AU8N7QaEeUWcawQSHEzP9RY="
)
cipher = Fernet(encryption_key)

@userblp.route("/register")
class USer(MethodView):
    @userblp.arguments(UserSchema)
    def post(self,user_data):
        if Usermodel.query.filter(Usermodel.username==user_data["username"]).first():
            abort(400,message="User alredy exists")
        hash_password= pbkdf2_sha256.hash(user_data["password"])
        encry_password=cipher.encrypt(hash_password.encode()).decode()
        user=Usermodel(username=user_data["username"], password=encry_password,email=user_data["email"],role=user_data["role"])
        db.session.add(user)
        db.session.commit()
        # NOTE: previously this returned the plaintext password AND the
        # encrypted hash in the response body. Never echo credentials back
        # to the caller — removed both fields.
        return {"message": "User created successfully"}, 201
    

@userblp.route("/user")
class alluser(MethodView):
    @userblp.response(200,UserSchema(many=True))
    def get(self):
       user=Usermodel.query.all()
       return user

@userblp.route("/login")
class UserLogin(MethodView):
    @userblp.arguments(UserSchema)
    def post(self, user_data):
        # Retrieve user by username
        user = Usermodel.query.filter(Usermodel.username == user_data["username"]).first()
        if user is None:
            abort(401, message="User not registered.")

        # Decrypt the stored password
        try:
            decrypted_password = cipher.decrypt(user.password.encode()).decode()
        except Exception as e:
            abort(500, message="Error decrypting password.")

        # Verify the provided password against the decrypted password
        if user and pbkdf2_sha256.verify(user_data["password"], decrypted_password):
            # PyJWT requires the `sub` claim to be a string, so the identity
            # is stringified here and cast back to int wherever it's read
            # (get_jwt_identity() below, and in app.py / resources/cart.py).
            access_token = create_access_token(identity=str(user.id), fresh=True, additional_claims={"role": user.role})
            refresh_token = create_refresh_token(str(user.id))

            # Log the login activity
            log = LogModel(username=user.username, activity="User logged in")
            db.session.add(log)
            db.session.commit()

           
            return {"access_token": access_token, "refresh_token": refresh_token}, 200
         
        abort(401, message="Invalid credentials.")


@userblp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        user_id = int(get_jwt_identity())
        user = Usermodel.query.get(user_id)
        if user:
            # Log the logout activity
            log = LogModel(username=user.username, activity="User logged out")
            db.session.add(log)
            db.session.commit()

        BlockList.add(jti)
        return {"message": "Successfully logged out"}, 200


@userblp.route("/user/<int:user_id>")
class User(MethodView):
  
    @userblp.response(200, UserSchema)
    def get(self, user_id):
        user = Usermodel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = Usermodel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200




@userblp.route("/logs")
class UserLogs(MethodView):
    @jwt_required()
    def get(self):
        jti = get_jwt()
        # user_id = get_jwt_identity()
        # user = Usermodel.query.get(user_id)
        if jti.get("role") != "admin":
            abort(403, message="Admins only.")
            

        logs = LogModel.query.order_by(LogModel.timestamp.desc()).all()
        return [{"username": log.username, "activity": log.activity, "timestamp": log.timestamp.isoformat()} for log in logs], 200


@userblp.route("/allpassword")
class password(MethodView):
    @userblp.response(200, UserSchema(many=True))
    def get(self):
        users=Usermodel.query.all()
        return users