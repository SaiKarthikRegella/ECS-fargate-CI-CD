from db import db 

class Usermodel(db.Model):
    __tablename__= "users"
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(80),unique=True)
    password=db.Column(db.String(), nullable=False)
    email=db.Column(db.String())
    role=db.Column(db.String())