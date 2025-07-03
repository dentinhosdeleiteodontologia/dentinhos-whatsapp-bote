# -*- coding: utf-8 -*-

# --- Importações Padrão ---
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash

# --- Importações de Extensões (Flask-Login, Flask-WTF) ---
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Optional

# --- Importações dos Modelos do Banco de Dados ---
from src.models.conversation import db, Patient, Schedule

# --- Criação do Blueprint ---
# O Blueprint agrupa todas as rotas relacionadas a este ficheiro.
system_bp = Blueprint('system', __name__)

# =============================================================================
# CONFIGURAÇÃO DE LOGIN E AUTENTICAÇÃO
# =============================================================================

login_manager = LoginManager()
login_manager.login_view = 'system.login'  # Redireciona para esta rota se o usuário não estiver logado

class User(UserMixin):
    """Classe de usuário simples para o Flask-Login."""
    def __init__(self, id):
        self.id = id

# Usuário hard-coded. No futuro, pode vir de um banco de dados.
ADMIN_USER = {'id': '1', 'username': 'admin', 'password': 'password123'}

@login_manager.user_loader
def load_user(user_id):
    """Carrega o usuário para a sessão."""
    if user_id == ADMIN_USER['id']:
        return User(user_id)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    """Lida com tentativas de acesso a páginas protegidas sem login."""
    flash('Você precisa fazer login para acessar esta página.', 'warning')
    return redirect(url_for('system.login'))

# =============================================================================
# DEFINIÇÃO DOS FORMULÁRIOS (WTForms)
# =============================================================================

class LoginForm(FlaskForm):
    """Formulário de login."""
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])

class PatientForm(FlaskForm):
    """Formulário para criar e editar pacientes."""
    full_name = StringField('Nome Completo', validators=[DataRequired()])
    phone_number = StringField('Nº de WhatsApp (ex: 55169...)', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    birth_date = DateField('Data de Nascimento', validators=[Optional()])
    address = StringField('Endereço', validators=[Optional()])
    medical_history = TextAreaField('Anamnese / Histórico Médico', validators=[Optional()])

class ScheduleForm(FlaskForm):
    """Formulário para criar e editar agendamentos."""
    patient_id = SelectField('Paciente', coerce=int, validators=[DataRequired(message="É obrigatório selecionar um paciente.")])
    title = StringField('Título da Consulta', validators=[DataRequired(message="O título é obrigatório.")])
    start_time = DateTimeField('Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data e hora de início são obrigatórias.")])
    end_time = DateTimeField('Fim', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data e hora de fim são obrigatórias.")])
    notes = TextAreaField('Notas (Opcional)', validators=[Optional()])

# =============================================================================
# ROTAS DO SISTEMA
# =============================================================================

# --- Rotas de Autenticação ---

@system_bp.route('/')
@login_required
def index():
    """Redireciona a rota base do sistema para a lista de pacientes."""
    return redirect(url_for('system.list_patients'))

@system_bp.route('/login', methods=['GET', 'POST'])
def login():
# ... (o resto do ficheiro continua igual)


@system_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == ADMIN_USER['username'] and form.password.data == ADMIN_USER['password']:
            user = User(ADMIN_USER['id'])
            login_user(user)
            return redirect(url_for('system.list_patients'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html', form=form)

@system_bp.route('/logout')
@login_required
def logout():
    """Faz o logout do usuário."""
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('system.login'))

# --- Rotas de Gestão de Pacientes (CRUD) ---

@system_bp.route('/pacientes')
@login_required
def list_patients():
    """Lista todos os pacientes."""
    patients = Patient.query.order_by(Patient.full_name).all()
    return render_template('patients.html', patients=patients)

@system_bp.route('/pacientes/novo', methods=['GET', 'POST'])
@login_required
def add_patient():
    """Página para adicionar um novo paciente."""
    form = PatientForm()
    if form.validate_on_submit():
        existing_patient = Patient.query.filter_by(phone_number=form.phone_number.data).first()
        if existing_patient:
            flash('Já existe um paciente com este número de telefone.', 'danger')
        else:
            new_patient = Patient(
                full_name=form.full_name.data,
                phone_number=form.phone_number.data,
                email=form.email.data,
                birth_date=form.birth_date.data,
                address=form.address.data,
                medical_history=form.medical_history.data
            )
            db.session.add(new_patient)
            db.session.commit()
            flash(f'Paciente "{new_patient.full_name}" adicionado com sucesso!', 'success')
            return redirect(url_for('system.list_patients'))
    return render_template('patient_form.html', form=form, title="Adicionar Novo Paciente")

@system_bp.route('/pacientes/editar/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    """Página para editar um paciente existente."""
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient) # Popula o objeto 'patient' com os dados do formulário
        db.session.commit()
        flash(f'Dados de "{patient.full_name}" atualizados com sucesso!', 'success')
        return redirect(url_for('system.list_patients'))
    return render_template('patient_form.html', form=form, title=f"Editar Paciente: {patient.full_name}")

@system_bp.route('/pacientes/apagar/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    """Ação para apagar um paciente."""
    patient = Patient.query.get_or_404(patient_id)
    patient_name = patient.full_name
    db.session.delete(patient)
    db.session.commit()
    flash(f'Paciente "{patient_name}" apagado com sucesso.', 'warning')
    return redirect(url_for('system.list_patients'))

# --- Rotas da Agenda ---

@system_bp.route('/agenda')
@login_required
def schedule():
    """Página principal da agenda, que exibe o calendário."""
    all_schedules = Schedule.query.all()
    events = [s.to_dict() for s in all_schedules]
    all_patients = Patient.query.order_by('full_name').all()
    form = ScheduleForm() # Cria um formulário vazio para o modal
    form.patient_id.choices = [(p.id, p.full_name) for p in all_patients]
    return render_template(
        'schedule.html',
        events_json=json.dumps(events),
        patients=all_patients,
        form=form
    )

@system_bp.route('/agenda/novo', methods=['POST'])
@login_required
def add_schedule():
    """Ação para adicionar uma nova consulta a partir do modal da agenda."""
    form = ScheduleForm()
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by('full_name').all()]
    if form.validate_on_submit():
        new_schedule = Schedule()
        form.populate_obj(new_schedule)
        db.session.add(new_schedule)
        db.session.commit()
        flash('Consulta agendada com sucesso!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'danger')
    return redirect(url_for('system.schedule'))
