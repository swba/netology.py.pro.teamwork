import pytest
from unittest.mock import MagicMock
from vk_handler import VKHandler
from vk_api.exceptions import ApiError
from datetime import date, datetime


@pytest.fixture
def vk():
    mock_vk = MagicMock()
    mock_api = MagicMock()
    mock_vk.get_api.return_value = mock_api
    return mock_vk


@pytest.fixture
def vk_handler_mock():
    """Фикстура для тестирования VKHandler"""
    handler = VKHandler('token')
    handler.vk = MagicMock()
    return handler


def test_get_user_info_success():
    # Создаем mock API
    mock_api = MagicMock()

    # Настраиваем возвращаемые данные
    mock_api.users.get.return_value = [{
        'first_name': 'Test',
        'last_name': 'User',
        'bdate': '1.1.1990',
        'city': {'title': 'Moscow'},
        'sex': 2,
        'interests': 'music,books'
    }]

    # Создаем обработчик с передачей mock API
    handler = VKHandler('test_token', api=mock_api)

    # Вызываем метод
    result = handler.get_user_info(123)

    # Проверяем результаты
    assert result is not None
    assert result['first_name'] == 'Test'
    assert result['last_name'] == 'User'
    assert result['age'] == datetime.now().year - 1990
    assert result['city']['title'] == 'Moscow'
    assert result['sex'] == 2
    assert result['interests'] == 'music,books'


def test_search_users():
    # Создаем mock API
    mock_api = MagicMock()

    # Настраиваем возвращаемые данные
    mock_api.users.search.return_value = {
        'items': [
            {
                'id': 1,
                'first_name': 'Test',
                'last_name': 'User',
                'city': {'title': 'Moscow'},
                'photo_max_orig': 'photo_url'
            }
        ]
    }

    # Создаем обработчик с передачей mock API
    handler = VKHandler('test_token', api=mock_api)

    # Параметры поиска
    search_params = {
        'sex': 1,
        'age_from': 20,
        'city': 'Moscow',
        'age_to': 30
    }

    # Вызываем метод
    users = handler.search_users(search_params)

    # Проверяем результаты
    assert len(users) == 1
    assert users[0]['first_name'] == 'Test'
    assert users[0]['city']['title'] == 'Moscow'

    # Проверяем вызов API (теперь без status=1, так как он добавляется внутри метода)
    mock_api.users.search.assert_called_once_with(
        count=1000,
        has_photo=1,
        fields='city,photo_max_orig',
        sex=1,
        age_from=20,
        age_to=30,
        city='Moscow',
        status=1  # Теперь этот параметр добавляется внутри метода
    )


# тест для случая, когда дата рождения неполная:
def test_get_user_info_incomplete_bdate():
    # Создаем mock API
    mock_api = MagicMock()
    mock_api.users.get.return_value = [{
        'first_name': 'Test',
        'last_name': 'User',
        'bdate': '1.1',  # Неполная дата
        'city': {'title': 'Moscow'},
        'sex': 2,
        'country': {'title': 'Russia'}
    }]

    # Создаем обработчик с передачей mock API
    handler = VKHandler('test_token', api=mock_api)

    # Вызываем метод
    info = handler.get_user_info(123)

    # Проверяем что данные получены
    assert info is not None
    # Проверяем что установлен возраст по умолчанию
    assert info['age'] == 25  # Ожидаем значение по умолчанию


# обработка случая полного отсутствия даты рождения:
def test_get_user_info_no_bdate():
    mock_api = MagicMock()
    mock_api.users.get.return_value = [{
        'first_name': 'Test',
        'last_name': 'User',
        'city': {'title': 'Moscow'},
        'sex': 2
    }]

    handler = VKHandler('test_token', api=mock_api)
    info = handler.get_user_info(123)

    assert info is not None
    assert info['age'] == 25  # Проверяем значение по умолчанию


# тест для случая, когда город не указан:
def test_get_user_info_no_city():
    # Создаем mock API
    mock_api = MagicMock()

    # Настраиваем возвращаемые данные (без города, но с country)
    mock_api.users.get.return_value = [{
        'first_name': 'Test',
        'last_name': 'User',
        'bdate': '1.1.1990',
        'country': {'title': 'Russia'},
        'sex': 2
    }]

    # Создаем обработчик с передачей mock API
    handler = VKHandler('test_token', api=mock_api)

    # Вызываем метод
    info = handler.get_user_info(123)

    # Проверяем что данные получены
    assert info is not None
    # Проверяем что установлен город по умолчанию
    assert info['city']['title'] == 'Не указан'  # Ожидаем значение по умолчанию


# тест для случая, когда нет ни города, ни страны:
def test_get_user_info_no_city_no_country():
    mock_api = MagicMock()
    mock_api.users.get.return_value = [{
        'first_name': 'Test',
        'last_name': 'User',
        'sex': 2
    }]

    handler = VKHandler('test_token', api=mock_api)
    info = handler.get_user_info(123)

    assert info is not None
    # Проверяем структуру и значение города по умолчанию
    assert info['city'] == {'title': 'Не указан'}


def test_get_user_info_empty_response():
    # Создаем мок VK API
    mock_vk = MagicMock()
    mock_vk.users.get.return_value = []  # Пустой ответ

    # Создаем обработчик с подменой API
    handler = VKHandler('test_token')
    handler.vk = mock_vk

    # Вызываем метод
    result = handler.get_user_info(123)

    # Проверяем что вернулся None
    assert result is None

    # Проверяем что API было вызвано
    mock_vk.users.get.assert_called_once_with(
        user_ids=123,
        fields='sex,city,bdate,interests'
    )


# тест для случая с некорректными данными:
def test_get_user_info_invalid_city_data():
    # Создаем мок API с некорректными данными города
    mock_api = MagicMock()
    mock_api.users.get.return_value = [{
        'id': 123,
        'first_name': 'Test',
        'last_name': 'User',
        'sex': 2,
        'city': 'Moscow',  # Строка вместо словаря
        'bdate': '1.1.1990',
        'interests': 'music'
    }]

    # Инициализируем обработчик с мок API
    handler = VKHandler('test_token')
    handler.vk = mock_api

    # Получаем информацию
    info = handler.get_user_info(123)

    # Проверяем что метод вернул данные
    assert info is not None
    assert info['first_name'] == 'Test'
    assert info['last_name'] == 'User'
    assert info['city']['title'] == 'Moscow'  # Город должен быть корректно обработан
    assert info['age'] == (datetime.now().year - 1990)


def test_get_user_info():
    # 1. Создаем мок VK API
    mock_vk = MagicMock()

    # 2. Настраиваем возвращаемые значения
    mock_vk.users.get.return_value = [{
        'first_name': 'Test',
        'last_name': 'User',
        'sex': 2,
        'city': {'title': 'Moscow'},
        'bdate': '1.1.1990',
        'interests': 'music'
    }]

    # 3. Создаем обработчик с моком API
    handler = VKHandler('test_token')
    handler.vk = mock_vk  # Подменяем реальный API на мок

    # 4. Вызываем метод
    info = handler.get_user_info(123)

    # 5. Проверяем результаты
    assert info is not None
    assert info['first_name'] == 'Test'
    assert info['last_name'] == 'User'
    assert info['city']['title'] == 'Moscow'
    assert info['age'] == (datetime.now().year - 1990)
    assert info['interests'] == 'music'


def test_vk_api_not_initialized():
    # Создаем обработчик
    handler = VKHandler('token')

    # Создаем неправильно инициализированный мок API
    mock_vk = MagicMock()
    del mock_vk.users  # Удаляем атрибут users для эмуляции ошибки
    handler.vk = mock_vk

    # Вызываем метод и проверяем возврат None
    assert handler.get_user_info(123) is None

    # Проверяем что ошибка была залогирована
    # (здесь нужно использовать ваш механизм проверки логов)


def test_get_user_info_with_mock(vk_handler_mock):
    # Настраиваем мок
    vk_handler_mock.vk.users.get.return_value = [{
        'first_name': 'Mock',
        'last_name': 'User',
        'sex': 1,
        'bdate': '15.5.1995'
    }]

    info = vk_handler_mock.get_user_info(123)

    assert info['first_name'] == 'Mock'
    assert info['age'] == (datetime.now().year - 1995)
