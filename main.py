import sqlite3
import datetime
import sys
import random

from threading import Timer

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from geopy.geocoders import Nominatim

import request

from translatepy.translators.yandex import YandexTranslate

translator = YandexTranslate()

import http.client

def valid_ip(IP):
    ip_split = list(map(int, str(IP).split('.')))
    n = len(ip_split)
    if not n == 4:
        return 0
    else:
        for i in range(4):
            if not 0 <= ip_split[i] <= 255:
                return 0
    return 1

def getplace(lat, lon):
    geolocator = Nominatim(user_agent=str(random.randint(10000, 10000000000)))
    location = geolocator.reverse(lat + "," + lon)
    if not location:
        return 0
    return location

def translate_from_en_to_ru(word):
    return translator.translate(word, 'ru')

class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Начальный Экран(Вход).ui', self)
        self.mistakes.hide()
        self.statusBar().hide()
        self.setFixedSize(760, 500)
        self.going.clicked.connect(self.allowance)
        self.registrationbutton.clicked.connect(self.register)

    def allowance(self):
        introduced_password = self.input_password.text()
        introduced_login = self.input_login.text()
        con = sqlite3.connect("аккаунты.db")
        cur = con.cursor()
        result = cur.execute(
            f""" Select IP, login from Acc where Acc.login = '{introduced_login}'
            and Acc.password='{introduced_password}'""").fetchall()
        if result:
            for elem in result:
                self.open_weather = Open_weather([elem[0], elem[1]])
                self.open_weather.show()
                self.hide()
        else:
            self.mistakes.show()
        con.close()


    def register(self):
        self.registration = Registration()
        self.registration.show()
        self.hide()


class Registration(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Регистрация.ui', self)
        self.statusBar().hide()
        self.setFixedSize(760, 500)
        self.registration.clicked.connect(self.register_an_account)
        self.login_page.clicked.connect(self.back_to_login)

    def back_to_login(self):
        self.go_home = MainWidget()
        self.go_home.show()
        self.hide()

    def password_verification(self, password):
        lit_ang_connections = 'qwertyuiop        asdfghjkl      zxcvbnm'
        lit_rus_connections = 'йцукенгшщзхъ     фывапролджэё      ячсмитьбю'
        if list(set(list(password)) & set(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])) == []:
            return 1
        elif len(password) <= 8:
            return 2
        elif password.isdigit():
            return 3
        elif password.isupper() or password.islower():
            return 4
        else:
            mini_password = password.lower()
            for i in lit_ang_connections.split() + lit_rus_connections.split():
                g = len(i) - 2
                for j in range(g):
                    if i[j: j + 3] in mini_password:
                        return 5
        return 0

    def register_an_account(self):
        password_errors = {
            1: 'В пароле должны содержаться цифры',
            2: 'Пароль должен сосотоять из более чем 8 символов',
            3: 'В пароле должны содержаться буквы',
            4: 'В пароле должны содержаться большие и маленькие буквы',
            5: 'Слишком простой пароль'
        }
        login_acc = self.login.text()
        password_acc = self.password.text()
        conn = http.client.HTTPConnection("ifconfig.me")
        conn.request("GET", "/ip")
        ip = str(conn.getresponse().read())[2:-1]

        if login_acc != '' and password_acc != '' and self.password_2.text() != '':
            if self.password.text() == self.password_2.text():
                if self.password_verification(password_acc) == 0:
                    if valid_ip(ip):
                        con = sqlite3.connect("аккаунты.db")
                        cursor = con.cursor()
                        cursor.execute("INSERT INTO Acc(login, password, IP) VALUES(?, ?, ?)", (login_acc, password_acc, ip))
                        con.commit()
                        cursor.close()
                        con.close()
                        self.back_to_login()
                    else:
                        self.error_message.setText('Некорректный IP-адрес')
                else:
                    self.error_message.setText(password_errors[self.password_verification(password_acc)])
            else:
                self.error_message.setText('Пароли не совпадают')
        else:
            self.error_message.setText('Не все поля заполнены')



class Open_weather(QMainWindow):
    def __init__(self, account):
        super().__init__()
        uic.loadUi('Главный экран(Погода).ui', self)
        self.statusBar().hide()
        self.setFixedSize(760, 500)
        self.account = account
        self.IP = self.account[0]

        try:
            self.get_weather()
        except Exception as e:
            print(e)

        self.update_weather.clicked.connect(self.get_weather)
        self.update_geo.clicked.connect(self.get_weather_update_geo)

    def set_background(self, weather):
        if weather == 'Clear':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/clear.jpg')
        elif weather == 'Clouds':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/cloudy.png')
        elif weather == 'Snow':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/snow.jpg')
        elif weather == 'Rain':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/rain.jpg')
        elif weather == 'Drizzle':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/drizzle.png')
        elif weather == 'Thunderstorm':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/thunder.jpg')
        elif weather == 'Mist' or weather == 'Fog' or weather == 'Smoke' or weather == 'Haze':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/fog.jpg')
        elif weather == 'Tornado':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/tornado.jpg')
        elif weather == 'Squall':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/squall.jpg')
        elif weather == 'Ash':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/ash.jpg')
        elif weather == 'Dust' or weather == 'Sand':
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/dust.jpg')
        else:
            pixmap = QPixmap('C:/Users/sasak/PycharmProjects/10_class_predprof/weather-photos/background/clear.jpg')
        self.background.setPixmap(pixmap)


    def get_weather(self):
        self.data = request.weather_request(0, self.IP)
        self.draw_weather()


    def get_weather_update_geo(self):
        self.data = request.weather_request(1, self.IP)
        self.draw_weather()

    def date_format(self):
        now = datetime.datetime.now()
        date = '{:02d}:{:02d}:{:02d} {:02d}.{:02d}.{:04d}'.format(now.hour, now.minute, now.second, now.day, now.month, now.year)
        return date

    def wind_dir_get(self, deg):
        if round(deg / 22.5) == 0 or round(deg / 22.5) == 15:
            return 'С'
        elif round(deg / 45) == 1:
            return 'СВ'
        elif round(deg / 45) == 2:
            return 'В'
        elif round(deg / 45) == 3:
            return 'ЮВ'
        elif round(deg / 45) == 4:
            return 'Ю'
        elif round(deg / 45) == 5:
            return 'ЮЗ'
        elif round(deg / 45) == 6:
            return 'З'
        elif round(deg / 45) == 7:
            return 'СЗ'


    def change_label_update(self):
        self.label_update.setText('Данные актуальны на \n' + self.date_format())

    def draw_weather(self):
        self.label_update.setText('Данные обновлены')
        timer = Timer(3.0, self.change_label_update)
        timer.start()

        self.temp = str(round(self.data['main']['temp'])) + '°'
        self.temp_like = str(round(self.data['main']['feels_like'])) + '°'
        self.hum = str(round(self.data['main']['humidity'])) + '%'
        self.press = str(round(0.750064 * self.data['main']['pressure'])) + '\nмм рт. ст.'
        self.wind_dir = str(self.data['wind']['deg']) + '° ' + self.wind_dir_get(self.data['wind']['deg'])
        self.wind_sp = str(round(self.data['wind']['speed'])) + ' м/c'
        self.clouds = str(round(self.data['clouds']['all'])) + '%'
        self.weather = self.data['weather'][0]['main']

        self.set_background(self.weather)

        with open('Saved_coords.txt') as f:
            self.lat, self.lon = f.read().split()

        self.place = getplace(self.lat, self.lon)
        if self.place != 0:
            self.loc = str(getplace(self.lat, self.lon)[0]).split(', ')
            print(self.loc)
            if len(self.loc) <= 4:
                self.label_geo.setText(str('Текущая локация:\n' + self.loc[0] + ', \n' + self.loc[1]))
            else:
                self.label_geo.setText(str('Текущая локация:\n' + self.loc[3] + ', \n' + self.loc[2]))
        else:
            self.label_geo.setText(str('Текущая локация:\n---\n---'))

        self.wind_direction.setText(self.wind_dir)
        self.wind_speed.setText(self.wind_sp)
        self.temperature.setText(self.temp)
        self.temperature_like.setText(self.temp_like)
        self.humidity.setText(self.hum)
        self.cloudness.setText(self.clouds)
        self.pressure.setText(self.press)




if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        ex = MainWidget()
        ex.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)

