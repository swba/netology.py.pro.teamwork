import requests
from pprint import pprint
import configparser
from datetime import datetime

config = configparser.ConfigParser()

config.read('config.ini')
vk_token = config['Password']['vk_token']


class VK:

    def __init__(self, token, version='5.199', url='https://api.vk.ru/method/'):
        self.base = url
        self.params = {
            'access_token': token,
            'v': version
            }

    
    # Получаем имя пользователя
    def get_first_name(self, owner_id, atrrb='sex', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        get_sex = response.json()
        for sex in get_sex['response']:
            return sex['first_name']

    
    # Получаем фамилию пользователя
    def get_last_name(self, owner_id, atrrb='sex', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        get_sex = response.json()
        for sex in get_sex['response']:
            return sex['last_name']

    
    # Получаем город пользователя
    def get_city(self, owner_id, atrrb='city', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        get_city = response.json()
        if 'response' not in get_city or not get_city['response']:
            return "Город не указан"
        user_data = get_city['response'][0]
        if 'city' not in user_data or not user_data['city']:
            return "Город не указан"
        
        return user_data['city']['title']

    
    # Получаем возраст пользователя
    def get_age(self, owner_id, atrrb='bdate', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        data = response.json()
        
        # Проверяем, есть ли дата рождения в ответе
        if 'response' not in data or not data['response']:
            return None
        
        bdate_str = data['response'][0].get('bdate')
        if not bdate_str:
            return f'Возраст не указан'  # Даты рождения нет или она скрыта
        
        # Преобразуем строку даты в возраст
        try:
            birth_date = datetime.strptime(bdate_str, "%d.%m.%Y").date()
            today = datetime.now().date()
            age = today.year - birth_date.year
            
            # Проверяем, был ли уже день рождения в этом году
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
                
            return age
        except ValueError:
            for bdate in data['response']:
                res = bdate['bdate']
            # Обработка случая, если дата в формате без года (например, "12.08")
            return f'Указаны только день и месяц рождения: {res}'

    
    # Получаем пол пользователя
    def get_sex(self, owner_id, atrrb='sex', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        get_sex = response.json()
        for sex in get_sex['response']:
            res = sex['sex']
            if res == 1:
                result = 'женский'
            elif res == 2:
                result = 'мужской'
        return result


    # Узнаем, есть ли у пользователя фото
    def get_has_photo(self, owner_id, atrrb='has_photo', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        has_photo = response.json()
        for photo in has_photo['response']:
            res = photo['has_photo']
            if res == 1:
                result = 'У пользователя есть фото'
            elif res == 0:
                result = 'У пользователя нет фото'
        return result

    # Получаем данные о музыкальных предпочтениях
    def get_music(self, owner_id, atrrb='music', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        get_music = response.json()
        # Проверяем, есть ли музыкальные предпочтения
        if 'response' not in get_music or not get_music['response']:     
            msg = "Музыкальные предпочтения не указаны" 
            return msg
        user_data = get_music['response'][0]
        if 'city' not in user_data or not user_data['music']:
            msg = "Музыкальные предпочтения не указаны" 
            return msg
        return user_data['music']

    # Узнаем, закрыт ли профиль пользователя
    def get_is_closed(self, owner_id, atrrb='is_closed', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        is_closed = response.json()
        for closed in is_closed['response']:
            res = closed['is_closed']
            if res == False:
                result = 'У пользователя открытый профиль'
            elif res == True:
                result = 'У пользователя закрытый профиль'
        return result

    # Получаем данные о семейном положении
    def get_relation(self, owner_id, atrrb='relation', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        response = requests.get(url, params=params)
        get_relation = response.json()
        # Проверяем, есть ли данные о семейном положении
        
        if 'response' not in get_relation or not get_relation['response']:     
            msg = "Статус отношений не задан" 
            return msg
        user_data = get_relation['response'][0]
        if 'relation' not in user_data or not user_data['relation']:
            msg = "Статус отношений не задан" 
            return msg
        else:
            relation_code = user_data['relation']
            relation_map = {
            0: "Статус отношений не задан",
            1: "Не женат/Не замужем",
            2: "Есть друг/подруга",
            3: "Помолвлен(-а)",
            4: "Женат/Замужем",
            5: "Всё сложно",
            6: "В активном поиске",
            7: "Влюблён(-а)",
            8: "В гражданском браке"}
        return relation_map.get(relation_code, "Статус отношений не задан" )

    # Получаем университет пользователя
    def get_univer(self, owner_id, atrrb='universities', metod='users.get'):
        url = self.base + metod
        params = {
            'user_ids': owner_id,
            'fields': atrrb,
            }
        params.update(self.params)
        try:
            response = requests.get(url, params=params)
            data = response.json()
        
            if not data.get('response'):
                return "Нет данных"  # Всегда возвращаем строку
        
            user_data = data['response'][0]
        
            if not user_data.get('universities'):
                return "Университет не указан"
        
            # Получаем первый университет с проверкой названия
            first_university = user_data['universities'][0].get('name')
            if first_university:
                return first_university if first_university else "Университет не указан"    
        except Exception:
            return "Ошибка запроса"  # Всегда возвращаем строку
    
        
if __name__ == '__main__':
    vk_user = VK(vk_token)
    #user_id = ''
    #get_relation = vk_user.get_relation(user_id)
    #print(get_relation)
    



