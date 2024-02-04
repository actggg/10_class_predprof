import sqlite3
import datetime
import sys
import random
import os
import csv
import pandas as pd

import sys
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import hashlib


from threading import Timer

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog

import pyqtgraph as pg

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

def translate(word):
    return translator.translate(word, 'ru')

class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Начальный Экран(Вход).ui', self)
        self.mistakes.hide()
        self.setBaseSize(760, 500)
        self.going.clicked.connect(self.allowance)
        self.registrationbutton.clicked.connect(self.register)


    def allowance(self):
        introduced_password = self.input_password.text()
        introduced_login = self.input_login.text()
        con = sqlite3.connect("аккаунты.db")
        cur = con.cursor()
        result = cur.execute(f""" Select key, salt from Acc where Acc.login = '{introduced_login}'""").fetchall()
        if result:
            for elem in result:
                key = elem[0]
                salt = elem[1]
        else:
            self.mistakes.show()
            con.close()
            return
        new_key = hashlib.pbkdf2_hmac('sha256', introduced_password.encode('utf-8'), salt, 100000)
        if key == new_key:
            result = cur.execute(f""" Select IP, login, key, salt from Acc where Acc.login = '{introduced_login}'""").fetchall()
            for elem in result:
                try:
                    self.open_menu = MainWindow([elem[0], elem[1], elem[2], elem[3]])
                    self.open_menu.show()
                    self.hide()
                except Exception as e:
                    print(e)
        else:
            self.mistakes.show()
            con.close()
            return
        con.close()


    def register(self):
        self.registration = Registration()
        self.registration.show()
        self.hide()


class Registration(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Регистрация.ui', self)
        self.setBaseSize(760, 500)
        self.registration.clicked.connect(self.register_an_account)
        self.login_page.clicked.connect(self.back_to_login)

    def back_to_login(self):
        self.go_home = MainWidget()
        self.go_home.show()
        self.hide()

    def password_verification(self, password):
        lit_ang_connections = 'qwertyuiopasdfghjklzxcvbnm'
        lit_rus_connections = 'йцукенгшщзхъфывапролджэёячсмитьбю'
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
            2: 'Пароль должен сосотоять\nиз более чем 8 символов',
            3: 'В пароле должны содержаться буквы',
            4: 'В пароле должны содержаться\n большие и маленькие буквы',
            5: 'Слишком простой пароль'
        }
        login_acc = self.login.text()
        password_acc = self.password.text()
        conn = http.client.HTTPConnection("ifconfig.me")
        conn.request("GET", "/ip")
        ip = str(conn.getresponse().read())[2:-1]
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password_acc.encode('utf-8'), salt, 100000)
        try:
            if login_acc != '' and password_acc != '' and self.password_2.text() != '':
                if self.password.text() == self.password_2.text():
                    if self.password_verification(password_acc) == 0:
                        if valid_ip(ip):
                            con = sqlite3.connect("аккаунты.db")
                            cursor = con.cursor()
                            cursor.execute("INSERT INTO Acc(login, key, salt, IP) VALUES(?, ?, ?, ?)", (login_acc, key, salt, ip))
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
        except Exception as e:
            print(e)

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes_temp = fig.add_subplot(211)
        self.axes_wind = fig.add_subplot(212)
        fig.subplots_adjust(top = 0.921, bottom = 0.139,
                            left = 0.069, right = 0.983,
                            hspace = 0.624, wspace = 0.2)
        super(MplCanvas, self).__init__(fig)

class Delete_Acc(QDialog):
    def __init__(self, account):
        super().__init__()
        uic.loadUi('Удаление аккаунта.ui', self)
        self.account = account
        self.delete_acc_final.clicked.connect(self.acc_del_final)
        self.back.clicked.connect(self.exit_fnc)
        self.mistakes.hide()

    def acc_del_final(self):
        introduced_password = self.input_password.text()
        introduced_login = self.input_login.text()
        con = sqlite3.connect("аккаунты.db")
        cur = con.cursor()
        result = cur.execute(f""" Select key, salt from Acc where Acc.login = '{introduced_login}'""").fetchall()
        if result:
            for elem in result:
                key = elem[0]
                salt = elem[1]
        new_key = hashlib.pbkdf2_hmac('sha256', introduced_password.encode('utf-8'), salt, 100000)
        if key != new_key:
            self.mistakes.show()
        else:
            if self.account[1] != introduced_login:
                self.mistakes.show()
            else:
                cur.execute(f""" Delete from Acc where Acc.login = '{introduced_login}'""").fetchall()
                con.commit()
                self.go_home = MainWidget()
                self.go_home.show()
                self.hide()
        con.close()

    def exit_fnc(self):
        self.open_menu = MainWindow(self.account)
        self.open_menu.show()
        self.hide()

class MainWindow(QMainWindow):
    def __init__(self, account):
        super().__init__()
        uic.loadUi('Главный экран(Погода).ui', self)
        self.setBaseSize(760, 500)
        self.account = account
        self.IP = self.account[0]
        self.pathfile = 0
        self.browse.clicked.connect(self.browsefiles)
        self.delete_acc.clicked.connect(self.acc_del)
        self.logout_button.clicked.connect(self.logout)
        self.exit_button.clicked.connect(self.exit_fnc)
        self.filetype = 'CSV'
        self.CSV_type.toggled.connect(self.CSV)
        self.XLSX_type.toggled.connect(self.XLSX)
        self.make_forecast.clicked.connect(self.do_forecast)


        try:
            self.get_weather()
        except Exception as e:
            print(e)

        self.update_weather.clicked.connect(self.get_weather)
        self.update_geo.clicked.connect(self.get_weather_update_geo)

    def do_forecast(self):
        try:
            for i in reversed(range(self.vis.count())):
                self.vis.itemAt(i).widget().deleteLater()
            self.date_begin = self.forecast_begin.dateTime().toPyDateTime().date()
            self.date_finish = self.forecast_finish.dateTime().toPyDateTime().date()

            df = pd.read_csv('Forecast.csv')
            df.set_index('date', inplace=True)

            table_temp = df['temperature'][(str(self.date_begin) + '-00'):(str(self.date_finish) + '-00')]
            list_table_temp = table_temp.tolist()
            table_temp = table_temp.astype(float)
            table_temp.index = pd.to_datetime(table_temp.index, format='%Y-%m-%d-%H')

            table_wind = df['wind'][(str(self.date_begin) + '-00'):(str(self.date_finish) + '-00')]
            list_table_wind = table_wind.tolist()
            table_wind = table_temp.astype(float)
            table_wind.index = pd.to_datetime(table_wind.index, format='%Y-%m-%d-%H')

            self.draw_plot([table_temp.index, table_wind.index], [list_table_temp, list_table_wind], ['axes_temp', 'axes_wind'])

        except Exception as e:
            print(e)
    def XLSX(self):
        self.filetype = 'XLSX'

    def CSV(self):
        self.filetype = 'CSV'

    def acc_del(self):
        self.delete_account = Delete_Acc(self.account)
        self.delete_account.show()
        self.hide()

    def logout(self):
        self.account = []
        self.go_home = MainWidget()
        self.go_home.show()
        self.hide()
    def exit_fnc(self):
        sys.exit(app.exec_())

    def browsefiles(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/', 'Data(*.{})'.format(self.filetype.lower()))
        file = fname[0].split('/')[-1]
        self.pathfile = fname[0]
        self.filename.setText(file)
        self.update_plot()

    def update_plot(self):
        try:
            if self.filetype == 'CSV':
                df = pd.read_csv(self.pathfile)
            elif self.filetype == 'XLSX':
                df = pd.read_excel(self.pathfile)
            else:
                return
            dictionary = {
                'температура': 'temperature',
                'ветер': 'wind',
                'давление': 'pressure',
                'влажность': 'humidity'
            }
            df.set_index('date', inplace=True)
            table = df[dictionary['температура']][str(self.date_begin):str(self.date_finish)]
            list_table = table.tolist()
            table = table.astype(float)
            table.index = pd.to_datetime(table.index)
            self.draw_plot(table.index, list_table)
        except Exception as e:
            print(e)


    def draw_plot(self, date_index, data, axes):
        sc = MplCanvas(self, width=20, height=1, dpi=100)
        n = len(axes)
        for i in range(n):
            exec('sc.{}.plot(date_index[i], data[i], marker="o")'.format(axes[i]))
            exec('sc.{}.set_ylim((min(data[i]) - 1, max(data[i]) + 3))'.format(axes[i]))
            exec('sc.{}.set_xticks(sc.{}.get_xticks(), sc.{}.get_xticklabels(), rotation=20, ha="right")'.format(axes[i], axes[i], axes[i]))
            exec('sc.{}.set_title("{}")'.format(axes[i], axes[i][5::]))
            for j in range(len(date_index[i])):
                exec('sc.{}.annotate(round(data[i][j], 1), (date_index[i][j], data[i][j] + 0.4))'.format(axes[i]))

        toolbar = NavigationToolbar(sc, self)
        self.vis.addWidget(toolbar)
        self.vis.addWidget(sc)

    def set_background(self, weather):
        weather_image = {
            'Clear': 'clear.jpg',
            'Clouds': 'cloudy.png',
            'Snow': 'snow.jpg',
            'Rain': 'rain.jpg',
            'Drizzle': 'drizzle.jpg',
            'Thunderstorm': 'thunder.jpg',
            'Tornado': 'tornado.jpg',
            'Squall': 'squall.jpg',
            'Ash': 'ash.jpg',
        }
        Fog = dict.fromkeys(['Mist', 'Fog', 'Smoke', 'Haze'], 'fog.jpg')
        Dust = dict.fromkeys(['Dust', 'Sand'], 'dust.jpg')
        weather_image = dict(list(weather_image.items()) + list(Fog.items()) + list(Dust.items()))
        StyleSheet = 'QStackedWidget{background-image: url(./weather-photos/background/'+weather_image[weather]+'); background-repeat: no-repeat; background-position: center; border-radius: 10%;}'
        self.background_1.setStyleSheet(StyleSheet)
        self.background_2.setStyleSheet(StyleSheet)
        self.background_3.setStyleSheet(StyleSheet)
        self.background_4.setStyleSheet(StyleSheet)
        self.weather_label.setText(str(translate(weather)).replace('Четкий', 'Ясно').replace('Облака', 'Облачно').replace('Моросить', 'Морось'))


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
        if 337.5 <= deg <= 360 or 0 <= deg <= 22.5:
            return 'С'
        elif 22.5 <= deg <= 67.5:
            return 'СВ'
        elif 67.5 <= deg <= 112.5:
            return 'В'
        elif 112.5 <= deg <= 157.5:
            return 'ЮВ'
        elif 157.5 <= deg <= 202.5:
            return 'Ю'
        elif 202.5 <= deg <= 247.5:
            return 'ЮЗ'
        elif 247.5 <= deg <= 292.5:
            return 'З'
        elif 292.5 <= deg <= 337.5:
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

