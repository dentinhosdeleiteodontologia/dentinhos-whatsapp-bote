# src/routes/whatsapp.py
# Solução 4: Blindar o processamento de POST e adicionar logs de payload.

from flask import Blueprint, request, jsonify
from src.models.conversation import db, Conversation, Appointment
from src.services.bot_logic import BotLogic
from src.services.whatsapp_service import send_whatsapp_message
import json
import os

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')
bot_logic = BotLogic()

@whatsapp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificação do webhook do WhatsApp Business API."""
    print("INFO: Recebido pedido de verificação de webhook (GET).")
    verify_token_esperado = os.environ.get('VERIFY_TOKEN')
    
    if not verify_token_esperado:
        print("ERRO CRÍTICO: A variável de ambiente VERIFY_TOKEN não está configurada!")
        return "Erro de configuração interna.", 500

    mode = request.args.get('hub.mode')
    token_recebido = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print(f"INFO: Modo='{mode}', Token Recebido='{token_recebido}', Token Esperado='{verify_token_esperado}'")
    
    if mode == 'subscribe' and token_recebido == verify_token_esperado:
        print("SUCESSO: Webhook verificado com sucesso!")
        return challenge
    else:
        print("FALHA: Verificação do webhook falhou.")
        return "Token de verificação inválido", 403

@whatsapp_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """Processa mensagens recebidas do WhatsApp (versão à prova de falhas)."""
    print("INFO: Recebido pedido POST em /webhook.")
    
    # 1. Obter os dados brutos, sem assumir que são JSON.
    raw_data = request.get_data()
    if not raw_data:
        print("AVISO: Pedido POST recebido com corpo vazio.")
        return jsonify({"status": "ok", "message": "Corpo vazio"}), 200

    # 2. Logar os dados brutos para depuração.
    print(f"DEBUG: Dados brutos recebidos (raw): {raw_data.decode('utf-8')}")

    # 3. Tentar converter para JSON de forma segura.
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        print("ERRO: Falha ao descodificar JSON do pedido POST.")
        # Retornamos 200 OK para que o WhatsApp não continue a enviar um pedido inválido.
        return jsonify({"status": "error", "message": "JSON mal formatado"}), 200

    # 4. Processar os dados JSON.
    try:
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') == 'messages':
                            process_message(change['value'])
        
        print("INFO: Pedido POST processado com sucesso.")
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"ERRO CRÍTICO ao processar a lógica do webhook: {str(e)}")
        return jsonify({"status": "error", "message": "Erro interno no processamento"}), 500

def process_message(message_data):
    # (Esta função permanece a mesma)
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
