from flask import Flask, render_template, redirect, jsonify, request, url_for, flash, send_from_directory, send_file
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from openpyxl import Workbook
from datetime import datetime
import pandas as pd
import string
import json
import io
import os

drivers = {
    "sqlite": "sqlite:///",
    "mariadb": "mysql+pymysql://",
}

# Inizializza app e servizi
app = Flask(__name__)
db_type = os.environ["DB_TYPE"]

if db_type not in drivers:
    app.logger.info("Tipo di database non supportato")
    raise RuntimeError("Tipo di database non supportato")

if db_type == "sqlite":
    uri = f"{drivers[db_type]}{os.environ['DB_NAME']}"
else:
    uri = (
        f"{drivers[db_type]}"
        f"{os.environ['DB_USER']}:"
        f"{os.environ['DB_PASSWORD']}@"
        f"{os.environ['DB_HOST']}:"
        f"{os.environ['DB_PORT']}/"
        f"{os.environ['DB_NAME']}"
    )
app.config["SQLALCHEMY_DATABASE_URI"] =  uri
app.config["SECRET_KEY"] = os.environ['SECRET_KEY']
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = u"Sessione scaduta!"

# Classi Database
class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

class Iscrizione(db.Model):
    __tablename__ = "iscrizioni"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, nullable=False)
    partecipante = db.Column(db.Integer, db.ForeignKey("partecipanti.id", name="fk_iscrizioni_partecipanti_id"), nullable=False)
    scelta_mattino = db.Column(db.Integer, db.ForeignKey("laboratori.id", name="fk_iscrizioni_laboratori_mattino_id"), nullable=False)
    scelta_pomeriggio = db.Column(db.Integer, db.ForeignKey("laboratori.id", name="fk_iscrizioni_laboratori_pomeriggio_id"), nullable=False)

class Partecipante(db.Model):
    __tablename__ = "partecipanti"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    cognome = db.Column(db.String(255), nullable=False)

class Laboratorio(db.Model):
    __tablename__ = "laboratori"
    id = db.Column(db.Integer, primary_key=True)
    posti = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)

class SysOption(db.Model):
    __tablename__ = "system_option"
    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.String(128), nullable=False)

migrate = Migrate(app, db)

@app.cli.command("init_db")
def init_db():
    try:
        db.session.add(User(username="admin", password=generate_password_hash("password")))
        print("Utente 'admin' creato con password: 'password'")
        db.session.commit()
        print("Operazione terminata correttamente!")
    except Exception as e:
        print("Qualcosa è andato storto!")
        print(e)

@app.cli.command("reset")
def crea_regione():
    print(f"Reset tool!")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("errore_generico.html"), 404

@app.errorhandler(405)
def internal_error(e):
    return render_template("errore_generico.html"), 405

@app.errorhandler(500)
def internal_error(e):
    return render_template("errore_generico.html"), 500

if __name__ == "__main__":
    app.run(port=8000, host="0.0.0.0")
