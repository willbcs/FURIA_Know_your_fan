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

📬 Fluxo do Sistema
1. Cadastro básico → 2. Upload de documento → 3. Conexão social → 4. Links de interesse → 5. Confirmação e envio automático de e-mail

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

📬 System Flow
1. Basic registration → 2. Document upload → 3. Social connection → 4. Interest links → 5. Confirmation and automatic email delivery

📧 Email System
Triggered automatically upon registration completion
Uses interest-based templates
Requires valid SendGrid API key

📬 Contact
For questions:
📧 [willbc.silva@gmail.com]

👨‍💻 Developed by:
[William Bruno Carlos Silva]