import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
from database import Database
from vk_handler import VKHandler
import os
from dotenv import load_dotenv

load_dotenv()


class Bot:
    def __init__(self):
        self.vk = vk_api.VkApi(token=os.getenv('VK_TOKEN'))
        self.longpoll = VkLongPoll(self.vk)
        self.db = Database()
        self.vk_handler = VKHandler(os.getenv('VK_TOKEN'))
        self.current_users = {}

    def start(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.handle_event(event)

    def handle_event(self, event):
        user_id = event.user_id
        text = event.text.lower()

        if text == 'привет':
            self.send_message(user_id, 'Привет! Начни поиск командой "поиск".', self.main_keyboard())
        elif text == 'поиск':
            self.start_search(user_id)
        elif text == 'далее':
            self.show_next_user(user_id)
        elif text == 'добавить в избранное':
            self.add_to_favorites(user_id)
        elif text == 'чёрный список':
            self.add_to_blacklist(user_id)
        elif text == 'мои избранные':
            self.show_favorites(user_id)
        else:
            self.send_message(user_id, 'Используйте кнопки для управления.', self.main_keyboard())

    def send_message(self, user_id, message, keyboard=None, attachments=None):
        params = {
            'user_id': user_id,
            'message': message,
            'random_id': random.randint(0, 2 ** 20),
            'keyboard': keyboard.get_keyboard() if keyboard else None,
            'attachment': ','.join(attachments) if attachments else None
        }
        self.vk.method('messages.send', params)

    def main_keyboard(self):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Поиск', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Далее', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Добавить в избранное', color=VkKeyboardColor.SECONDARY)
        keyboard.add_button('Чёрный список', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Мои избранные', color=VkKeyboardColor.SECONDARY)
        return keyboard

    def start_search(self, user_id):
        user_info = self.vk_handler.get_user_info(user_id)
        if not user_info:
            self.send_message(user_id, 'Не удалось получить ваши данные.')
            return

        self.db.add_user(user_id, user_info['first_name'], user_info['last_name'],
                         user_info['age'], user_info['sex'], user_info['city'])

        search_params = {
            'sex': 1 if user_info['sex'] == 2 else 2,
            'city': user_info['city'],
            'age_from': user_info['age'] - 2,
            'age_to': user_info['age'] + 2
        }

        found_users = self.vk_handler.search_users(search_params)
        filtered_users = [
            user for user in found_users
            if not self.db.check_blacklist(user_id, user['id'])
               and user['id'] not in self.db.get_favorites(user_id)
        ]

        self.current_users[user_id] = {'index': 0, 'users': filtered_users}
        self.show_user(user_id)

    def show_user(self, user_id):
        current = self.current_users.get(user_id)
        if not current or current['index'] >= len(current['users']):
            self.send_message(user_id, 'Пользователи закончились.')
            return

        user = current['users'][current['index']]
        photos = self.vk_handler.get_photos(user['id'])
        attachments = [f"photo{photo['owner_id']}_{photo['id']}" for photo in photos]

        message = (
            f"{user['first_name']} {user['last_name']}\n"
            f"Ссылка: vk.com/id{user['id']}"
        )
        self.send_message(user_id, message, self.main_keyboard(), attachments)

    def show_next_user(self, user_id):
        if user_id in self.current_users:
            self.current_users[user_id]['index'] += 1
            self.show_user(user_id)
        else:
            self.send_message(user_id, 'Начните поиск командой "поиск".')

    def add_to_favorites(self, user_id):
        current = self.current_users.get(user_id)
        if current:
            current_user = current['users'][current['index']]
            self.db.add_favorite(user_id, current_user['id'])
            self.send_message(user_id, 'Добавлено в избранное!')

    def add_to_blacklist(self, user_id):
        current = self.current_users.get(user_id)
        if current:
            current_user = current['users'][current['index']]
            self.db.add_to_blacklist(user_id, current_user['id'])
            self.send_message(user_id, 'Добавлено в чёрный список.')

    def show_favorites(self, user_id):
        favorites = self.db.get_favorites(user_id)
        if not favorites:
            self.send_message(user_id, 'Список избранных пуст.')
            return

        message = "Ваши избранные:\n"
        for fav in favorites:
            message += f"• vk.com/id{fav}\n"
        self.send_message(user_id, message)


if __name__ == '__main__':
    bot = Bot()
    bot.start()
