import pytest
from unittest.mock import MagicMock, patch
from bot import Bot
from vk_api.longpoll import VkEventType
import json


@pytest.fixture
def mock_bot():
    """Фикстура для тестирования бота с моками"""
    with patch('bot.Database'), patch('bot.VKHandler'), patch('bot.vk_api.VkApi'):
        bot = Bot()
        bot._send_message = MagicMock()
        bot.db = MagicMock()
        bot.vk_handler = MagicMock()

        # Добавляем моки для других методов
        bot._start_search = MagicMock()
        bot._show_favorites = MagicMock()
        return bot


def test_handle_text_start_search(mock_bot):
    """Тест обработки команды 'поиск'"""
    mock_event = MagicMock()
    mock_event.user_id = 123
    mock_event.text = 'поиск'
    mock_event.payload = None

    mock_bot._start_search = MagicMock()
    mock_bot._handle_text(mock_event.user_id, mock_event.text)

    mock_bot._start_search.assert_called_once_with(123)


def test_handle_payload_add_favorite(mock_bot):
    """Тест обработки добавления в избранное"""
    payload = json.dumps({'type': 'add_fav', 'user_id': 456})
    mock_bot.db.add_favorite.return_value = True

    mock_bot._handle_payload(123, json.loads(payload))

    mock_bot.db.add_favorite.assert_called_once_with(123, 456)
    mock_bot._send_message.assert_called_with(123, "Пользователь добавлен в избранное!")


def test_handle_payload_like_photo(mock_bot):
    """Тест обработки лайка фото"""
    payload = json.dumps({'type': 'like', 'photo_id': 789, 'owner_id': 456})
    mock_bot.vk_handler.like_photo.return_value = True

    mock_bot._handle_payload(123, json.loads(payload))

    mock_bot.vk_handler.like_photo.assert_called_once_with(789, 456)
    mock_bot._send_message.assert_called_with(123, "Лайк поставлен!")


def test_show_user(mock_bot):
    """Тест отображения пользователя"""
    # Подготовка тестовых данных
    mock_bot.user_states = {
        123: {
            'users': [{
                'id': 456,
                'first_name': 'Test',
                'last_name': 'User',
                'age': 25,
                'city': 'Moscow'
            }],
            'index': 0
        }
    }

    # Настройка mock для фотографий
    mock_bot.vk_handler.get_photos.return_value = [{
        'owner_id': 456,
        'id': 789,
        'likes': {'count': 10}
    }]

    # Настройка mock для клавиатуры
    mock_bot.vk_handler.create_keyboard.return_value = 'keyboard_json'

    # Вызов тестируемого метода
    mock_bot._show_user(123)

    # Проверка вызова _send_message
    mock_bot._send_message.assert_called_once_with(
        user_id=123,
        message=(
            "Test User\n"
            "Возраст: 25\n"
            "Город: Moscow\n"
            "Ссылка: https://vk.com/id456"
        ),
        keyboard='keyboard_json',
        attachment='photo456_789'
    )


# тест для случая без фотографий:
def test_show_user_no_photos(mock_bot):
    """Тест отображения пользователя без фото"""
    # Настройка mock для _show_next_user
    mock_bot._show_next_user = MagicMock()

    # Подготовка тестовых данных
    mock_bot.user_states = {
        123: {
            'users': [{
                'id': 456,
                'first_name': 'Test'
            }],
            'index': 0
        }
    }

    # Настройка mock для пустого списка фото
    mock_bot.vk_handler.get_photos.return_value = []

    # Вызов тестируемого метода
    mock_bot._show_user(123)

    # Проверка что был вызван _show_next_user
    mock_bot._show_next_user.assert_called_once_with(123)

    # Проверка что _send_message не вызывался
    mock_bot._send_message.assert_not_called()


# Тест для случая с одной фотографией:
def test_show_user_one_photo(mock_bot):
    mock_bot._show_next_user = MagicMock()
    mock_bot.user_states = {
        123: {
            'users': [{
                'id': 456,
                'first_name': 'Test',
                'last_name': 'User',  # Добавлено обязательное поле
                'age': 25,  # Добавлено для полноты теста
                'city': 'Moscow'  # Добавлено для полноты теста
            }],
            'index': 0
        }
    }
    mock_bot.vk_handler.get_photos.return_value = [{
        'owner_id': 456,
        'id': 789,
        'likes': {'count': 5}
    }]
    mock_bot.vk_handler.create_keyboard.return_value = 'keyboard_json'  # Добавлен mock для клавиатуры

    mock_bot._show_user(123)

    # Проверяем что _show_next_user не вызывался
    mock_bot._show_next_user.assert_not_called()

    # Проверяем что _send_message вызван с правильными параметрами
    mock_bot._send_message.assert_called_once()
    args = mock_bot._send_message.call_args[1]
    assert args['attachment'] == 'photo456_789'
    assert "Test User" in args['message']
    assert "Возраст: 25" in args['message']
    assert "Город: Moscow" in args['message']


# Тест для случая с несколькими фотографиями:
def test_show_user_multiple_photos(mock_bot):
    mock_bot.user_states = {
        123: {
            'users': [{'id': 456}],
            'index': 0
        }
    }
    mock_bot.vk_handler.get_photos.return_value = [
        {'owner_id': 456, 'id': 1},
        {'owner_id': 456, 'id': 2},
        {'owner_id': 456, 'id': 3}
    ]

    mock_bot._show_user(123)

    args = mock_bot._send_message.call_args[1]
    assert args['attachment'] == 'photo456_1,photo456_2,photo456_3'


# тест для случая, когда пользователи закончились:
def test_show_user_no_more_users(mock_bot):
    mock_bot.user_states = {
        123: {
            'users': [],
            'index': 0
        }
    }

    mock_bot._show_user(123)

    # Проверяем что сообщение было отправлено с правильным текстом
    assert mock_bot._send_message.call_count == 1
    assert mock_bot._send_message.call_args[0] == (123, "Пользователи закончились.")


def test_start_search_with_cache(mocker):
    """Тест начала поиска с использованием кэша"""
    # 1. Инициализация бота
    bot = Bot()

    # 2. Мокирование зависимостей
    mock_get_user_info = mocker.patch.object(
        bot.vk_handler,
        'get_user_info',
        return_value={
            'first_name': 'Test',
            'last_name': 'User',
            'sex': 2,
            'city': {'title': 'Moscow', 'id': 1},
            'age': 25,
            'interests': ''
        }
    )

    mock_get_cached = mocker.patch.object(
        bot.db,
        'get_cached_results',
        return_value=[{
            'id': 456,
            'first_name': 'Cached',
            'last_name': 'User',
            'city': {'title': 'Moscow', 'id': 1},
            'age': 24
        }]
    )

    # 3. Вызов тестируемого метода
    bot._start_search(123)

    # 4. Проверки
    mock_get_user_info.assert_called_once_with(123)

    expected_params = {
        'user_id': 123,
        'sex': 1,
        'city': 'Moscow',
        'age_from': 20,
        'age_to': 30,
        'interests': ''
    }
    mock_get_cached.assert_called_once_with(123, expected_params)

    # 5. Проверка состояния
    assert 123 in bot.user_states
    assert bot.user_states[123]['users'][0]['id'] == 456


def test_show_favorites():
    """Тест отображения избранного"""
    # 1. Создаем реальный экземпляр бота
    bot = Bot()

    # 2. Мокируем зависимости
    bot.db = MagicMock()
    bot._send_message = MagicMock()
    bot._main_keyboard = MagicMock(return_value='keyboard_mock')

    # 3. Настраиваем тестовые данные
    test_favorites = [111, 222, 333]
    bot.db.get_favorites.return_value = test_favorites

    # 4. Вызываем тестируемый метод
    bot._show_favorites(123)

    # 5. Проверяем вызовы к БД
    bot.db.get_favorites.assert_called_once_with(123)

    # 6. Проверяем вызов отправки сообщения (с позиционными аргументами)
    expected_message = "Ваши избранные:\n1. vk.com/id111\n2. vk.com/id222\n3. vk.com/id333"
    bot._send_message.assert_called_once_with(
        123,  # user_id (позиционный)
        expected_message,  # message (позиционный)
        'keyboard_mock'  # keyboard (позиционный)
    )


def test_error_handling():
    bot = Bot()
    bot._send_message = MagicMock()

    # Создаем событие, которое точно пройдет условия
    event = MagicMock()
    event.type = VkEventType.MESSAGE_NEW
    event.to_me = True
    event.user_id = 123
    event.text = 'test'
    event.payload = None

    # Имитируем ошибку
    with patch.object(bot, '_handle_text', side_effect=Exception("Test")):
        bot._handle_event(event)

        # Проверяем аргументы вызова
        args, kwargs = bot._send_message.call_args
        assert args[0] == 123  # user_id
        assert "Произошла ошибка при обработке команды" in args[1]


# Параметризованные тесты
@pytest.mark.parametrize("command,expected", [
    ('поиск', '_start_search'),
    ('избранное', '_show_favorites'),
    ('test', '_send_message')
])
def test_text_commands(mock_bot, command, expected):
    # Создаем mock события
    event = MagicMock(spec=VkEventType)
    event.type = VkEventType.MESSAGE_NEW
    event.to_me = True
    event.user_id = 123
    event.text = command
    event.payload = None

    # Вызываем обработчик события
    mock_bot._handle_event(event)

    # Проверяем вызов нужного метода
    getattr(mock_bot, expected).assert_called_once()


# тестирование обработки payload
def test_handle_payload(mock_bot):
    # Создаем mock события с payload
    event = MagicMock(spec=VkEventType)
    event.type = VkEventType.MESSAGE_NEW
    event.to_me = True
    event.user_id = 123
    event.text = ''
    event.payload = '{"type": "like", "photo_id": 123}'

    mock_bot._handle_payload = MagicMock()

    # Вызываем обработчик события
    mock_bot._handle_event(event)

    # Проверяем что _handle_payload был вызван
    mock_bot._handle_payload.assert_called_once_with(123, {"type": "like", "photo_id": 123})


def test_start_search_with_missing_fields():
    """Тест поиска с отсутствующими полями"""
    # 1. Создаем реальный экземпляр бота
    bot = Bot()

    # 2. Мокируем зависимости
    bot.vk_handler = MagicMock()
    bot.db = MagicMock()

    # 3. Настраиваем тестовые данные
    test_user_info = {
        'first_name': 'Test',
        'last_name': 'User',
        'sex': 2,
        'city': {'title': 'Moscow'},
        'age': 25,
        'interests': ''
    }
    bot.vk_handler.get_user_info.return_value = test_user_info

    # 4. Настраиваем поведение БД
    bot.db.get_cached_results.return_value = None  # Нет кэшированных результатов
    bot.db.check_blacklist.return_value = False
    bot.db.get_favorites.return_value = []

    # 5. Настраиваем результат поиска
    test_users = [{
        'id': 456,
        'first_name': 'Found',
        'city': {'title': 'Moscow'},
        'age': 24
    }]
    bot.vk_handler.search_users.return_value = test_users

    # 6. Вызываем тестируемый метод
    bot._start_search(123)

    # 7. Проверяем вызовы
    bot.vk_handler.get_user_info.assert_called_once_with(123)
    bot.vk_handler.search_users.assert_called_once()

    # 8. Проверяем сохранение состояния
    assert 123 in bot.user_states
    assert len(bot.user_states[123]['users']) == 1
    assert bot.user_states[123]['users'][0]['id'] == 456
