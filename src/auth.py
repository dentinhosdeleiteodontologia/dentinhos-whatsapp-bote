# src/auth.py
# Versão 1.4 - Correção Final da Rota de Login

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

# --- Configuração do Login ---
auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

# AQUI ESTÁ A CORREÇÃO PRINCIPAL:
# A "vista de login" (login_view) deve apontar para a rota dentro deste blueprint: 'auth.login'
login_manager.login_view = 'auth.login'
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

# --- Formulário de Login ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# --- Rotas de Login/Logout ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('system.list_patients'))
    
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == ADMIN_USER['username'] and form.password.data == ADMIN_USER['password']:
            user = User(ADMIN_USER['id'])
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('system.list_patients'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('auth.login'))
