import os
import asyncio
import shutil
from telethon import TelegramClient
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

async def main():
    session_file = 'telegram_session'
    
    # Создаем клиент
    client = TelegramClient(
        session_file,
        os.getenv('TELEGRAM_API_ID'),
        os.getenv('TELEGRAM_API_HASH')
    )
    
    try:
        # Подключаемся
        await client.connect()
        print("Connected to Telegram")
        
        # Запускаем авторизацию
        try:
            await client.start(
                phone=os.getenv('TELEGRAM_PHONE'),
                code_callback=lambda: input('Please enter the code you received: '),
                password=lambda: input('Please enter your 2FA password: ')
            )
            print("Successfully authorized!")
        except Exception as e:
            print(f"Error during authorization: {str(e)}")
            # Удаляем файл сессии в случае ошибки
            if os.path.exists(session_file + '.session'):
                os.remove(session_file + '.session')
            raise
    finally:
        # Отключаемся
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 