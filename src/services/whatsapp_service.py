# src/services/whatsapp_service.py

import requests
import os
import json

def send_whatsapp_message(phone_number, message_text):
    """
    Envia uma mensagem de texto para um número de telefone via WhatsApp Business API.
    """
    ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("ERRO CRÍTICO: As variáveis de ambiente do WhatsApp não estão configuradas. A mensagem não pode ser enviada.")
        return

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload ))
        response.raise_for_status()
        print(f"Mensagem enviada com sucesso para {phone_number}.")
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"ERRO ao enviar mensagem para {phone_number}: {e}")
        # Adicionar mais detalhes do erro se disponíveis
        if e.response is not None:
            print(f"Detalhes do erro da API: {e.response.text}")
        return None
