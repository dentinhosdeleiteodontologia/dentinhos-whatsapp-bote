# Este é o NOVO CONTEÚDO para o ficheiro src/models/conversation.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(10), default='incoming') # incoming or outgoing
    status = db.Column(db.String(20), default='received') # received, processed, failed
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
    child_name = db.Column(db.String(100), nullable=False)
    child_age = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    preferred_period = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, cancelled
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

# --- NOSSA NOVA TABELA COMEÇA AQUI ---

class Patient(db.Model):
    __tablename__ = 'patient' # Define o nome da tabela explicitamente

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True) # unique=True garante que não há dois pacientes com o mesmo número
    email = db.Column(db.String(120), unique=True, nullable=True) # O email é opcional
    birth_date = db.Column(db.Date, nullable=True) # Guardar como data, não como texto
    medical_history = db.Column(db.Text, nullable=True) # Campo para a anamnese inicial
    address = db.Column(db.String(250), nullable=True) # Endereço do paciente
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Data de registo do paciente

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'email': self.email,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'medical_history': self.medical_history,
            'address': self.address,
            'created_at': self.created_at.isoformat()
        }
feat: Add Patient model to database
