import os
from flask import Flask, jsonify, redirect, url_for
from flask_cors import CORS
from src.models.conversation import db
from src.routes.whatsapp import whatsapp_bp
from src.routes.system import system_bp, login_manager # Importamos as novas partes
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
CORS(app)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dentinhos-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dentinhos_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://')

# Inicializar banco de dados
db.init_app(app)

# Inicializar o LoginManager
login_manager.init_app(app)
login_manager.login_view = 'system.login' # Diz ao Flask-Login qual é a nossa página de login

# Registrar blueprints
app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
app.register_blueprint(system_bp, url_prefix='/system') # Registramos o novo blueprint do sistema

@app.route('/')
def home():
    # Agora a página inicial redireciona para o login do sistema
    return redirect(url_for('system.login'))

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Criar tabelas do banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
