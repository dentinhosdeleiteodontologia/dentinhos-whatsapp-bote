# main.py
# TESTE DE DIAGNÓSTICO: Desativar completamente o CSRF para isolar o problema.

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
# from flask_wtf.csrf import CSRFProtect # <-- PASSO 1: Comentar a importação

# --- Configuração da Aplicação ---
app = Flask(__name__)

db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'uma-chave-secreta-muito-segura-para-desenvolvimento')

# --- Inicialização das Extensões ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça login para aceder a esta página."

# --- PASSO 2: Comentar a inicialização e a isenção do CSRF ---
# csrf = CSRFProtect(app)

# --- Modelos e Blueprints ---
from src.models.user import User
from src.models.conversation import Conversation, Patient, Schedule

from src.routes.auth import auth_bp
from src.routes.system import system_bp
from src.routes.whatsapp import whatsapp_bp

# csrf.exempt(whatsapp_bp) # <-- PASSO 3: Comentar a isenção

app.register_blueprint(auth_bp)
app.register_blueprint(system_bp)
app.register_blueprint(whatsapp_bp)

# --- Configuração do Login Manager ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Rotas Principais ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/health')
def health_check():
    return "OK", 200

# --- Criação do Banco de Dados ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
