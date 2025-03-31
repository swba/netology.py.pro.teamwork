# Пакет `vk_client`

Данный пакет реализует интеграцию с API ВКонтакте и 
предоставляет соответствующий класс `VkClient`.

Пример использования:
```python
from vk_client import VkClient

vk_client = VkClient('VK_API_TOKEN')

# Получение данных пользователя.
vk_user = vk_client.get_user(1)
# Переменная vk_user - это объект класса VkUser.
# Печатаем полное имя пользователя.
print(f'Полное имя: {vk_user.first_name} {vk_user.last_name}')
# Получаем возраст пользователя (может быть пустым).
if vk_user.age:
    print(f'Возраст: {vk_user.age}')
# Получаем пол пользователя (может быть пустым).
if vk_user.gender:
    print(f"Пол: {'Мужской' if vk_user.gender == 'male' else 'Женский'}")
# Получаем город пользователя (может быть пустым):
if vk_user.city:
    print(f'Город: {vk_user.city.title} (#{vk_user.city.id})')

# Получение данных нескольких пользователей.
# Переменная vk_users - это список объектов класса VkUser. 
vk_users = vk_client.get_users([1, 13, 666])
print(vk_users)

# Поиск пользователей.
# Ищем 5 мужчин от 38 до 42 лет, исключая Павла Дурова.
# Переменная vk_users - это список объектов класса VkUser. 
vk_users = vk_client.search_users(exclude=[1], age_from=38, age_to=42, count=10)
print(vk_users)

# Получение фотографий пользователя.
# По умолчанию возвращаются фотографии профиля.
# Переменная vk_photos - это список объектов класса VkPhoto.
vk_photos = vk_client.get_user_photos(1)
print(vk_photos)

# Можно получать фотографии из любого альбома, например, со
# стены (album_id='wall'). 
vk_photos = vk_client.get_user_photos(1, album_id='wall', count=5)
print(vk_photos)

# При задании параметра top будет возвращено не более, чем top
# фотографий, отсортированных в порядке убывания количества
# лайков.
vk_photos = vk_client.get_user_photos(1, top=3, album_id='wall')
print(vk_photos)

# Поставить лайк под фото.
vk_client.like_photo(666)
# Убрать лайк.
vk_client.unlike_photo(666)
```

**ВАЖНО**: для работы метода поиска пользователей `search_users` 
должен использоваться 
[ключ доступа пользователя](https://dev.vk.com/ru/api/access-token/getting-started#%D0%9A%D0%BB%D1%8E%D1%87%20%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0%20%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D1%8F).
Использование сервисного ключа доступа или ключа доступа 
сообщества приведёт к ошибке доступа.
