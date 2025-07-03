# src/routes/whatsapp.py
# Correção: Reverter a rota do webhook para o padrão /webhook

from flask import Blueprint, request, jsonify
from src.models.conversation import db, Conversation, Appointment
from src.services.bot_logic import BotLogic
from src.services.whatsapp_service import send_whatsapp_message
import json
import os

# A alteração está aqui: removemos o url_prefix para que as rotas sejam registadas na raiz.
whatsapp_bp = Blueprint('whatsapp', __name__)
bot_logic = BotLogic()

# Esta rota agora será /webhook
@whatsapp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificação do webhook do WhatsApp Business API"""
    # Usamos um valor padrão seguro caso a variável de ambiente não exista
    verify_token = os.environ.get('VERIFY_TOKEN', 'DENTINHOS_TOKEN_SEGURO_FALLBACK')
    
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            print("SUCESSO: Webhook verificado com sucesso!")
            return challenge
        else:
            print(f"FALHA: Webhook não verificado. Token recebido: '{token}', Token esperado: '{verify_token}'")
            return "Token de verificação inválido", 403
    
    return "Parâmetros de verificação em falta", 400

# Esta rota agora será /webhook
@whatsapp_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """Processa mensagens recebidas do WhatsApp"""
    try:
        data = request.get_json()
        
        if not data:
            print("ERRO: Webhook recebido sem dados (payload vazio).")
            return jsonify({"status": "error", "message": "Dados inválidos"}), 400
        
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') == 'messages':
                            process_message(change['value'])
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao processar webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_message(message_data):
    """Processa uma mensagem individual"""
    try:
        if 'messages' in message_data:
            for message in message_data['messages']:
                if message.get('type') != 'text':
                    continue

                phone_number = message['from']
                message_text = message.get('text', {}).get('body', '')
                
                conversation = Conversation(
                    phone_number=phone_number,
                    message=message_text,
                    message_type='incoming',
                    status='received'
                )
                db.session.add(conversation)
                db.session.commit()
                
                response = bot_logic.process_message(message_text, phone_number)
                
                if response:
                    conversation.response = response
                    conversation.status = 'processed'
                    db.session.commit()
                    
                    send_whatsapp_message(phone_number, response)
                    print(f"Resposta enviada para {phone_number}.")
                
    except Exception as e:
        print(f"ERRO ao processar mensagem individual: {str(e)}")

# --- Rotas de Administração (permanecem as mesmas) ---

@whatsapp_bp.route('/conversations', methods=['GET'])
def get_conversations():
    conversations = Conversation.query.order_by(Conversation.timestamp.desc()).all()
    return jsonify([conv.to_dict() for conv in conversations])

@whatsapp_bp.route('/appointments', methods=['GET'])
def get_appointments():
    appointments = Appointment.query.order_by(Appointment.timestamp.desc()).all()
    return jsonify([apt.to_dict() for apt in appointments])

@whatsapp_bp.route('/appointments/<int:appointment_id>/status', methods=['PUT'])
def update_appointment_status(appointment_id):
    data = request.get_json()
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = data.get('status', appointment.status)
    db.session.commit()
    return jsonify(appointment.to_dict())
