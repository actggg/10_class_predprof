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


class Open_Game(QMainWindow):
    def __init__(self, *accaunt):
        super().__init__()
        uic.loadUi('казино.ui', self)
        self.LineEdit.setValidator(QIntValidator(0, 2147483647, self))
        self.accaunt = accaunt
        self.balans.setText(str(self.accaunt[0]))
        self.label_52.hide()
        self.label_54.hide()
        self.plainTextEdit.setEnabled(False)
        self.count = 0
        self.count_to_twist = 0
        self.count_to_twist_list = []
        self.toolittel.hide()
        self.rocket_is_flying.hide()
        self.pushButton_2.clicked.connect(self.roulette)
        self.pushButton.clicked.connect(self.twist)
        self.pushButton_3.clicked.connect(self.fly)
        self.win = {'999': 20000, '888': 10000,
                    '777': 5000, '666': 2000,
                    '555': 1000, '444': 500,
                    '333': 300, '222': 150,
                    '111': 50, '123': 5,
                    '234': 5, '345': 5,
                    '456': 5, '567': 5,
                    '678': 5, '789': 5}

    def roulette(self):
        self.roll = Roulette(self.accaunt[1], self.balans.text())
        self.roll.show()
        self.hide()

    def saveStat(self):
        con = sqlite3.connect("аккаунты.db")
        cur = con.cursor()
        cur.execute(f"""UPDATE Acc Set money = {self.balans.text()} Where login = '{self.accaunt[1]}'""")
        con.commit()
        con.close()

    def fly(self):
        self.go = Quiz(self.accaunt[1], self.balans.text())
        self.go.show()
        self.hide()

    def twist(self):
        try:
            self.label_52.hide()
            self.toolittel.setReadOnly(True)
            self.pushButton_3.setEnabled(False)
            self.LineEdit.setEnabled(False)
            self.pushButton.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.label_3.setText('')
            self.count_to_twist += 1
            self.rocket_is_flying.show()
            self.rocket_is_standing.hide()
            self.toolittel.hide()
            self.bet = int(self.LineEdit.text())
            self.count_to_twist_list.append(self.bet)
            if self.bet not in range(1, int(self.balans.text()) + 1):
                self.toolittel.show()
                self.LineEdit.setEnabled(True)
                self.pushButton.setEnabled(True)
                self.pushButton_2.setEnabled(True)
                self.pushButton_3.setEnabled(True)
                return 0
            else:
                self.balans.setText(str(int(self.balans.text()) - self.bet))
            self.twists = 0
            self.digit = '123456789'
        except Exception as e:
            print(e)

        def taskmanager():
            self.saveStat()
            self.count += 3
            self.rocket_is_flying.move(40, 590 - self.count)
            self.twists += 1
            self.slot_1.setText(random.choice(str(self.digit)))
            self.slot_2.setText(random.choice(str(self.digit)))
            self.slot_3.setText(random.choice(str(self.digit)))
            if self.twists <= 10:
                t = Timer(0.05, taskmanager)
                t.start()
            elif self.twists <= 20:
                t = Timer(0.2, taskmanager)
                t.start()
            elif self.twists <= 25:
                t = Timer(0.5, taskmanager)
                t.start()
            else:
                if self.slot_1.text() + self.slot_2.text() + self.slot_3.text() in self.win:
                    self.balans.setText(str(int(self.balans.text()) + int(self.bet) * self.win[
                        self.slot_1.text() + self.slot_2.text() + self.slot_3.text()]))
                    self.label_3.setText(str(int(self.bet) * self.win[
                        self.slot_1.text() + self.slot_2.text() + self.slot_3.text()]))
                    if self.slot_1.text() == self.slot_2.text() and self.slot_1.text() == self.slot_3.text():
                        len_win = len(self.label_3.text())
                        self.label_54.setText(
                            ' ' * ((12 - len_win) // 2) + self.label_3.text() + ' ' * ((12 - len_win) // 2))
                        self.label_52.show()
                        self.label_54.show()
                        time.sleep(2)
                        self.label_52.hide()
                        self.label_54.hide()
                elif self.slot_1.text() + self.slot_2.text() == '11' or self.slot_2.text() + self.slot_3.text() == '11':
                    self.balans.setText(str(int(self.balans.text()) + int(self.bet) * 5))
                    self.label_3.setText(str(int(self.bet) * 5))
                elif self.slot_1.text() == '1' or self.slot_2.text() == '1' or self.slot_3.text() == '1':
                    self.balans.setText(str(int(self.balans.text()) + int(self.bet) * 2))
                    self.label_3.setText(str(int(self.bet) * 2))
                self.LineEdit.setEnabled(True)
                self.pushButton.setEnabled(True)
                self.pushButton_2.setEnabled(True)
                self.pushButton_3.setEnabled(True)
                if self.count_to_twist % 7 == 0:
                    self.balans.setText(str(int(self.balans.text()) + sum(self.count_to_twist_list) // 7))
                    self.rocket_is_flying.move(40, 590)
                    self.count = 0
                    self.rocket_is_flying.hide()
                    self.rocket_is_standing.show()
                self.saveStat()

        taskmanager()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec_())

