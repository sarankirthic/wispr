from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

migrate.init_app(app, db, render_as_batch=True)

from app.routes import api
app.register_blueprint(api, url_prefix='/api')
