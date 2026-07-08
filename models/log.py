from datetime import datetime
from db import db

class LogModel(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    activity = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
