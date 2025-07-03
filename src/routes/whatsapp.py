# src/routes/whatsapp.py
# TESTE DE DIAGNÓSTICO EXTREMO: Simplificar o webhook POST ao máximo.

from flask import Blueprint, request, jsonify
import os
import json # Manter para depuração, se necessário

# Não vamos importar BotLogic, Conversation, Appointment, send_whatsapp_message
# para garantir que nada interfere.

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')

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
    """TESTE: Processa mensagens recebidas do WhatsApp com o mínimo de lógica."""
    print("INFO: [TESTE EXTREMO] Recebido pedido POST em /webhook.")
    
    # Tentar obter o corpo do pedido, mas sem processá-lo.
    try:
        raw_data = request.get_data()
        print(f"DEBUG: [TESTE EXTREMO] Dados brutos recebidos (tamanho: {len(raw_data)} bytes).")
        # Opcional: imprimir os primeiros 500 caracteres para depuração
        # print(f"DEBUG: [TESTE EXTREMO] Conteúdo: {raw_data.decode('utf-8')[:500]}")
    except Exception as e:
        print(f"ERRO: [TESTE EXTREMO] Falha ao obter dados brutos: {str(e)}")
        # Ainda assim, tentar retornar 200 OK para não ser reenviado
        return jsonify({"status": "error", "message": "Falha ao ler dados"}), 200

    # Retornar 200 OK imediatamente, sem qualquer outra lógica.
    print("INFO: [TESTE EXTREMO] Retornando 200 OK imediatamente.")
    return jsonify({"status": "success", "message": "Pedido recebido e ignorado (teste)"}), 200

# --- Rotas de Administração (Manter para não quebrar a aplicação, mas não serão testadas) ---
# Você pode manter as rotas get_conversations, get_appointments, update_appointment_status
# mas elas não serão afetadas por este teste.
# Se quiser, pode comentá-las temporariamente para um isolamento ainda maior,
# mas lembre-se de as reativar depois.

# @whatsapp_bp.route('/conversations', methods=['GET'])
# def get_conversations():
#     return jsonify({"message": "Conversations route disabled for test"})

# @whatsapp_bp.route('/appointments', methods=['GET'])
# def get_appointments():
#     return jsonify({"message": "Appointments route disabled for test"})

# @whatsapp_bp.route('/appointments/<int:appointment_id>/status', methods=['PUT'])
# def update_appointment_status(appointment_id):
#     return jsonify({"message": "Appointment status route disabled for test"})
