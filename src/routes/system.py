# src/routes/system.py
# Módulo do Sistema de Gestão - Fase 3

import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Optional

from src.models.conversation import db, Patient, Schedule

# --- Blueprint ---
system_bp = Blueprint('system', __name__, url_prefix='/system')

# --- Formulários ---
class PatientForm(FlaskForm):
    full_name = StringField('Nome Completo', validators=[DataRequired(message="O nome é obrigatório.")])
    phone_number = StringField('Nº de WhatsApp (ex: 55169...)', validators=[DataRequired(message="O telefone é obrigatório.")])
    email = StringField('Email', validators=[Optional(), Email(message="Email inválido.")])
    birth_date = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[Optional()])
    address = StringField('Endereço', validators=[Optional()])
    medical_history = TextAreaField('Anamnese / Histórico Médico', validators=[Optional()])

class ScheduleForm(FlaskForm):
    patient_id = SelectField('Paciente', coerce=int, validators=[DataRequired(message="Selecione um paciente.")])
    title = StringField('Título da Consulta', validators=[DataRequired(message="O título é obrigatório.")])
    start_time = DateTimeField('Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data de início é obrigatória.")])
    end_time = DateTimeField('Fim', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message="A data de fim é obrigatória.")])
    notes = TextAreaField('Notas (Opcional)', validators=[Optional()])

# --- Rotas de Pacientes (CRUD) ---
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
        existing_patient_phone = Patient.query.filter_by(phone_number=form.phone_number.data).first()
        existing_patient_email = Patient.query.filter(Patient.email.isnot(None), Patient.email == form.email.data).first()
        if existing_patient_phone:
            flash('Já existe um paciente com este número de telefone.', 'danger')
        elif form.email.data and existing_patient_email:
            flash('Já existe um paciente com este email.', 'danger')
        else:
            new_patient = Patient()
            form.populate_obj(new_patient)
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
