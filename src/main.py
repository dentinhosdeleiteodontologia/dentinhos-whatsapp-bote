# src/main.py
# Versão 1.2 - Arquitetura de Login e Rotas Corrigida

import os
from flask import Flask, jsonify, redirect, url_for, render_template, flash
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

from src.models.conversation import db
from src.routes.whatsapp import whatsapp_bp
from src.routes.system import system_bp

# --- Configuração da Aplicação ---
app = Flask(__name__)
CORS(app)
csrf = CSRFProtect(app)

# Configurações
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dentinhos-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dentinhos_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Corrigir URL do PostgreSQL no Heroku/Render
db_uri = app.config['SQLALCHEMY_DATABASE_URI']
if db_uri.startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace('postgres://', 'postgresql://', 1)

# Inicializar Banco de Dados
db.init_app(app)

# --- Configuração do Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Aponta para a rota de login principal
login_manager.login_message = "Por favor, faça o login para aceder a esta página."
login_manager.login_message_category = "info"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

ADMIN_USER = {'id': '1', 'username': 'admin', 'password': 'password123'}

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER['id']:
        return User(user_id)
    return None

# --- Registro dos Blueprints ---
app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
app.register_blueprint(system_bp) # O prefixo '/system' já está no blueprint

# --- Rotas Principais (Login e Navegação) ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

@app.route('/')
def home():
    # Redireciona para a página de login se não estiver logado, ou para a lista de pacientes se estiver
    if current_user.is_authenticated:
        return redirect(url_for('system.list_patients'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('system.list_patients'))
    
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == ADMIN_USER['username'] and form.password.data == ADMIN_USER['password']:
            user = User(ADMIN_USER['id'])
            login_user(user)
            # Redireciona para a próxima página ou para a lista de pacientes
            next_page = request.args.get('next')
            return redirect(next_page or url_for('system.list_patients'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# --- Comandos do Flask ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
