# src/models/conversation.py
# Versão 2.0 - Fase 3: Adicionada a tabela Schedule

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(10), default='incoming')
    status = db.Column(db.String(20), default='received')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    child_name = db.Column(db.String(100), nullable=True)
    child_age = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    preferred_period = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'child_name': self.child_name,
            'child_age': self.child_age,
            'reason': self.reason,
            'preferred_period': self.preferred_period,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(200), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relação com as consultas
    schedules = db.relationship('Schedule', backref='patient', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'email': self.email,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'address': self.address,
            'medical_history': self.medical_history,
            'created_at': self.created_at.isoformat()
        }

# --- NOSSA NOVA TABELA DE AGENDAMENTOS ---
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': f"{self.title} ({self.patient.full_name})", # Mostra o nome do paciente no evento
            'start': self.start_time.isoformat(),
            'end': self.end_time.isoformat(),
            'notes': self.notes,
            'patient_name': self.patient.full_name
        }
