# src/services/bot_logic.py (Versão Modificada)

import re
from datetime import datetime
from src.models.conversation import db, Appointment

class BotLogic:
    def __init__(self):
        self.user_states = {}

    def process_message(self, message, phone_number):
        """Processa a mensagem e retorna a resposta apropriada, considerando o horário comercial."""
        message_lower = message.lower().strip()
        state = self.user_states.get(phone_number, {}).get('step', 'initial')

        # --- FLUXO DE CONVERSA PRINCIPAL ---
        # O menu principal e as informações devem funcionar a qualquer hora.
        if message_lower in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'menu'] or state == 'initial':
            self.user_states[phone_number] = {'step': 'awaiting_choice'}
            return self.get_main_menu()

        elif '1' in message_lower and state == 'awaiting_choice':
            return self.get_first_consultation_info()

        elif '2' in message_lower and state == 'awaiting_choice':
            return self.get_insurance_info()

        elif '3' in message_lower and state == 'awaiting_choice':
            return self.get_treatments_info()

        # --- OPÇÕES QUE DEPENDEM DO HORÁRIO ---
        # Agora, a verificação do horário é feita aqui, apenas para as opções relevantes.

        elif '4' in message_lower and state == 'awaiting_choice': # Agendar
            if not self.is_business_hours():
                return self.get_after_hours_message(action="agendamento")
            return self.start_appointment_flow(phone_number)

        elif '5' in message_lower and state == 'awaiting_choice': # Falar com a equipe
            if not self.is_business_hours():
                return self.get_after_hours_message(action="atendimento")
            return self.get_team_contact()

        elif any(word in message_lower for word in ['emergência', 'emergencia', 'urgência', 'urgencia', 'dor']):
            return self.get_emergency_contact()

        # --- FLUXO DE AGENDAMENTO (se já estiver em andamento) ---
        elif phone_number in self.user_states and state != 'awaiting_choice':
            return self.handle_appointment_flow(message, phone_number)

        else:
            return self.get_default_response()

    def get_main_menu(self):
        """Retorna o menu principal"""
        return """🦷 *Dentinhos de Leite Odontologia*

Olá! Seja bem-vindo(a)! Como posso ajudá-lo(a) hoje?

*Escolha uma das opções:*

1️⃣ Informações sobre primeira consulta
2️⃣ Informações sobre convênios
3️⃣ Conhecer tratamentos disponíveis
4️⃣ Agendar consulta
5️⃣ Falar com a equipe

Digite o número da opção desejada ou a palavra-chave.

Para emergências 24h: (16) 99269-2383 ou (16) 99212-0514"""

    def get_first_consultation_info(self):
        """Informações sobre primeira consulta"""
        return """💰 *PRIMEIRA CONSULTA*

🔹 *Valor:* R$ 179,90
🔹                     *Inclui:*
   • Consulta completa com o Dr Rafael Moreira -Odontopediatra - CRO/SP 156455
   • À Consulta tem em média 1h de atendimento.
   • Atendimento humanizado e lúdico.
   • Consultório com estrutura completa.
   • Limpeza profissional (profilaxia).
   • Aplicação de flúor (quando necessário).
   • Orientações de higiene bucal.
   • Orientação de Dieta.
   • Avaliação Ortodôntica e Ortopédica.
   • Guia de orientação para os pequenos.

📅 Para agendar sua consulta, digite *4* ou *agendar*
🏠 Voltar ao menu principal: digite *menu*"""

    def get_insurance_info(self):
        """Informações sobre convênios"""
        return """🏥 *CONVÊNIOS ODONTOLÓGICOS*

❌ *Não trabalhamos com convênios odontológicos*

*Por quê?*
Para garantir a qualidade e o tempo necessário para cada atendimento, optamos por atendimento particular. Isso nos permite:

✅ Consultas sem pressa
✅ Materiais de primeira qualidade
✅ Atendimento personalizado
✅ Foco total na saúde bucal do seu filho

💳 Aceitamos cartões de débito e crédito
💰 Consulta: R$ 179,90

🏠 Voltar ao menu principal: digite *menu*"""

    def get_treatments_info(self):
        """Informações sobre tratamentos"""
        return """🦷 *TRATAMENTOS DISPONÍVEIS*

👶 *Odontopediatria Especializada:*
• Consultas preventivas
• Limpeza e aplicação de flúor
• Tratamento de cáries
• Restaurações em resina
• Extrações quando necessário
• Orientação de higiene bucal

🔬 *Tratamentos Especiais:*
• Laserterapia (tratamento com laser)
• Pré-natal odontológico (orientação para gestantes)

🎯 *Nosso diferencial:*
• Ambiente lúdico e acolhedor
• Técnicas para reduzir ansiedade
• Atendimento humanizado

📅 Agende sua consulta: digite *4*
🏠 Menu principal: digite *menu*"""

    def start_appointment_flow(self, phone_number):
        """Inicia o fluxo de agendamento"""
        self.user_states[phone_number] = {
            'step': 'name',
            'data': {}
        }
        return """📅 *AGENDAMENTO DE CONSULTA*

Vou precisar de algumas informações:

👶 *Qual o nome da criança?*"""

    def handle_appointment_flow(self, message, phone_number):
        """Gerencia o fluxo de agendamento"""
        state = self.user_states[phone_number]
        step = state['step']

        if step == 'name':
            state['data']['child_name'] = message
            state['step'] = 'age'
            return """👶 *Qual a idade da criança?*

(Ex: 3 anos, 5 anos e 6 meses, etc.)"""

        elif step == 'age':
            state['data']['child_age'] = message
            state['step'] = 'reason'
            return """🔍 *Qual o motivo da consulta?*

(Ex: primeira consulta, dor de dente, limpeza, etc.)"""

        elif step == 'reason':
            state['data']['reason'] = message
            state['step'] = 'period'
            return """⏰ *Qual o melhor período para você?*

Digite uma das opções:
• Manhã
• Tarde
• Qualquer horário"""

        elif step == 'period':
            state['data']['preferred_period'] = message

            appointment = Appointment(
                phone_number=phone_number,
                child_name=state['data']['child_name'],
                child_age=state['data']['child_age'],
                reason=state['data']['reason'],
                preferred_period=state['data']['preferred_period']
            )
            db.session.add(appointment)
            db.session.commit()

            del self.user_states[phone_number]

            return f"""✅ *AGENDAMENTO SOLICITADO*

📋 *Resumo:*
👶 Criança: {state['data']['child_name']}
🎂 Idade: {state['data']['child_age']}
🔍 Motivo: {state['data']['reason']}
⏰ Período: {state['data']['preferred_period']}

📞 Nossa equipe entrará em contato em breve para confirmar o horário disponível.

🏠 Voltar ao menu: digite *menu*
📞 Emergências: (16) 99269-2383 ou (16) 99212-0514"""

    def get_team_contact(self):
        """Informações para falar com a equipe"""
        return """👥 *FALAR COM A EQUIPE*

📞 *Atendimento Humano:*
Durante o horário comercial, nossa equipe está disponível para atendimento personalizado.

📱 *Contatos:*
• (16) 99269-2383
• (16) 99212-0514

🕐 *Horário de Atendimento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

🚨 *Emergências 24h:*
(16) 99269-2383 ou (16) 99212-0514

🏠 Voltar ao menu: digite *menu*"""

    def get_emergency_contact(self):
        """Contato para emergências"""
        return """🚨 *EMERGÊNCIAS 24H*

Se seu filho está com dor ou desconforto, entre em contato imediatamente:

📞 *Telefones de Emergência:*
• (16) 99269-2383
• (16) 99212-0514

⚡ *Atendimento de urgências 24 horas*

🏥 Nossa equipe está preparada para atender emergências odontológicas a qualquer hora.

🏠 Voltar ao menu: digite *menu*"""

    def get_after_hours_message(self, action="atendimento"):
        """Mensagem para horário fora de expediente, personalizada pela ação."""
        message = f"""🌙 *FORA DO HORÁRIO DE ATENDIMENTO*

Obrigado por entrar em contato com a Dentinhos de Leite Odontologia!

Nosso horário para {action} é:
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

Por favor, entre em contato durante este horário, ou se preferir, deixe sua mensagem e retornaremos assim que possível.

🚨 *Para emergências 24h, ligue:*
📞 (16) 99269-2383 ou (16) 99212-0514

Digite *menu* para ver outras opções."""
        return message

    def get_default_response(self):
        """Resposta padrão quando não entende a mensagem"""
        return """❓ *Não entendi sua mensagem*

Digite *menu* para ver as opções disponíveis ou escolha uma das opções:

1️⃣ Primeira consulta
2️⃣ Convênios
3️⃣ Tratamentos
4️⃣ Agendar consulta
5️⃣ Falar com equipe

🚨 Emergências: (16) 99269-2383 ou (16) 99212-0514"""

    def is_business_hours(self):
        """Verifica se está no horário de atendimento"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour

        if weekday < 5:
            return 8 <= hour < 18
        elif weekday == 5:
            return 8 <= hour < 12
        else:
            return False
