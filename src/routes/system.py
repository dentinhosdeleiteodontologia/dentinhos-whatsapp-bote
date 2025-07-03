# src/routes/system.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Optional
import json

from src.models.conversation import db, Patient, Schedule

# --- Blueprint ---
system_bp = Blueprint('system', __name__)

# --- Formulários ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class PatientForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[DataRequired()])
    phone_number = StringField('Nº de WhatsApp (ex: 55169...)', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    birth_date = DateField('Data de Nascimento', validators=[Optional()])
    address = StringField('Endereço', validators=[Optional()])
    medical_history = TextAreaField('Anamnese / Histórico Médico', validators=[Optional()])

class ScheduleForm(FlaskForm):
    patient_id = SelectField('Paciente', coerce=int, validators=[DataRequired(message="Por favor, selecione um paciente.")])
    title = StringField('Título da Consulta', validators=[DataRequired(message="O título é obrigatório.")])
    start_time = DateTimeField('Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data de início é obrigatória.")])
    end_time = DateTimeField('Fim', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data de fim é obrigatória.")])
    notes = TextAreaField('Notas (Opcional)', validators=[Optional()])

# --- Rotas de Pacientes ---
@system_bp.route('/')
@system_bp.route('/pacientes')
@login_required
def list_patients():
    patients = Patient.query.order_by(Patient.full_name).all()
    return render_template('patients.html', patients=patients)

@system_bp.route('/pacientes/novo', methods=['GET', 'POST'])
@login_required
def add_patient():
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
            flash(f'Paciente "{form.full_name.data}" adicionado com sucesso!', 'success')
            return redirect(url_for('system.list_patients'))
    return render_template('patient_form.html', form=form, title="Adicionar Novo Paciente")

@system_bp.route('/pacientes/editar/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash(f'Dados de "{patient.full_name}" atualizados com sucesso!', 'success')
        return redirect(url_for('system.list_patients'))
    return render_template('patient_form.html', form=form, title=f"Editar Paciente: {patient.full_name}")

@system_bp.route('/pacientes/apagar/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
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
    all_schedules = Schedule.query.all()
    events = [s.to_dict() for s in all_schedules]
    events_json = json.dumps(events)
    form = ScheduleForm()
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by('full_name').all()]
    return render_template('schedule.html', events_json=events_json, form=form)

@system_bp.route('/agenda/novo', methods=['POST'])
@login_required
def add_schedule():
    form = ScheduleForm()
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
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'danger')
    return redirect(url_for('system.schedule'))

