from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from src.models.conversation import db, Patient
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

system_bp = Blueprint('system', __name__)

# --- Configuração do Login ---
login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Usuário hard-coded por enquanto. No futuro, podemos criar uma tabela de usuários.
# Lembre-se de trocar esta senha por uma mais segura nas variáveis de ambiente!
ADMIN_USER = {'id': '1', 'username': 'admin', 'password': 'password123'}

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER['id']:
        return User(user_id)
    return None

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# --- Rotas do Sistema ---

@system_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == ADMIN_USER['username'] and form.password.data == ADMIN_USER['password']:
            user = User(ADMIN_USER['id'])
            login_user(user)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('system.list_patients'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html', form=form)

@system_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('system.login'))

@system_bp.route('/pacientes')
@login_required
def list_patients():
    patients = Patient.query.order_by(Patient.full_name).all()
    return render_template('patients.html', patients=patients)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('system.login'))
