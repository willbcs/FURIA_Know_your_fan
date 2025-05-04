🚀 FURIA - KNOW YOUR FAN - README
🇧🇷 Português
🤖 Sobre o Projeto
Sistema completo de cadastro para fãs da FURIA com:

📝 Formulário inteligente com validações

📄 Upload e leitura automática de documentos (RG/CNH)

🔗 Conexão com Discord, Google e Steam

✉️ Envio de e-mails personalizados via SendGrid

🗄️ Armazenamento seguro no MongoDB

Desenvolvido como projeto do Challenge #2: Know Your Fan para a vaga de Assistente de Engenharia de Software.

📦 Dependências
Crie e ative um ambiente virtual (recomendado):
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

Instale as dependências:
pip install -r requirements.txt

⚙️ Configuração
Crie um arquivo .env na raiz do projeto com:
MONGO_URI = "sua_string_de_conexao"
MONGO_DB_NAME = "nome_banco"
FLASK_SECRET_KEY = 'sua_chave_secreta'
CLIENT_ID = "123456789123456789"
CLIENT_SECRET = "Laba3pTiukWlmkos-Ri6ATAEuEqjTRLQ"
GOOGLE_CLIENT_ID = "123456123456123456123456"
GOOGLE_CLIENT_SECRET = "sua_chave_secreta"
STEAM_API_KEY = "sua_chave_steam"
SENDER_EMAIL = endereco_de_email_configurado #(Sendgrid)  
SENDER_NAME = nome_do_sender_configurado #(Sendgrid)
SENDGRID_API_KEY = "sua_chave_sendgrid"

Integrações OAuth (obrigatórias):
Crie apps nos respectivos sites:
Discord Developer Portal
Google Cloud Console
Steam Developer

🚀 Como Executar
Inicie o servidor Flask:
python app.py
O sistema estará disponível em: http://127.0.0.1:5000
Para dispositivos móveis na mesma rede estará disponível em http://192.168.15.7:5000

📬 Fluxo do Sistema Completo

1. Cadastro Básico (Obrigatório)
- Dados pessoais: Nome completo, CPF (com validação), data de nascimento (idade mínima 12 anos), e-mail válido e endereço
- Preferências: Seleção de eSports acompanhados, interesses, atividades diárias e hábitos de compra
- Validação em tempo real com feedback visual
- Aceite de termos LGPD obrigatório

2. Upload de Documento (Obrigatório)
- Envio de RG, CNH ou Passaporte (PNG, JPG, JPEG ou PDF)
- Validação automática dos dados do documento (nome e CPF/RG)
- OCR com EasyOCR para extração de informações
- Armazenamento seguro no servidor (pasta uploads)

3. Conexão Social (Mínimo 1 obrigatória)
- Vinculação de contas via OAuth:
  • Discord: Coleta dados básicos e verifica participação no servidor da FURIA
  • Google: Acessa perfil, e-mail e dados adicionais (com permissão)
  • Steam: Obtém perfil público e lista de jogos mais jogados
- Redes sociais opcionais: Twitter/X, Instagram, Twitch (com validação de URLs)

4. Links de Interesse (Opcional)
- Inserção de até 3 links de fontes de notícias sobre eSports
- Validação automática para garantir que são links relacionados a eSports
- Armazenados para personalização de conteúdo futuro

5. Confirmação e E-mail
- Consolidação de todos os dados em um documento no MongoDB
- Envio automático de e-mail personalizado via SendGrid com:
  • Recomendações baseadas nos interesses do usuário
  • Links úteis e conteúdo relevante
  • Template responsivo com logo da FURIA
- Redirecionamento para página de sucesso com confirmação

📧 Envio de E-mails
Disparado automaticamente ao final do cadastro
Usa templates personalizados baseados nos interesses
Requer chave API do SendGrid válida

📬 Contato
Em caso de dúvidas:
📧 [willbc.silva@gmail.com]

👨‍💻 Desenvolvido por:
[William Bruno Carlos Silva]


🇺🇸 English
🤖 About the Project
Complete fan registration system for FURIA featuring:

📝 Smart form with validations

📄 Automatic document upload and processing (ID/Driver's License)

🔗 Discord, Google, and Steam integration

✉️ Personalized email delivery via SendGrid

🗄️ Secure MongoDB storage

Developed as part of Challenge #2: Know Your Fan for the Software Engineering Assistant position.

📦 Dependencies
Create and activate a virtual environment (recommended):
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

Install dependencies:
pip install -r requirements.txt

⚙️ Configuration
Create a .env file in the project root with:
MONGO_URI = "your_connection_string"
MONGO_DB_NAME = "database_name"
FLASK_SECRET_KEY = 'your_secret_key'
CLIENT_ID = "123456789123456789"
CLIENT_SECRET = "Laba3pTiukWlmkos-Ri6ATAEuEqjTRLQ"
GOOGLE_CLIENT_ID = "123456123456123456123456"
GOOGLE_CLIENT_SECRET = "your_secret_key"
STEAM_API_KEY = "your_steam_key"
SENDER_EMAIL = configured_email_address  #(Sendgrid)  
SENDER_NAME = configured_sender_name  #(Sendgrid)
SENDGRID_API_KEY = "your_sendgrid_key"

Required OAuth Integrations:
Create apps on the respective platforms:
Discord Developer Portal
Google Cloud Console
Steam Developer

🚀 How to Run
Start the Flask server:
python app.py

The system will be available at:
http://127.0.0.1:5000 (local)
http://192.168.15.7:5000 (for mobile devices on the same network)

📬 Complete System Flow

1. Basic Registration (Mandatory)
- Personal data: Full name, CPF (validated), birth date (minimum age 12), valid email and address
- Preferences: eSports selection, interests, daily activities and purchase habits
- Real-time validation with visual feedback
- LGPD terms acceptance required

2. Document Upload (Mandatory)
- RG, driver's license or passport upload (PNG, JPG, JPEG or PDF)
- Automatic document data validation (name and CPF/RG)
- OCR with EasyOCR for information extraction
- Secure server storage (uploads folder)

3. Social Connection (Minimum 1 required)
- Account linking via OAuth:
  • Discord: Collects basic data and checks FURIA server participation
  • Google: Accesses profile, email and additional data (with permission)
  • Steam: Gets public profile and most played games list
- Optional social networks: Twitter/X, Instagram, Twitch (with URL validation)

4. Interest Links (Optional)
- Input of up to 3 eSports news sources links
- Automatic validation to ensure eSports-related links
- Stored for future content personalization

5. Confirmation and Email
- Consolidates all data in a MongoDB document
- Automatic personalized email via SendGrid with:
  • Recommendations based on user interests
  • Useful links and relevant content
  • Responsive template with FURIA logo
- Redirect to success page with confirmation

📧 Email System
Triggered automatically upon registration completion
Uses interest-based templates
Requires valid SendGrid API key

📬 Contact
For questions:
📧 [willbc.silva@gmail.com]

👨‍💻 Developed by:
[William Bruno Carlos Silva]