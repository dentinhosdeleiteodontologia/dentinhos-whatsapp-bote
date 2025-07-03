# src/routes/whatsapp.py
# Solução Final: Manter a rota /api/whatsapp/webhook e adicionar logs detalhados.

from flask import Blueprint, request, jsonify
from src.models.conversation import db, Conversation, Appointment
from src.services.bot_logic import BotLogic
from src.services.whatsapp_service import send_whatsapp_message
import json
import os

# 1. GARANTIR O PREFIXO CORRETO
whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')
bot_logic = BotLogic()

# A rota final será: /api/whatsapp/webhook
@whatsapp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificação do webhook do WhatsApp Business API com logs detalhados."""
    print("INFO: Recebido pedido de verificação de webhook (GET).")
    
    verify_token_esperado = os.environ.get('VERIFY_TOKEN')
    
    # 2. LOGS DETALHADOS
    if not verify_token_esperado:
        print("ERRO CRÍTICO: A variável de ambiente VERIFY_TOKEN não está configurada na Render!")
        return "Erro de configuração interna do servidor.", 500

    mode = request.args.get('hub.mode')
    token_recebido = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print(f"INFO: Modo recebido: '{mode}'")
    print(f"INFO: Token recebido: '{token_recebido}'")
    print(f"INFO: Token esperado: '{verify_token_esperado}'")
    
    if mode and token_recebido:
        if mode == 'subscribe' and token_recebido == verify_token_esperado:
            print("SUCESSO: Webhook verificado com sucesso! Retornando o challenge.")
            return challenge
        else:
            print("FALHA: A verificação do webhook falhou. O modo ou o token não correspondem.")
            return "Token de verificação inválido", 403
    
    print("FALHA: Parâmetros 'hub.mode' ou 'hub.verify_token' em falta no pedido.")
    return "Parâmetros de verificação em falta", 400

# A rota final será: /api/whatsapp/webhook
@whatsapp_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """Processa mensagens recebidas do WhatsApp"""
    try:
        data = request.get_json()
        if not data:
            print("AVISO: Webhook (POST) recebido sem dados.")
            return jsonify({"status": "ok"}), 200 # Responde 200 para não ser reenviado
        
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') == 'messages':
                            process_message(change['value'])
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao processar webhook (POST): {str(e)}")
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
                    print(f"INFO: Resposta enviada para {phone_number}.")
                
    except Exception as e:
        print(f"ERRO ao processar mensagem individual: {str(e)}")

# --- Rotas de Administração (permanecem as mesmas) ---
# ... (código das rotas /conversations e /appointments)
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
