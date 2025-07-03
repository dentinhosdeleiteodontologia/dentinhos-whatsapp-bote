import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

# Importa as configurações do banco de dados e os modelos
from src.models.conversation import db

# Cria a aplicação Flask
app = Flask(__name__)

# --- CONFIGURAÇÕES ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dentinhos-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dentinhos_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True # Garante que o CSRF está ativo

# Corrige URL do PostgreSQL no Heroku/Render se necessário
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://')

# --- INICIALIZAÇÃO DOS MÓDULOS ---
db.init_app(app)
CORS(app)
csrf = CSRFProtect(app) # Inicializa o CSRF aqui

# --- REGISTO DOS BLUEPRINTS (ROTAS) ---
# Importa os blueprints DEPOIS de a app estar configurada
from src.routes.whatsapp import whatsapp_bp
from src.routes.system import system_bp, login_manager

app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
app.register_blueprint(system_bp, url_prefix='/system')

# Inicializa o LoginManager com a app
login_manager.init_app(app)

# --- ROTAS GERAIS DA APLICAÇÃO ---
@app.route('/')
def home():
    return jsonify({
        "message": "Bot WhatsApp Dentinhos de Leite Odontologia",
        "status": "online",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# --- CRIAÇÃO DAS TABELAS ---
with app.app_context():
    db.create_all()

# --- EXECUÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
