# src/auth.py
# Módulo de Autenticação - Fase 1

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

# --- Configuração do Login ---
# Criamos um "blueprint", um módulo para organizar as rotas de autenticação
auth_bp = Blueprint('auth', __name__)

# Criamos o gestor de login
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Diz ao sistema qual é a página de login
login_manager.login_message = "Por favor, faça o login para aceder a esta página."
login_manager.login_message_category = "info"

# --- Modelo de Utilizador Simples ---
# Por agora, o nosso utilizador é um objeto simples em memória
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Os dados do nosso único administrador. No futuro, isto pode vir de um banco de dados.
ADMIN_USER = {'id': '1', 'username': 'admin', 'password': 'password123'}

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER['id']:
        return User(user_id)
    return None

# --- Formulário de Login ---
class LoginForm(FlaskForm):
    username = StringField('Utilizador', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])

# --- Rotas de Login/Logout ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se o utilizador já estiver logado, não o deixamos ver a página de login novamente
    if current_user.is_authenticated:
        return redirect(url_for('home')) # Vamos criar a rota 'home' no main.py

    form = LoginForm()
    if form.validate_on_submit():
        # Verifica se o utilizador e a senha estão corretos
        if form.username.data == ADMIN_USER['username'] and form.password.data == ADMIN_USER['password']:
            user = User(ADMIN_USER['id'])
            login_user(user)
            # Redireciona para a página principal do sistema após o login
            return redirect(url_for('home'))
        else:
            flash('Utilizador ou senha inválidos.', 'danger')
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required # Só quem está logado pode fazer logout
def logout():
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'success')
    return redirect(url_for('auth.login'))
