# src/main.py
# Versão 2.0 - Fase 2 Concluída

import os
from flask import Flask, redirect, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_login import current_user

from src.models.conversation import db
from src.routes.whatsapp import whatsapp_bp
from src.auth import auth_bp, login_manager
from src.routes.system import system_bp # Importamos o nosso novo módulo do sistema

# --- Configuração da Aplicação ---
app = Flask(__name__)
CORS(app)
csrf = CSRFProtect(app)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dentinhos-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dentinhos_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db_uri = app.config['SQLALCHEMY_DATABASE_URI']
if db_uri.startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace('postgres://', 'postgresql://', 1)

# Inicializar Extensões
db.init_app(app)
login_manager.init_app(app)

# --- Registro dos Blueprints ---
app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
app.register_blueprint(auth_bp)
app.register_blueprint(system_bp) # Registamos o nosso novo módulo do sistema

# --- Rota Principal ---
@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Se estiver logado, a página principal agora é a lista de pacientes
    return redirect(url_for('system.list_patients'))

# --- Comandos do Flask ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
