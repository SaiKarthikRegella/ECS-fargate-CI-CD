import os
from flask import Flask,jsonify,request
from flask_jwt_extended import JWTManager
from flask_smorest import Api
from db import db
from resources.user import userblp as UserBlueprint 
from resources.store import blp as StoreBlueprint
from resources.items import blp as ItemBluePrint
from resources.cart import blp as cartblp
from blocklist import BlockList
from flask_jwt_extended import get_jwt_identity
from models import Usermodel, LogModel
from resources.rate_limiter import check_rate_limit, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

def create_app(db_url=None):
    app = Flask(__name__)
    app.config["API_TITLE"] = "ITS_Project"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///data.db"
    # JWT_SECRET_KEY now comes from the environment. The fallback below is ONLY
    # for local dev/tests so `pytest` works with zero setup. In ECS this gets
    # injected via the task definition (or Secrets Manager) — never baked into
    # the image.
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", "dev-only-insecure-key-do-not-use-in-prod"
    )
    app.config["JWT_ALGORITHM"] = "HS256"
    db.init_app(app)

    @app.route("/health")
    def health():
        # Unauthenticated, no DB hit — this is what the ALB target group polls.
        # Keep it cheap; if it ever needs a DB check, catch failures and return 503.
        return jsonify({"status": "ok"}), 200

    @app.before_request
    def log_request_data():
        if request.path == "/health":
            return  # don't let ALB health checks (every ~30s) flood the logs table
        username = "Anonymous"
        if request.headers.get("Authorization"):
            try:
                user_id = int(get_jwt_identity())
                username = Usermodel.query.get(user_id).username
            except:
                pass  # Handle cases where the token or user is invalid

        log = LogModel(
            username=username,
            activity=f"Request to {request.endpoint} with data: {request.json if request.is_json else request.args}"
        )
        db.session.add(log)
        db.session.commit()

    # Middleware to log responses
    @app.after_request
    def log_response_data(response):
        if request.path == "/health":
            return response
        username = "Anonymous"
        if request.headers.get("Authorization"):
            try:
                user_id = int(get_jwt_identity())
                username = Usermodel.query.get(user_id).username
            except:
                pass  # Handle cases where the token or user is invalid

        log = LogModel(
            username=username,
            activity=f"Response from {request.endpoint} with status: {response.status_code}"
        )
        db.session.add(log)
        db.session.commit()
        return response
    jwt=JWTManager(app)
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BlockList
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )
    
    @app.before_request
    def apply_rate_limit():
        if request.path == '/health':
            return
        # Disable rate limiting in test environment
        if app.config.get('TESTING'):
            return
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        if not check_rate_limit(client_ip):
            return jsonify({
                'error': 'rate_limit_exceeded',
                'message': f'Limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s'
            }), 429
    with app.app_context():
        db.create_all()
    api = Api(app)
    api.register_blueprint(UserBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(ItemBluePrint)
    api.register_blueprint(cartblp)


    

    return app

if __name__ == "__main__":
    app=create_app()
    app.run(ssl_context=("cert.pem", "key.pem"), debug=True,host="127.0.0.1", port=5000)
