import csv
import random
import sqlite3
import sys
import time
from threading import Timer

import pymorphy2
from PyQt5 import uic
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Начальный Экран.ui', self)
        self.mistakes.hide()
        self.going.clicked.connect(self.allowance)
        self.registrationbutton.clicked.connect(self.register)

    def allowance(self):
        introduced_password = self.input_password.text()
        introduced_login = self.input_login.text()
        con = sqlite3.connect("аккаунты.db")
        cur = con.cursor()
        result = cur.execute(
            f""" Select money, login from Acc where Acc.login = '{introduced_login}'
            and Acc.password='{introduced_password}'""").fetchall()
        if result:
            for elem in result:
                self.open_game = Open_Game(elem[0], elem[1])
                self.open_game.show()
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
        uic.loadUi('регистрация.ui', self)
        self.registration.clicked.connect(self.register_an_account)
        self.license_agreement.clicked.connect(self.license_agreement_open)

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
            1: 'в пароле должны содержаться цифры',
            2: 'пароль должен сосотоять из более чем 8 символов',
            3: 'в пароле должны содержаться буквы',
            4: 'в пароле должны содержаться большие и маленькие буквы',
            5: 'слишком простой пароль'
        }
        login_acc = self.login.text()
        password_acc = self.password.text()
        if login_acc != '' and password_acc != '' and self.password_2.text() != '':
            if self.statement.isChecked():
                if self.password.text() == self.password_2.text():
                    if self.password_verification(password_acc) == 0:
                        con = sqlite3.connect("аккаунты.db")
                        cursor = con.cursor()
                        cursor.execute("INSERT INTO Acc(login, password) VALUES(?, ?)", (login_acc, password_acc))
                        con.commit()
                        cursor.close()
                        con.close()
                        self.go_home = MainWidget()
                        self.go_home.show()
                        self.hide()
                    else:
                        self.error_message.setText(password_errors[self.password_verification(password_acc)])
                else:
                    self.error_message.setText('пароли не совпадают')
            else:
                self.error_message.setText('вы забыли лицензионное соглашение')
        else:
            self.error_message.setText('не все поля заполнены')

    def license_agreement_open(self):
        self.setWindowTitle('Input dialog')
        self.show()
        text, ok = QInputDialog.getText(self, 'Лицензионное соглашение',
                                        f'Хоть кто то это прочитал, оставте свой отзыв')
        k = open('output.dat', 'w')
        k.write(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec_())

