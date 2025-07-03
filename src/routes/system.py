from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from src.models.conversation import db, Patient
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional
import json
from src.models.conversation import db, Patient, Schedule
from src.main import csrf

from wtforms import StringField, PasswordField, DateField, TextAreaField, SelectField, DateTimeField
# ...



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

class PatientForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[DataRequired()])
    phone_number = StringField('Nº de WhatsApp (ex: 55169...)' , validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    birth_date = DateField('Data de Nascimento', validators=[Optional()])
    address = StringField('Endereço', validators=[Optional()])
    medical_history = TextAreaField('Anamnese / Histórico Médico', validators=[Optional()])

# --- Rotas do Sistema ---




# ... (depois da classe PatientForm)

# --- NOSSO NOVO FORMULÁRIO DE AGENDAMENTO ---
class ScheduleForm(FlaskForm):
    patient_id = SelectField('Paciente', coerce=int, validators=[DataRequired()])
    title = StringField('Título da Consulta', validators=[DataRequired()])
    start_time = DateTimeField('Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('Fim', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    notes = TextAreaField('Notas (Opcional)', validators=[Optional()])



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
# ... (código da rota add_patient) ...

# --- NOVAS ROTAS PARA EDITAR E APAGAR ---

@system_bp.route('/pacientes/editar/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    # Encontra o paciente no banco de dados ou retorna um erro 404 (Não Encontrado)
    patient = Patient.query.get_or_404(patient_id)
    # Cria o formulário, pré-preenchendo com os dados do paciente
    form = PatientForm(obj=patient)
    
    if form.validate_on_submit():
        # Atualiza os dados do paciente com os dados do formulário
        patient.full_name = form.full_name.data
        patient.phone_number = form.phone_number.data
        patient.email = form.email.data
        patient.birth_date = form.birth_date.data
        patient.address = form.address.data
        patient.medical_history = form.medical_history.data
        
        db.session.commit()
        flash(f'Dados de "{patient.full_name}" atualizados com sucesso!', 'success')
        return redirect(url_for('system.list_patients'))
        
    return render_template('patient_form.html', form=form, title=f"Editar Paciente: {patient.full_name}")

@system_bp.route('/pacientes/apagar/<int:patient_id>', methods=['GET']) # Usamos GET aqui porque o link é simples
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient_name = patient.full_name
    
    db.session.delete(patient)
    db.session.commit()
    
    flash(f'Paciente "{patient_name}" apagado com sucesso.', 'warning')
    return redirect(url_for('system.list_patients'))


@login_manager.unauthorized_handler
# ... (resto do ficheiro) ...

# ... (código da rota delete_patient) ...


# ... (código da rota delete_patient) ...

# --- NOVA ROTA PARA ADICIONAR CONSULTAS ---
@system_bp.route('/agenda/novo', methods=['POST']) # Apenas POST, pois será chamado por um formulário
@csrf.exempt
@login_required
def add_schedule():
    form = ScheduleForm()
    # Popula a lista de pacientes no formulário
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by('full_name').all()]
    
    if form.validate_on_submit():
        new_schedule = Schedule(
            patient_id=form.patient_id.data,
            title=form.title.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            notes=form.notes.data
        )
        db.session.add(new_schedule)
        db.session.commit()
        flash('Consulta agendada com sucesso!', 'success')
    else:
        # Se houver erros de validação, mostra-os
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'danger')

    return redirect(url_for('system.schedule'))

# --- ROTA DA AGENDA (EXISTENTE) ---
@system_bp.route('/agenda')
# ... (o resto do ficheiro continua igual) ...


# --- ROTA DA AGENDA (VERSÃO CORRIGIDA E FINAL) ---
@system_bp.route('/agenda')
@login_required
def schedule():
    all_schedules = Schedule.query.all()
    events = [s.to_dict() for s in all_schedules]
    events_json = json.dumps(events)
    
    all_patients = Patient.query.order_by('full_name').all()
    
    # AQUI ESTÁ A CHAVE: Criamos uma instância do formulário
    form = ScheduleForm()
    
    return render_template('schedule.html', 
                           events_json=events_json, 
                           patients=all_patients, 
                           form=form) # E passamo-la para o template


@login_manager.unauthorized_handler
# ... (resto do ficheiro) ...


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('system.login'))
@system_bp.route('/pacientes/novo', methods=['GET', 'POST'])
@login_required
def add_patient():
    form = PatientForm()
    if form.validate_on_submit():
        # Verifica se o número de telefone já existe
        existing_patient = Patient.query.filter_by(phone_number=form.phone_number.data).first()
        if existing_patient:
            flash('Já existe um paciente com este número de telefone.', 'danger')
            return render_template('patient_form.html', form=form, title="Adicionar Novo Paciente")

        # Cria uma nova instância do Paciente com os dados do formulário
        new_patient = Patient(
            full_name=form.full_name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            birth_date=form.birth_date.data,
            address=form.address.data,
            medical_history=form.medical_history.data
        )
           # Adiciona ao banco de dados
        db.session.add(new_patient)
        db.session.commit()
        
        flash(f'Paciente "{form.full_name.data}" adicionado com sucesso!', 'success')
        return redirect(url_for('system.list_patients'))
        
    return render_template('patient_form.html', form=form, title="Adicionar Novo Paciente")
