import sqlite3
import datetime
import os
import random
import pandas as pd

import openpyxl

import sys
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import hashlib

from threading import Timer

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QFont

from translatepy.translators.yandex import YandexTranslate

translator = YandexTranslate()

import requests
import asyncio
import winsdk.windows.devices.geolocation as wdg

from statsmodels.tsa.seasonal import seasonal_decompose

def mid(x):
    return x.sum() / len(x)

def disp(x):
    return mid(x**2) - (mid(x))**2

async def getCoords():
    locator = wdg.Geolocator()
    pos = await locator.get_geoposition_async()
    return pos.coordinate.latitude, pos.coordinate.longitude

def getloc():
    try:
        return asyncio.run(getCoords())
    except PermissionError:
        return 0


def weather_request(lat, lon):
    with open('API_KEY_WEATHER.txt') as f:
        key = f.readline()
    url = 'https://api.openweathermap.org/data/2.5/weather'
    getparams = {
        'lat': lat,
        'lon': lon,
        'appid': key,
        'units': 'metric'
    }
    response = requests.get(url=url, params=getparams)
    data = response.json()
    return data

def getplace(lat, lon):
    url = 'https://nominatim.openstreetmap.org/reverse?lat={}&lon={}&format=json&addressdetails=1'.format(str(lat) + '0' * random.randint(1, 20), str(lon) + '0' * random.randint(1, 20))
    response = requests.get(url=url)
    data = response.json()
    if not data:
        return 0
    return data


def translate(word):
    return translator.translate(word, 'ru')



class NoteWindow(QDialog):
    def __init__(self, cur_weather, old_weather):
        super().__init__()
        uic.loadUi('Уведомление.ui', self)
        self.weather_text.setText('Погодные условия изменились\n\nПредыдущие погодные условия: {}\n\nТекущие погодные условия: {}'.format(old_weather, cur_weather))
        self.buttonBox.clicked.connect(self.close)

    def close(self):
        self.hide()

class ErrorWindow(QDialog):
    def __init__(self, error):
        super().__init__()
        uic.loadUi('Ошибка.ui', self)
        x = list(error.split())
        self.error_text.setText(str(' '.join(x[:len(x) // 3:])) + '\n' + str(' '.join(x[len(x) // 3:2 * len(x) // 3:])) + '\n' + str(' '.join(x[2 * len(x) // 3::])))
        self.buttonBox.clicked.connect(self.close)

    def close(self):
        self.hide()

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
            result = cur.execute(
                f""" Select login, key, salt from Acc where Acc.login = '{introduced_login}'""").fetchall()
            for elem in result:
                try:
                    self.open_menu = MainWindow([elem[0], elem[1], elem[2]])
                    self.open_menu.show()
                    self.hide()
                except Exception as e:
                    self.err = ErrorWindow(str(e))
                    self.err.show()

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
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password_acc.encode('utf-8'), salt, 100000)
        try:
            if login_acc != '' and password_acc != '' and self.password_2.text() != '':
                if self.password.text() == self.password_2.text():
                    if self.password_verification(password_acc) == 0:
                        con = sqlite3.connect("аккаунты.db")
                        cursor = con.cursor()
                        try:
                            cursor.execute("INSERT INTO Acc(login, key, salt) VALUES(?, ?, ?)",(login_acc, key, salt))
                            con.commit()
                            cursor.close()
                            con.close()
                            self.back_to_login()
                        except Exception as e:
                            if str(e) != 'UNIQUE constraint failed: Acc.login':
                                self.err = ErrorWindow(str(e))
                                self.err.show()
                            else:
                                self.error_message.setText('Логин уже существует')
                        con.close()
                    else:
                        self.error_message.setText(password_errors[self.password_verification(password_acc)])
                else:
                    self.error_message.setText('Пароли не совпадают')
            else:
                self.error_message.setText('Не все поля заполнены')
        except Exception as e:
            self.err = ErrorWindow(str(e))
            self.err.show()


class MplCanvasForecast(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes_temp = fig.add_subplot(211)
        self.axes_wind = fig.add_subplot(212)
        fig.subplots_adjust(top=0.917, bottom=0.145,
                            left=0.063, right=0.983,
                            hspace=0.673, wspace=0.2)
        super(MplCanvasForecast, self).__init__(fig)

class MplCanvasReview(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes_1 = fig.add_subplot(111)
        fig.subplots_adjust(top=0.909, bottom=0.16,
                            left=0.098, right=0.983,
                            hspace=0.624, wspace=0.2)
        super(MplCanvasReview, self).__init__(fig)


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
            if self.account[0] != introduced_login:
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
        self.file_path = '/'
        self.trend = 0
        self.count = 0
        self.plot_type = 'plot'
        self.old_weather = ''
        self.browse.clicked.connect(self.browsefiles)
        self.delete_acc.clicked.connect(self.acc_del)
        self.logout_button.clicked.connect(self.logout)
        self.exit_button.clicked.connect(self.exit_fnc)
        self.filetype = 'CSV'
        self.CSV_type.toggled.connect(self.CSV)
        self.XLSX_type.toggled.connect(self.XLSX)
        self.plot.toggled.connect(self.plot_tog)
        self.hist.toggled.connect(self.hist_tog)
        self.make_forecast.clicked.connect(self.do_forecast)
        self.make_review.clicked.connect(self.do_review)

        self.opened_files = ['Открытые файлы:']
        self.opened_files_review = ['---']
        self.opened_files_data = {}
        self.opened_reviews = ['Удаление:']
        self.view_files.addItems(self.opened_files)
        self.review_files.addItems(self.opened_files_review)
        self.review_del.addItems(self.opened_reviews)

        self.view_files.textActivated.connect(self.rem_file)
        self.review_files.textActivated.connect(self.activate_file)
        self.review_del.textActivated.connect(self.rem_review)

        try:
            self.get_weather()
        except Exception as e:
            self.err = ErrorWindow(str(e))
            self.err.show()

        self.update_weather.clicked.connect(self.get_weather)
        self.trend_show.stateChanged.connect(self.trend_changed)

    def trend_changed(self):
        self.trend = self.trend_show.checkState()

    def activate_file(self):
        self.review_col.clear()
        self.review_date.clear()

        if self.review_files.currentText() != '---':
            file = self.review_files.currentText()
            self.review_col.addItems(self.opened_files_data[file]['cols'])
            self.review_date.addItems(self.opened_files_data[file]['cols'])

    def rem_review(self):
        if self.review_del.currentText() != 'Удаление:':
            self.opened_reviews.remove(self.review_del.currentText())
            self.vis_tabs.removeTab(self.review_del.currentIndex())
            self.count += 1

        self.review_del.clear()
        self.review_del.addItems(self.opened_reviews)
        self.review_del.setCurrentIndex(0)


    def rem_file(self):
        self.review_col.clear()
        self.review_date.clear()
        if self.view_files.currentText() in self.opened_files and self.view_files.currentText() != 'Открытые файлы:':
            self.opened_files.remove(self.view_files.currentText())
            self.opened_files_data.pop(self.view_files.currentText()[:-12])
            self.opened_files_review = ['---']
            for i in range(1, len(self.opened_files), 1):
                self.opened_files_review.append(self.opened_files[i][:-12])

        self.view_files.clear()
        self.view_files.addItems(self.opened_files)
        self.view_files.setCurrentIndex(0)

        self.review_files.clear()
        self.review_files.addItems(self.opened_files_review)
        self.review_files.setCurrentIndex(0)

    def add_file(self):
        try:
            added_file = str(self.file_path.split('/')[-1])
            if added_file and not (added_file + ' - (Удалить)') in self.opened_files:
                self.opened_files_review.append(added_file)
                self.opened_files.append(added_file + ' - (Удалить)')
                if added_file[-3::].upper() == 'CSV':
                    self.opened_files_data[added_file] = {
                        'path': self.file_path,
                        'cols': list(pd.read_csv(self.file_path).columns)
                    }
                elif added_file[-4::].upper() == 'XLSX':
                    self.opened_files_data[added_file] = {
                        'path': self.file_path,
                        'cols': list(pd.read_excel(self.file_path).columns)
                    }

            self.view_files.clear()
            self.view_files.addItems(self.opened_files)

            index = self.review_files.currentIndex()
            self.review_files.clear()
            self.review_files.addItems(self.opened_files_review)
            self.review_files.setCurrentIndex(index)
        except Exception as e:
            self.err = ErrorWindow(str(e))
            self.err.show()


    def do_forecast(self):
        try:
            for i in reversed(range(self.vis.count())):
                self.vis.itemAt(i).widget().deleteLater()
            date_begin = self.forecast_begin.dateTime().toPyDateTime().date()
            date_finish = self.forecast_finish.dateTime().toPyDateTime().date()

            df = pd.read_csv('Forecast.csv')
            df.set_index('date', inplace=True)

            table_temp = df['temperature'][(str(date_begin)):(str(date_finish))]
            list_table_temp = table_temp.tolist()
            table_temp = table_temp.astype(float)
            table_temp_index = list(map(datetime.datetime.fromisoformat, table_temp.index.tolist()))

            table_wind = df['wind'][(str(date_begin)):(str(date_finish))]
            list_table_wind = table_wind.tolist()
            table_wind = table_temp.astype(float)
            table_wind_index = list(map(datetime.datetime.fromisoformat, table_wind.index.tolist()))

            self.draw_plot_forecast([table_temp_index, table_wind_index], [list_table_temp, list_table_wind],
                                    ['axes_temp', 'axes_wind'])

        except Exception as e:
            self.err = ErrorWindow(str(e))
            self.err.show()



    def do_review(self):
        try:
            file = self.review_files.currentText()
            if file != '---':
                file_path = self.opened_files_data[file]['path']
                if file[-3::].upper() == 'CSV':
                    df = pd.read_csv(file_path)
                elif file[-4::].upper() == 'XLSX':
                    df = pd.read_excel(file_path)
                else:
                    return
                col = self.review_col.currentText()
                date_begin = self.review_begin.dateTime().toPyDateTime().date()
                date_finish = self.review_finish.dateTime().toPyDateTime().date()

                df.set_index(str(self.review_date.currentText()), inplace=True)

                table = df[col][(str(date_begin)):(str(date_finish))]

                list_table = table.tolist()
                table = table.astype(float)

                dates_str = list(map(str, table.index.tolist()))
                index = list(map(datetime.datetime.fromisoformat, dates_str))

                table = pd.Series(list_table, index=index)
                if self.trend:
                    decompose = seasonal_decompose(table).trend
                    list_decompose = decompose.tolist()

                self.stats_text = 'Среднее: ' + str(round(mid(table), 3)) + ' Медиана: ' + str(round(table.median(), 3)) + ' Стандартное отклонение: ' + str(round(disp(table), 3))

                if self.trend:
                    self.draw_plot_review(index, list_table, decompose.index, list_decompose)
                else:
                    self.draw_plot_review(index, list_table, 0, 0)

                self.review_del.clear()
                self.opened_reviews.append('id:' + str(len(self.opened_reviews) - 1 + self.count) + ' ' + str(self.review_files.currentText() + ' ' + self.review_col.currentText()) + ' - (Удалить)')
                self.review_del.addItems(self.opened_reviews)

        except Exception as e:
            self.err = ErrorWindow(str(e))
            self.err.show()


    def XLSX(self):
        self.filetype = 'XLSX'

    def CSV(self):
        self.filetype = 'CSV'

    def plot_tog(self):
        self.plot_type = 'plot'

    def hist_tog(self):
        self.plot_type = 'hist'

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
        self.file_path = fname[0]
        self.add_file()

    def draw_plot_review(self, date_index, data, dec_index, dec_data):
        sc = MplCanvasReview(self, width=20, height=1, dpi=100)
        if self.plot_type == 'plot':
            sc.axes_1.plot(date_index, data, marker="o")
        else:
            sc.axes_1.bar(date_index, data)
        if self.trend:
            sc.axes_1.plot(dec_index, dec_data, color='orange')
        sc.axes_1.set_ylim((min(data) - 1, max(data) + 1))
        sc.axes_1.set_xticks(sc.axes_1.get_xticks(), sc.axes_1.get_xticklabels(), rotation=20, ha="right")
        sc.axes_1.set_title('Анализ - ' + str(self.review_col.currentText()))
        for j in range(0, len(date_index), round(len(date_index) / 35) + 1):
            sc.axes_1.annotate(round(data[j], 1), (date_index[j], data[j] + 0.4))

        layout = QVBoxLayout()
        toolbar = NavigationToolbar(sc, self)
        infobar = QLabel()
        infobar.setText(self.stats_text)
        infobar.setFont(QFont('MS Shell Dlg 2', 12))
        infobar.setFixedSize(1000, 35)

        layout.addWidget(infobar)
        layout.addWidget(toolbar)
        layout.addWidget(sc)

        tab = QWidget()
        tab.setLayout(layout)
        self.vis_tabs.addTab(tab, 'id:' + str(len(self.opened_reviews) - 1 + self.count) + ' ' + str(self.review_files.currentText() + ' ' + self.review_col.currentText()))


    def draw_plot_forecast(self, date_index, data, axes):
        sc = MplCanvasForecast(self, width=20, height=1, dpi=100)
        n = len(axes)
        for i in range(n):
            exec('sc.{}.plot(date_index[i], data[i], marker="o")'.format(axes[i]))
            exec('sc.{}.set_ylim((min(data[i]) - 1, max(data[i]) + 1))'.format(axes[i]))
            exec('sc.{}.set_xticks(sc.{}.get_xticks(), sc.{}.get_xticklabels(), rotation=20, ha="right")'.format(axes[i], axes[i], axes[i]))
            exec('sc.{}.set_title("{}")'.format(axes[i], axes[i][5::]))
            for j in range(0, len(date_index[0]), round(len(date_index[0]) / 35) + 1):
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
        StyleSheet = 'QStackedWidget{background-image: url(./weather-photos/background/' + weather_image[
            weather] + '); background-repeat: no-repeat; background-position: center; border-radius: 10%;}'
        self.background_1.setStyleSheet(StyleSheet)
        self.background_2.setStyleSheet(StyleSheet)
        self.background_3.setStyleSheet(StyleSheet)
        self.background_4.setStyleSheet(StyleSheet)
        self.background_5.setStyleSheet(StyleSheet)
        self.cur_weather = str(translate(weather)).replace('Четкий', 'Ясно').replace('Облака', 'Облачно').replace('Моросить','Морось')
        if self.cur_weather != self.old_weather and self.old_weather != ' ':
            self.Note = NoteWindow(self.cur_weather, self.old_weather)
            self.Note.show()
        self.old_weather = self.cur_weather
        self.weather_label.setText(self.cur_weather)

    def get_weather(self):
        self.lat, self.lon = getloc()
        self.data = weather_request(self.lat, self.lon)
        self.draw_weather()

    def date_format(self):
        now = datetime.datetime.now()
        date = '{:02d}:{:02d}:{:02d} {:02d}.{:02d}.{:04d}'.format(now.hour, now.minute, now.second, now.day, now.month,
                                                                  now.year)
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

        self.loc = getplace(self.lat, self.lon)

        if self.loc:
            if self.loc['address']:
                self.label_geo.setText(str('Текущая локация:\n' + self.loc['address']['city'] + ', ' + self.loc['address']['suburb'] + '\n' + self.loc['address']['road']))
            else:
                self.label_geo.setText(str('Текущая локация:\n' + self.loc[2] + ', \n' + self.loc[3]))
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
