from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
import asyncio
from telethon import TelegramClient, functions, types
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import logging
import threading
from telethon.tl.functions.auth import SendCodeRequest
from telethon.tl.types import CodeSettings
import subprocess
import sys
from telethon.errors import FloodWaitError
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.errors import PhoneCodeInvalidError, PhoneCodeExpiredError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, resources={r"/*": {"origins": "*"}})

# Загрузка конфигурации
load_dotenv()
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

logger.info(f"Loaded configuration: API_ID={API_ID}, PHONE={PHONE}")

# Глобальный клиент Telegram
client = None
auth_code_event = asyncio.Event()
auth_code = None

async def init_client():
    """Инициализация клиента Telegram"""
    global client
    if client is None:
        logger.info("Initializing new Telegram client...")
        client = TelegramClient('telegram_session', API_ID, API_HASH)
        await client.connect()
        logger.info("Telegram client connected")
        
        # Проверяем статус авторизации
        is_authorized = await client.is_user_authorized()
        logger.info(f"Client authorization status: {is_authorized}")
        
        if not is_authorized:
            logger.info("Client is not authorized, will need to start auth process")
    return client

async def start_client():
    global client, auth_code_event, auth_code
    if client is None:
        client = TelegramClient('telegram_session', API_ID, API_HASH)
        
        try:
            logger.info("Starting client...")
            await client.start(phone=PHONE)
            logger.info("Client started successfully")
        except Exception as e:
            logger.error(f"Error in start_client: {str(e)}")
            raise e

# Список всех подарков
GIFTS = {
    1: "Bunny Muffin",
    2: "Candy Cane",
    3: "Cookie Heart",
    4: "Crystal Ball",
    5: "Desk Calendar",
    6: "Diamond Ring",
    7: "Durov's Cap",
    8: "Easter Egg",
    9: "Electric Skull",
    10: "Eternal Candle",
    11: "Eternal Rose",
    12: "Evil Eye",
    13: "Flying Broom",
    14: "Gem Signet",
    15: "Genie Lamp",
    16: "Ginger Cookie",
    17: "Hanging Star",
    18: "Heroic Helmet",
    19: "Hex Pot",
    20: "Holiday Drink",
    21: "Homemade Cake",
    22: "Hypno Lollipop",
    23: "Ion Gem",
    24: "Jack-in-the-Box",
    25: "Jelly Bunny",
    26: "Jester Hat",
    27: "Jingle Bell",
    28: "Kissed Frog",
    29: "Light Sword",
    30: "Lol Pop",
    31: "Loot Bag",
    32: "Love Candle",
    33: "Love Potion",
    34: "Lunar Snake",
    35: "Mad Pumpkin",
    36: "Magic Potion",
    37: "Mini Oscar",
    38: "Nail Bracelet",
    39: "Neko Helmet",
    40: "Party Sparkler",
    41: "Perfume Bottle",
    42: "Pet Snake",
    43: "Plush Pepe",
    44: "Precious Peach",
    45: "Record Player",
    46: "Restless Jar",
    47: "Sakura Flower",
    48: "Santa Hat",
    49: "Scared Cat",
    50: "Sharp Tongue",
    51: "Signet Ring",
    52: "Skull Flower",
    53: "Sleigh Bell",
    54: "Snake Box",
    55: "Snow Globe",
    56: "Snow Mitten",
    57: "Spiced Wine",
    58: "Spy Agaric",
    59: "Star Notepad",
    60: "Swiss Watch",
    61: "Tama Gadget",
    62: "Top Hat",
    63: "Toy Bear",
    64: "Trapped Heart",
    65: "Vintage Cigar",
    66: "Voodoo Doll",
    67: "Winter Wreath",
    68: "Witch Hat",
    69: "Xmas Stocking"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/gifts', methods=['GET'])
def get_gifts():
    return jsonify(GIFTS)

@app.route('/api/auth/status', methods=['GET'])
async def auth_status():
    try:
        logger.info("Checking auth status...")
        await init_client()
        is_authorized = await client.is_user_authorized()
        logger.info(f"Auth status: {is_authorized}")
        return jsonify({'authorized': is_authorized})
    except Exception as e:
        logger.error(f"Auth status error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/start', methods=['POST'])
async def auth_start():
    try:
        logger.info("Starting auth process...")
        data = request.json
        logger.info(f"Request data: {data}")
        
        if not data:
            logger.warning("No JSON data in request")
            return jsonify({'error': 'No data provided'}), 400
            
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        phone = data.get('phone')
        
        if not api_id or not api_hash or not phone:
            logger.warning("Missing required fields")
            return jsonify({'error': 'API ID, API Hash и номер телефона обязательны'}), 400
            
        logger.info(f"Using API ID: {api_id}, phone: {phone}")
        
        # Создаем нового клиента с переданными данными
        global client
        client = TelegramClient('telegram_session', api_id, api_hash)
        await client.connect()
        logger.info("Telegram client connected")
        
        if await client.is_user_authorized():
            logger.info("User is already authorized")
            return jsonify({'status': 'already_authorized'})
            
        logger.info("User not authorized, starting auth process...")
        
        try:
            # Отправляем код
            await client.send_code_request(phone)
            logger.info("Code sent successfully")
            return jsonify({'status': 'code_sent'})
        except FloodWaitError as e:
            wait_time = e.seconds
            hours = wait_time // 3600
            minutes = (wait_time % 3600) // 60
            error_msg = f'Слишком много попыток. Пожалуйста, подождите {hours} ч. {minutes} мин. перед следующей попыткой.'
            logger.warning(f"FloodWaitError: {error_msg}")
            return jsonify({'error': error_msg}), 429
            
    except Exception as e:
        logger.error(f"Auth start error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/code', methods=['POST'])
async def auth_code():
    try:
        logger.info("Received code request")
        data = request.json
        logger.info(f"Request data: {data}")
        
        if not data or 'code' not in data:
            logger.warning("No code provided in request")
            return jsonify({'error': 'Код не указан'}), 400
            
        code = data['code']
        logger.info(f"Code from request: {code}")
        
        if not client:
            logger.error("Client not initialized")
            return jsonify({'error': 'Клиент не инициализирован'}), 500
            
        try:
            logger.info(f"Attempting to sign in with code: {code}")
            # Добавляем таймаут для операции
            try:
                await asyncio.wait_for(client.sign_in(code=code), timeout=30)
                logger.info("Successfully signed in with code")
                return jsonify({'status': 'success'})
            except asyncio.TimeoutError:
                logger.error("Sign in operation timed out")
                return jsonify({'error': 'Превышено время ожидания ответа от Telegram'}), 408
                
        except SessionPasswordNeededError:
            logger.info("2FA password required")
            return jsonify({'status': 'password_required'})
        except PhoneCodeInvalidError:
            logger.error("Invalid phone code")
            return jsonify({'error': 'Неверный код подтверждения'}), 400
        except PhoneCodeExpiredError:
            logger.error("Phone code expired")
            return jsonify({'error': 'Срок действия кода истек'}), 400
        except Exception as e:
            logger.error(f"Code sign in error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Ошибка при вводе кода: {str(e)}'}), 400
            
    except Exception as e:
        logger.error(f"Auth code error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/password', methods=['POST'])
async def auth_password():
    logger.info("Received password request")
    try:
        data = request.json
        logger.info(f"Request data: {data}")
        
        if not data:
            logger.warning("No JSON data in request")
            return jsonify({'error': 'No data provided'}), 400
            
        password = data.get('password')
        logger.info(f"Password from request: {password}")
        
        if not password:
            logger.warning("Password not provided in request")
            return jsonify({'error': 'Password is required'}), 400
            
        logger.info("Attempting to sign in with password...")
        
        try:
            # Используем client.start() для авторизации с паролем
            logger.info("Calling client.start() with password...")
            await client.start(password=password)
            logger.info("Successfully signed in with password")
            
            # Сохраняем сессию
            await client.save_session()
            return jsonify({'status': 'success'})
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Password sign in error: {error_msg}", exc_info=True)
            return jsonify({'error': f'Ошибка при вводе пароля: {error_msg}'}), 500
    except Exception as e:
        logger.error(f"Auth password error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_user', methods=['POST'])
async def check_user():
    try:
        await init_client()
        data = request.json
        username = data.get('username')
        gift_id = int(data.get('gift_id', 0))

        if not username:
            return jsonify({'error': 'Username is required'}), 400

        # Получение информации о пользователе
        user = await client.get_entity(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Получение подарков пользователя
        gifts = []
        async for message in client.iter_messages(user, limit=100):
            if message.gift:
                gift_name = message.gift.title
                if gift_id == 0 or (gift_id in GIFTS and GIFTS[gift_id] == gift_name):
                    gifts.append({
                        'name': gift_name,
                        'date': message.date.isoformat(),
                        'id': message.id
                    })

        return jsonify({
            'username': username,
            'gifts': gifts,
            'total': len(gifts)
        })

    except Exception as e:
        logger.error(f"Check user error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_group', methods=['POST'])
async def check_group():
    try:
        await init_client()
        data = request.json
        group_id = data.get('group_id')
        gift_id = int(data.get('gift_id', 0))

        if not group_id:
            return jsonify({'error': 'Group ID is required'}), 400

        # Получение информации о группе
        group = await client.get_entity(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404

        # Получение участников группы
        participants = []
        async for user in client.iter_participants(group, limit=200):
            try:
                async for message in client.iter_messages(user, limit=100):
                    if message.gift:
                        gift_name = message.gift.title
                        if gift_id == 0 or (gift_id in GIFTS and GIFTS[gift_id] == gift_name):
                            participants.append({
                                'username': user.username,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'gift': gift_name,
                                'date': message.date.isoformat()
                            })
                            break
            except Exception as e:
                continue

        return jsonify({
            'group_id': group_id,
            'participants': participants,
            'total': len(participants)
        })

    except Exception as e:
        logger.error(f"Check group error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080) 