import os
import asyncio
from telethon import TelegramClient, functions, types
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, InputUserSelf, InputUser, InputPeerUser
from telethon.tl.functions import payments
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import time

# Загрузка переменных окружения
load_dotenv()

# Словарь подарков
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

class MTProtoGiftFinder:
    def __init__(self):
        self.client = TelegramClient(
            'mtproto_session',
            os.getenv('TELEGRAM_API_ID'),
            os.getenv('TELEGRAM_API_HASH')
        )
        self.semaphore = asyncio.Semaphore(10)  # Ограничиваем количество одновременных запросов

    async def start(self):
        """Запуск клиента"""
        await self.client.start(phone=os.getenv('TELEGRAM_PHONE'))

    async def stop(self):
        """Остановка клиента"""
        await self.client.disconnect()

    def print_user_info(self, user):
        """Вывод всей информации о пользователе"""
        print("\nИнформация о пользователе:")
        print("-" * 50)
        
        # Выводим все атрибуты объекта
        for attr in dir(user):
            # Пропускаем служебные атрибуты
            if not attr.startswith('_'):
                try:
                    value = getattr(user, attr)
                    # Пропускаем методы
                    if not callable(value):
                        print(f"{attr}: {value}")
                except Exception as e:
                    print(f"{attr}: [Ошибка получения значения: {str(e)}]")
        
        print("-" * 50)

    async def get_user_info(self, user_id):
        """Получение информации о пользователе"""
        try:
            # Получаем информацию о пользователе
            user = await self.client.get_entity(user_id)
            
            # Получаем полную информацию
            full_user = await self.client(functions.users.GetFullUserRequest(
                id=user_id
            ))
            
            return user, full_user
        except Exception as e:
            print(f"Ошибка при получении информации: {str(e)}")
            return None, None

    async def get_user_gifts(self, user_id, access_hash):
        """Получение подарков пользователя"""
        async with self.semaphore:  # Используем семафор для ограничения одновременных запросов
            try:
                # Создаем InputPeerUser для пользователя
                peer = InputPeerUser(
                    user_id=user_id,
                    access_hash=access_hash
                )
                
                # Получаем сохраненные подарки пользователя
                result = await self.client(functions.payments.GetSavedStarGiftsRequest(
                    peer=peer,
                    offset="",  # Начинаем с начала
                    limit=100,  # Максимальное количество подарков
                    exclude_unsaved=False,  # Включаем все подарки
                    exclude_saved=False,
                    exclude_unlimited=False,
                    exclude_limited=False,
                    exclude_unique=False,
                    sort_by_value=False
                ))
                
                if hasattr(result, 'gifts'):
                    return result.gifts
                return []
            except Exception as e:
                print(f"Ошибка при получении подарков: {str(e)}")
                return []

    async def get_group_participants(self, group_input):
        """Получение списка участников группы"""
        try:
            # Получаем информацию о группе
            try:
                # Пробуем получить группу по ID
                group_id = int(group_input)
                group = await self.client.get_entity(group_id)
            except ValueError:
                # Если не получилось, значит это ссылка
                group = await self.client.get_entity(group_input)
            
            participants = []
            offset = 0
            limit = 200  # Увеличиваем лимит для получения большего количества участников за один запрос

            while True:
                result = await self.client(GetParticipantsRequest(
                    channel=group,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=limit,
                    hash=0
                ))

                if not result.users:
                    break

                for user in result.users:
                    if user.username:
                        participants.append({
                            'id': user.id,
                            'username': user.username,
                            'access_hash': user.access_hash
                        })

                offset += len(result.users)
                if len(result.users) < limit:
                    break

            return participants
        except Exception as e:
            print(f"Ошибка при получении участников группы: {str(e)}")
            return []

    def is_valid_gift_format(self, gift):
        """Проверка формата подарка"""
        try:
            if not hasattr(gift, 'gift') or not hasattr(gift.gift, 'title'):
                return False
            
            title = gift.gift.title
            # Если gift_name не указан (режим просмотра всех), проверяем только на буквы
            if not hasattr(self, 'current_gift_name'):
                return all(c.isalpha() or c.isspace() for c in title)
            # Иначе проверяем точное совпадение
            return title == self.current_gift_name
        except Exception:
            return False

    def format_gift_info(self, gift):
        """Форматирование информации о подарке"""
        try:
            if not self.is_valid_gift_format(gift):
                return None
                
            return gift.gift.title
        except Exception as e:
            return None

    def print_gifts_list(self):
        """Вывод списка доступных подарков"""
        print("\nДоступные подарки:")
        for gift_id, gift_name in GIFTS.items():
            print(f"{gift_id}. {gift_name}")

async def check_participant(finder, participant, gift_name):
    """Проверка подарков у одного участника"""
    try:
        gifts = await finder.get_user_gifts(participant['id'], participant['access_hash'])
        user_gifts = []
        for gift in gifts:
            gift_info = finder.format_gift_info(gift)
            if gift_info:
                user_gifts.append(gift_info)
        
        if user_gifts:
            return participant['username'], user_gifts
        return None
    except Exception as e:
        print(f"Ошибка при проверке пользователя @{participant['username']}: {str(e)}")
        return None

async def main():
    finder = MTProtoGiftFinder()
    await finder.start()

    try:
        print("\nВыберите режим работы:")
        print("1. Проверка подарков у одного пользователя")
        print("2. Поиск подарков в группе")
        print("3. Показать список доступных подарков")
        mode = input("Введите номер режима (1, 2 или 3): ")

        if mode == "3":
            finder.print_gifts_list()
            return

        gift_id = input("Введите ID подарка (или 0 для просмотра всех подарков): ")
        try:
            gift_id = int(gift_id)
            if gift_id == 0:
                gift_name = None
            elif gift_id not in GIFTS:
                print("Неверный ID подарка")
                return
            else:
                gift_name = GIFTS[gift_id]
                finder.current_gift_name = gift_name
        except ValueError:
            print("ID подарка должен быть числом")
            return

        if mode == "1":
            username = input("Введите username пользователя (без @): ")
            try:
                user = await finder.client.get_entity(username)
                gifts = await finder.get_user_gifts(user.id, user.access_hash)
                
                valid_gifts = []
                for gift in gifts:
                    gift_info = finder.format_gift_info(gift)
                    if gift_info:
                        valid_gifts.append(gift_info)
                
                if valid_gifts:
                    if gift_name:
                        print(f"\nУ пользователя @{username} найден подарок: {gift_name}")
                    else:
                        print(f"\nУ пользователя @{username} найдены подарки:")
                        for i, gift in enumerate(valid_gifts, 1):
                            print(f"{i}. {gift}")
                else:
                    if gift_name:
                        print(f"\nУ пользователя @{username} нет подарка {gift_name}")
                    else:
                        print(f"\nУ пользователя @{username} нет подарков нужного формата")
            except Exception as e:
                print(f"Ошибка при получении информации о пользователе: {str(e)}")

        elif mode == "2":
            group_input = input("Введите ID группы (например, -1001905581924) или ссылку на группу: ")
            
            print("\nПолучение списка участников группы...")
            participants = await finder.get_group_participants(group_input)
            
            if not participants:
                print("Не удалось получить список участников группы")
                return
            
            print(f"Найдено {len(participants)} участников")
            print("\nПоиск пользователей с подарками...")
            
            # Создаем список задач для асинхронного выполнения
            tasks = []
            for participant in participants:
                task = asyncio.create_task(check_participant(finder, participant, gift_name))
                tasks.append(task)
            
            # Ждем завершения всех задач
            results = await asyncio.gather(*tasks)
            
            # Фильтруем результаты
            users_with_gifts = [result for result in results if result is not None]
            
            if users_with_gifts:
                if gift_name:
                    print(f"\nНайдено {len(users_with_gifts)} пользователей с подарком {gift_name}:")
                    for i, (username, _) in enumerate(users_with_gifts, 1):
                        print(f"{i}. @{username}")
                else:
                    print(f"\nНайдено {len(users_with_gifts)} пользователей с подарками нужного формата:")
                    for i, (username, gifts) in enumerate(users_with_gifts, 1):
                        print(f"\n{i}. @{username} - {len(gifts)} подарков:")
                        for j, gift in enumerate(gifts, 1):
                            print(f"   {j}. {gift}")
            else:
                if gift_name:
                    print(f"\nПользователей с подарком {gift_name} не найдено")
                else:
                    print("\nПользователей с подарками нужного формата не найдено")
        
        else:
            print("Неверный режим работы")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    
    finally:
        await finder.stop()

if __name__ == "__main__":
    asyncio.run(main()) 