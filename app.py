from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import os
import easyocr
import re
from datetime import datetime, date, timedelta
from config import MONGO_URI, MONGO_DB_NAME
from werkzeug.utils import secure_filename
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import urllib.parse
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from pathlib import Path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
DISCORD_CLIENT_ID = os.getenv('CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URIS = [
    "http://127.0.0.1:5000/auth/discord/callback",
    "http://192.168.15.7:5000/auth/discord/callback",
    "http://192.168.15.7/auth/discord/callback"
]
FURIA_GUILD_ID = "700387128227659797"

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = "http://127.0.0.1:5000/auth/google/callback"
GOOGLE_SCOPES = [
    'openid',
    'profile',
    'email',
    'https://www.googleapis.com/auth/user.birthday.read',
    'https://www.googleapis.com/auth/user.gender.read',
    'https://www.googleapis.com/auth/user.phonenumbers.read',
    'https://www.googleapis.com/auth/user.addresses.read',
    'https://www.googleapis.com/auth/youtube.readonly'
]
STEAM_API_KEY = os.getenv('STEAM_API_KEY')

def get_redirect_uri(request):
    host = request.host_url.rstrip('/')
    if '192.168.15.7:5000' in host and host.count('5000') > 1:
        host = host.replace(':5000', '', 1)
    return f"{host}/auth/discord/callback"

fans_collection = db['fans']

# EasyOCR
reader = easyocr.Reader(['pt'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf'}

def extract_document_info(text_list):
    cpf = None
    rg = None
    data_nascimento = None
    cpf_usuario = session['fan_data']['cpf']
    
    cpf_pattern = re.compile(r'(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})')
    rg_pattern = re.compile(r'(RG|IDENTIDADE|REGISTRO GERAL)[^\d]*(\d[\d\.-]+\d)', re.IGNORECASE)
    nascimento_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')

    for text in text_list:
        text = text.strip().upper()
        
        if not data_nascimento:
            nasc_match = nascimento_pattern.search(text)
            if nasc_match:
                data_nascimento = nasc_match.group()

        if not cpf:
            cpf_matches = cpf_pattern.finditer(text)
            for match in cpf_matches:
                candidate = re.sub(r'[^0-9]', '', match.group())
                if len(candidate) == 11 and candidate == cpf_usuario:
                    cpf = candidate
                    break

        if not rg:
            rg_match = rg_pattern.search(text)
            if rg_match:
                rg_candidate = re.sub(r'[^0-9]', '', rg_match.group(2))
                if 7 <= len(rg_candidate) <= 12:
                    rg = rg_candidate
            elif not rg and (text.startswith('RG') or 'REGISTRO' in text):
                numbers = re.sub(r'[^0-9]', '', text)
                if 7 <= len(numbers) <= 12:
                    rg = numbers

    return cpf, rg, data_nascimento

def validate_document(extracted_text, fan_data):
    nome_encontrado = any(fan_data['nome'].lower() in text.lower() for text in extracted_text)
    cpf_digits = re.sub(r'[^0-9]', '', fan_data['cpf'])
    cpf_encontrado = any(cpf_digits in re.sub(r'[^0-9]', '', text) for text in extracted_text)
    rg_encontrado = any(
        'RG' in text.upper() or 
        'IDENTIDADE' in text.upper() or 
        'REGISTRO' in text.upper() 
        for text in extracted_text
    )
    return nome_encontrado and (cpf_encontrado or rg_encontrado)

def get_recommendations(fan_data):
    """Gera recomendações personalizadas baseadas nos interesses do fã"""
    recommendations = {
        # eSports
        'cs': [
            {'title': 'Notícias - FURIA CS', 'url': 'https://themove.gg/esports/cs'},
            {'title': 'Próximos Torneios - CS', 'url': 'https://draft5.gg/equipe/330-FURIA/campeonatos'}
        ],
        'valorant': [
            {'title': 'Valorant - Site Oficial', 'url': 'https://playvalorant.com/pt-br/'},
            {'title': 'Notícias - FURIA Valorant', 'url': 'https://valorantzone.gg/campeonatos-em-andamento/'}
        ],
        'lol': [
            {'title': 'Notícias - FURIA LOL', 'url': 'https://themove.gg/esports/lol'},
            {'title': 'Torneios - LOL', 'url': 'https://pt.egamersworld.com/lol/events'}
        ],
        'pubg': [
            {'title': 'Notícias - FURIA PUBG', 'url': 'https://themove.gg/esports/pubg'},
            {'title': 'Site Oficial - PUBG', 'url': 'https://pubg.com/pt-br/main'}
        ],
        'rocket': [
            {'title': 'Notícias - FURIA Rocket League', 'url': 'https://themove.gg/esports/rocket-league'},
            {'title': 'Site Oficial - Rocket League', 'url': 'https://www.rocketleague.com/pt-br'}
        ],
        # Produtos
        'roupas': [
            {'title': 'Produtos licenciados FURIA', 'url': 'https://www.furia.gg/produtos'},
            {'title': 'Outlet Oficial', 'url': 'https://www.furia.gg/outlet'}
        ],
        'acessorios': [
            {'title': 'Coleção FURIA', 'url': 'https://www.furia.gg/colecao'},
            {'title': 'Acessórios Exclusivos', 'url': 'https://www.furia.gg/acessorios'}
        ],
        # Conteúdo
        'streaming': [
            {'title': 'FURIA na Twitch', 'url': 'https://www.twitch.tv/furiatv'}           
        ]
    }
    
    selected_recommendations = []
    
    # 1. Análise de eSports (jogos)
    for esport in fan_data.get('esports', []):
        esport_lower = esport.lower()
        
        if any(term in esport_lower for term in ['cs', 'counter', 'cs:go', 'cs2']):
            selected_recommendations.extend(recommendations['cs'])
        elif any(term in esport_lower for term in ['valora', 'vlr']):
            selected_recommendations.extend(recommendations['valorant'])
        elif any(term in esport_lower for term in ['lol', 'league', 'league of legends']):
            selected_recommendations.extend(recommendations['lol'])
        elif any(term in esport_lower for term in ['pubg', 'playerunknown']):
            selected_recommendations.extend(recommendations['pubg'])
        elif any(term in esport_lower for term in ['rocket', 'rl ', 'rocket league']):
            selected_recommendations.extend(recommendations['rocket'])
    
    # 2. Análise de compras (produtos físicos)
    for compra in fan_data.get('compras', []):
        compra_lower = compra.lower()
        
        if any(term in compra_lower for term in ['roupa', 'vestuário', 'camiseta', 'moletom']):
            selected_recommendations.extend(recommendations['roupas'])
        elif any(term in compra_lower for term in ['acessório', 'boné', 'mochila', 'colecionável']):
            selected_recommendations.extend(recommendations['acessorios'])
    
    # 3. Análise de atividades (hábitos)
    for atividade in fan_data.get('atividades', []):
        atividade_lower = atividade.lower()
        if any(term in atividade_lower for term in ['assistir', 'stream', 'live']):
            selected_recommendations.extend(recommendations['streaming'])
    
    # Recomendações padrão (fallback)
    if len(selected_recommendations) < 3:
        selected_recommendations.extend([
            {'title': 'Loja Oficial FURIA', 'url': 'https://www.furia.gg/loja'},
            {'title': 'FURIA TV', 'url': 'https://www.furia.gg/tv'},
            {'title': 'Blog de Esports', 'url': 'https://www.furia.gg/news'}
        ])
    
    # Remove duplicatas mantendo a ordem
    seen_urls = set()
    final_recommendations = []
    for rec in selected_recommendations:
        if rec['url'] not in seen_urls:
            seen_urls.add(rec['url'])
            final_recommendations.append(rec)
    
    return final_recommendations

def send_welcome_email(email, fan_data):
    """Envia e-mail de boas-vindas com recomendações personalizadas"""
    try:
        # Configurações básicas
        recommendations = get_recommendations(fan_data)
        first_name = fan_data['nome'].split()[0]
        esports_list = ', '.join(fan_data['esports'])
        
        # Lê a imagem da logo
        logo_path = Path('static') / 'furia-logo.png'
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
        
        # Renderiza o template HTML
        html_content = render_template(
            'email.html',
            first_name=first_name,
            esports=esports_list,
            recommendations=recommendations,
            current_year=datetime.now().year
        )
        
        # Cria a mensagem
        message = Mail(
            from_email=os.getenv('SENDER_EMAIL'),
            to_emails=email,
            subject=f'🚀 Bem-vindo à FURIA, {first_name}! Aqui estão suas recomendações',
            html_content=html_content
        )
        
        # Adiciona anexo da logo
        encoded_logo = base64.b64encode(logo_data).decode()
        attached_logo = Attachment(
            FileContent(encoded_logo),
            FileName('furia-logo.png'),
            FileType('image/png'),
            Disposition('inline'),
            content_id='furia-logo'
        )
        message.attachment = attached_logo
        
        # Envia o e-mail
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        
        print(f"E-mail enviado para {email}, status: {response.status_code}")
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf = re.sub(r'\D', '', request.form.get('cpf', ''))
        endereco = request.form.get('endereco', '').strip()
        email = request.form.get('email', '').strip().lower()
        data_nascimento = request.form.get('data_nascimento', '')
        
        partes_nome = [parte for parte in nome.split() if len(parte) >= 2]
        if len(partes_nome) < 2:
            flash('Por favor, insira seu nome completo (pelo menos nome e sobrenome).', 'error')
            return redirect(url_for('index'))
            
        if len(cpf) != 11 or not cpf.isdigit():
            flash('CPF deve conter 11 dígitos numéricos.', 'error')
            return redirect(url_for('index'))
            
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not EMAIL_REGEX.fullmatch(email):
            flash('Por favor, insira um e-mail válido (exemplo: usuario@provedor.com).', 'error')
            return redirect(url_for('index'))
            
        try:
            data_nasc = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            idade = (date.today() - data_nasc).days // 365
            if idade < 12:
                flash('Você deve ter pelo menos 12 anos para se cadastrar.', 'error')
                return redirect(url_for('index'))
            elif idade > 120:
                flash('Data de nascimento inválida.', 'error')
                return redirect(url_for('index'))
        except (ValueError, TypeError):
            flash('Data de nascimento inválida.', 'error')
            return redirect(url_for('index'))
            
        esports = request.form.getlist('esports')
        interesses = request.form.getlist('interesses')
        atividades = request.form.getlist('atividades')
        compras = request.form.getlist('compras')
        
        if not esports:
            flash('Selecione pelo menos um eSport que você acompanha.', 'error')
            return redirect(url_for('index'))
            
        outros_esports = request.form.get('outros_esports', '').strip()
        outros_interesses = request.form.get('outros_interesses', '').strip()
        outros_atividades = request.form.get('outros_atividades', '').strip()
        outros_compras = request.form.get('outros_compras', '').strip()
        
        if outros_esports:
            esports.append(outros_esports)
        if outros_interesses:
            interesses.append(outros_interesses)
        if outros_atividades:
            atividades.append(outros_atividades)
        if outros_compras:
            compras.append(outros_compras)
            
        session['fan_data'] = {
            'nome': nome,
            'cpf': cpf,
            'email': email,
            'endereco': endereco,
            'data_nascimento': data_nascimento,
            'esports': esports,
            'interesses': interesses,
            'atividades': atividades,
            'compras': compras,
            'timestamp': datetime.now().isoformat()
        }
        
        return redirect(url_for('upload'))
        
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'fan_data' not in session:
        flash('Por favor, complete seus dados básicos primeiro.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'documento' not in request.files:
            flash('Nenhum arquivo enviado.', 'error')
            return redirect(url_for('upload'))

        file = request.files['documento']

        if file.filename == '' or not allowed_file(file.filename):
            flash('Arquivo inválido. Envie PNG, JPG, JPEG ou PDF.', 'error')
            return redirect(url_for('upload'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        try:
            results = reader.readtext(filepath)
            texto_extraido = [text for (_, text, _) in results]
            print("Texto extraído:", texto_extraido)

            if not validate_document(texto_extraido, session['fan_data']):
                os.remove(filepath)
                flash('Os dados do documento não correspondem aos informados. Verifique seu documento.', 'error')
                return redirect(url_for('upload'))

            cpf_doc, rg_doc, nascimento_doc = extract_document_info(texto_extraido)

            session['documento'] = {
                'arquivo': filename,
                'texto_extraido': texto_extraido,
                'cpf_documento': cpf_doc,
                'rg_documento': rg_doc,
                'data_nascimento_documento': nascimento_doc,
                'data_upload': datetime.now().isoformat()
            }

            flash('Documento validado com sucesso!', 'success')
            return redirect(url_for('social'))

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            flash('Erro ao processar o documento. Verifique se ele é uma imagem clara (PNG, JPG, JPEG) ou PDF válido.', 'error')
            return redirect(url_for('upload'))

    return render_template('upload.html')

@app.route('/social', methods=['GET', 'POST'])
def social():
    if 'fan_data' not in session or 'documento' not in session:
        flash('Sessão expirada. Por favor, preencha novamente.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if not session.get('discord_data') and not session.get('google_data') and not session.get('steam_data'):
            flash('Você deve vincular pelo menos uma conta (Discord, Google ou Steam) para continuar.', 'error')
            return redirect(url_for('social'))

        twitter = request.form.get('twitter', '').strip()
        instagram = request.form.get('instagram', '').strip()
        twitch = request.form.get('twitch', '').strip()
        youtube = request.form.get('youtube', '').strip()

        social_data = {
            'twitter': f'https://x.com/{twitter.lstrip("@")}' if twitter else '',
            'instagram': f'https://instagram.com/{instagram.lstrip("@")}' if instagram else '',
            'twitch': f'https://twitch.tv/{twitch}' if twitch else '',
            'youtube': f'https://youtube.com/{youtube}' if youtube else ''
        }

        for platform, url in social_data.items():
            if url and platform != 'twitter':
                try:
                    response = requests.head(url, timeout=5, allow_redirects=True)
                    if response.status_code != 200:
                        flash(f'Perfil do {platform.capitalize()} não encontrado. Verifique o nome.', 'error')
                        return redirect(url_for('social'))
                except Exception:
                    flash(f'Erro ao verificar {platform.capitalize()}. Verifique o link.', 'error')
                    return redirect(url_for('social'))

        session['social_data'] = social_data
        return redirect(url_for('links'))

    return render_template('social.html')

def validar_link_esports(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return False
        keywords = ['esports', 'furia', 'csgo', 'valorant', 'league of legends', 'dota', 'rainbow six', 'rocket league']
        conteudo = response.text.lower()
        return any(keyword in conteudo for keyword in keywords)
    except Exception:
        return False

@app.route('/links', methods=['GET', 'POST'])
def links():
    if 'fan_data' not in session or 'documento' not in session or 'social_data' not in session:
        flash('Sessão expirada. Por favor, preencha novamente.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        links = request.form.getlist('links')
        valid_links = []
        for link in links:
            link = link.strip()
            if link:
                if not link.startswith(('http://', 'https://')):
                    link = 'https://' + link
                if not validar_link_esports(link):
                    flash(f'O link informado "{link}" não parece ser relacionado a e-sports. Verifique.', 'error')
                    return redirect(url_for('links'))
                valid_links.append(link)

        session['links_data'] = valid_links
        return redirect(url_for('success'))

    return render_template('links.html')

@app.route('/success')
def success():
    if 'fan_data' not in session or 'documento' not in session or 'social_data' not in session or 'links_data' not in session:
        flash('Sessão expirada. Por favor, preencha novamente.', 'error')
        return redirect(url_for('index'))

    # Processar dados adicionais do Google se existirem
    google_extras = {}
    if 'google_data' in session and 'access_token' in session['google_data'].get('tokens', {}):
        try:
            creds = Credentials(session['google_data']['tokens']['access_token'])
            
            youtube = build('youtube', 'v3', credentials=creds)
            channel_response = youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if channel_response.get('items'):
                google_extras['youtube'] = {
                    'channel_id': channel_response['items'][0]['id'],
                    'title': channel_response['items'][0]['snippet']['title'],
                    'subscribers': channel_response['items'][0]['statistics'].get('subscriberCount'),
                    'videos': channel_response['items'][0]['statistics'].get('videoCount')
                }
            
            people_service = build('people', 'v1', credentials=creds)
            profile = people_service.people().get(
                resourceName='people/me',
                personFields='birthdays,genders,phoneNumbers,addresses'
            ).execute()
            
            if profile.get('birthdays'):
                google_extras['birthday'] = profile['birthdays'][0]['date']
            if profile.get('genders'):
                google_extras['gender'] = profile['genders'][0]['value']
            if profile.get('phoneNumbers'):
                google_extras['phone'] = profile['phoneNumbers'][0]['value']
            if profile.get('addresses'):
                google_extras['address'] = profile['addresses'][0]['formattedValue']
                
        except Exception as e:
            print(f"Erro ao obter dados extras do Google: {str(e)}")

    # Garantir que os dados das plataformas tenham estrutura consistente, mesmo quando não vinculados
    discord_data = session.get('discord_data', {})
    google_data = session.get('google_data', {})
    steam_data = session.get('steam_data', {})

    fan_data = {
        'nome': session['fan_data']['nome'],
        'cpf': session['fan_data']['cpf'],
        'email': session['fan_data']['email'],
        'endereco': session['fan_data']['endereco'],
        'data_nascimento': session['fan_data']['data_nascimento'],
        'esports': session['fan_data']['esports'],
        'interesses': session['fan_data']['interesses'],
        'atividades': session['fan_data']['atividades'],
        'compras': session['fan_data']['compras'],
        'documento': {
            'arquivo': session['documento']['arquivo'],
            'cpf_documento': session['documento']['cpf_documento'],
            'rg_documento': session['documento']['rg_documento'],
            'data_nascimento_documento': session['documento']['data_nascimento_documento'],
            'data_upload': session['documento']['data_upload'],
            'texto_extraido': session['documento']['texto_extraido']
        },
        'redes_sociais': session['social_data'],
        'links_esports': session['links_data'],
        'cadastro_em': datetime.now().isoformat(),
        'google_data': {
            **google_data,
            **google_extras
        },
        'discord_data': discord_data,
        'steam_data': steam_data
    }

    # Envia e-mails para todos os e-mails únicos encontrados
    emails_to_send = set()
    
    # E-mail do formulário
    if fan_data['email']:
        emails_to_send.add(fan_data['email'])
    
    # E-mail do Google
    if google_data.get('user', {}).get('email'):
        emails_to_send.add(google_data['user']['email'])
    
    # E-mail do Discord
    if discord_data.get('user', {}).get('email'):
        emails_to_send.add(discord_data['user']['email'])
    
    # Envia e-mail para cada e-mail único
    for email in emails_to_send:
        send_welcome_email(email, fan_data)

    fans_collection.insert_one(fan_data)
    session.clear()
    return render_template('success.html')

@app.route('/login/discord')
def discord_login():
    SCOPE = "identify email guilds guilds.members.read connections"
    redirect_uri = get_redirect_uri(request)
    
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={SCOPE}"
    )
    return redirect(discord_auth_url)

@app.route('/auth/discord/callback')
def discord_callback():
    try:
        if 'error' in request.args:
            error_desc = request.args.get('error_description', 'Erro desconhecido')
            flash(f'Erro no Discord: {error_desc}', 'error')
            return redirect(url_for('social'))

        code = request.args.get('code')
        if not code:
            flash('Código de autorização não recebido', 'error')
            return redirect(url_for('social'))

        token_data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': get_redirect_uri(request),
            'scope': 'identify email guilds guilds.members.read connections'
        }
        
        token_response = requests.post('https://discord.com/api/oauth2/token', data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}

        user_response = requests.get('https://discord.com/api/users/@me', headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        guilds_response = requests.get('https://discord.com/api/users/@me/guilds', headers=headers)
        guilds_data = guilds_response.json() if guilds_response.status_code == 200 else []
        is_in_furia = any(guild['id'] == FURIA_GUILD_ID for guild in guilds_data)

        connections_response = requests.get('https://discord.com/api/users/@me/connections', headers=headers)
        connections_data = connections_response.json() if connections_response.status_code == 200 else []

        discord_info = {
            'connected_at': datetime.now().isoformat(),
            'is_in_furia': is_in_furia,
            'user': {
                'id': user_data['id'],
                'username': user_data.get('username'),
                'discriminator': user_data.get('discriminator', '0'),
                'email': user_data.get('email'),
                'verified': user_data.get('verified', False),
                'avatar': f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data.get('avatar')}.png?size=1024" if user_data.get('avatar') else None,
                'locale': user_data.get('locale', 'pt-BR'),
                'flags': user_data.get('flags', 0),
                'premium_type': user_data.get('premium_type', 0)
            },
            'connections': [
                {
                    'type': conn['type'],
                    'name': conn['name'],
                    'verified': conn['verified']
                } for conn in connections_data
            ]
        }

        if is_in_furia:
            try:
                member_url = f"https://discord.com/api/guilds/{FURIA_GUILD_ID}/members/{user_data['id']}"
                member_response = requests.get(member_url, headers=headers)
                
                if member_response.status_code == 200:
                    member_data = member_response.json()
                    discord_info['guild_member'] = {
                        'nick': member_data.get('nick'),
                        'roles': member_data.get('roles', []),
                        'joined_at': member_data.get('joined_at'),
                        'premium_since': member_data.get('premium_since')
                    }
            except Exception as e:
                print(f"Erro nos dados do membro: {str(e)}")

        session['discord_data'] = discord_info
        session.modified = True

        flash('Conta do Discord vinculada com sucesso!', 'success')
        return redirect(url_for('social'))

    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP: {http_err}")
        flash(f'Erro ao comunicar com o Discord: {http_err}', 'error')
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        flash('Ocorreu um erro inesperado ao conectar com o Discord', 'error')
    
    return redirect(url_for('social'))

@app.route('/login/google')
def google_login():
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={'%20'.join(GOOGLE_SCOPES)}"
        f"&access_type=online"
        f"&prompt=consent"
    )
    return redirect(google_auth_url)

@app.route('/auth/google/callback')
def google_callback():
    try:
        code = request.args.get('code')
        if not code:
            flash('Falha na autenticação com Google', 'error')
            return redirect(url_for('social'))

        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': GOOGLE_REDIRECT_URI
        }
        
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()

        userinfo = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        ).json()

        session['google_data'] = {
            'user': userinfo,
            'tokens': tokens,
            'connected_at': datetime.now().isoformat()
        }

        flash('Conta do Google vinculada com sucesso!', 'success')
        return redirect(url_for('social'))

    except Exception as e:
        flash(f'Erro ao conectar com Google: {str(e)}', 'error')
        return redirect(url_for('social'))
    
@app.route('/login/steam')
def login_steam():
    return redirect(
        'https://steamcommunity.com/openid/login?' +
        urllib.parse.urlencode({
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.mode': 'checkid_setup',
            'openid.return_to': f"{request.host_url.rstrip('/')}/auth/steam/callback",
            'openid.realm': request.host_url.rstrip('/'),
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        })
    )

@app.route('/auth/steam/callback')
def steam_callback():
    params = request.args.to_dict()
    params['openid.mode'] = 'check_authentication'

    try:
        response = requests.post('https://steamcommunity.com/openid/login', data=params)
        if 'is_valid:true' not in response.text:
            flash('Falha ao autenticar com a Steam.', 'error')
            return redirect(url_for('social'))

        steam_id_match = re.search(r'https://steamcommunity.com/openid/id/(\d+)', request.args.get('openid.claimed_id', ''))
        if not steam_id_match:
            flash('SteamID não encontrado.', 'error')
            return redirect(url_for('social'))

        steam_id = steam_id_match.group(1)

        user_info = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/', params={
            'key': STEAM_API_KEY,
            'steamids': steam_id
        }).json()

        player = user_info['response']['players'][0] if user_info['response']['players'] else {}

        games_response = requests.get('https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/', params={
            'key': STEAM_API_KEY,
            'steamid': steam_id,
            'include_appinfo': True,
            'include_played_free_games': True
        })

        games_data = games_response.json().get('response', {})
        owned_games = games_data.get('games', [])

        owned_games = sorted(owned_games, key=lambda g: g.get('playtime_forever', 0), reverse=True)[:10]

        jogos = [{
            'appid': g['appid'],
            'nome': g['name'],
            'tempo_total_horas': round(g['playtime_forever'] / 60, 1),
            'icone': f"https://cdn.cloudflare.steamstatic.com/steam/apps/{g['appid']}/header.jpg"
        } for g in owned_games]

        steam_data = {
            'steamid': steam_id,
            'username': player.get('personaname'),
            'avatar': player.get('avatarfull'),
            'profile_url': player.get('profileurl'),
            'country': player.get('loccountrycode'),
            'connected_at': datetime.now().isoformat(),
            'jogos_mais_jogados': jogos
        }

        session['steam_data'] = steam_data
        flash('Conta Steam vinculada com sucesso!', 'success')
        return redirect(url_for('social'))

    except Exception as e:
        print("Erro na autenticação Steam:", e)
        flash('Erro ao conectar com a Steam.', 'error')
        return redirect(url_for('social'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)