from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTableWidgetItem
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PIL import Image, ImageDraw
import sys
import keyboard
import random
import copy
import datetime
import threading

#random.seed(8)


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(519, 655)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(110, 10, 300, 600))
        self.label.setStyleSheet("")
        self.label.setText("")
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 200, 101, 16))
        self.label_2.setStyleSheet("font: 75 11pt \"Century Gothic\";")
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 160, 101, 16))
        self.label_3.setStyleSheet("font: 75 11pt \"Century Gothic\";\n"
"")
        self.label_3.setObjectName("label_3")
        self.timer = QTimer(Dialog)
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "TETRIS"))
        self.label_2.setText(_translate("Dialog", "Линии: 0"))
        self.label_3.setText(_translate("Dialog", "Очки: 0"))


class Example(QMainWindow, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.score = 0
        self.lines = 0
        self.INTERVAL_FOR_TIMER = 1050
        self.HEIGHT = 600
        self.WIDTH = 300
        self.RID_SQUARED = 30
        self.WHITE, self.GRAY = (255, 255, 255), (127, 118, 121)
        self.lock = threading.Lock()
        self.random_num = 0

        self.matrix = [[['-', None] for _ in range(self.WIDTH // self.RID_SQUARED)] for _ in
                       range(self.HEIGHT // self.RID_SQUARED)]
        self.COLOURS = {0: (255, 255, 51),
                        1: (31, 174, 233),
                        2: (186, 85, 211),
                        3: (0, 0, 194),
                        4: (255, 160, 0),
                        5: (43, 181, 43),
                        6: (255, 78, 51)}
        self.figures_in_the_matrix = [[[[0, 0], [1, 0], [0, 1], [1, 1]], [4, -1]],
                                      [[[-2, 0], [-1, 0], [0, 0], [1, 0]], [5, 0]],
                                      [[[0, -1], [-1, 0], [0, 0], [1, 0]], [4, 0]],
                                      [[[1, -1], [1, 0], [0, 0], [-1, 0]], [4, 0]],
                                      [[[-1, -1], [-1, 0], [0, 0], [1, 0]], [4, 0]],
                                      [[[-1, 1], [0, 1], [0, 0], [1, 0]], [4, -1]],
                                      [[[-1, 0], [0, 0], [0, 1], [1, 1]], [4, -1]]]
        self.matrix_canvas = {}
        for x in range(self.WIDTH // self.RID_SQUARED):
            for y in range(self.HEIGHT // self.RID_SQUARED):
                self.matrix_canvas[x, y] = [[(x * self.RID_SQUARED, y * self.RID_SQUARED), (
                (x + 1) * self.RID_SQUARED, (y + 1) * self.RID_SQUARED)], None]
        # pprint.pprint(self.matrix_canvas)
        self.bell, self.random_num, self.matrix_for_this_figure, self.new_figure, \
        self.coords_of_figure, self.bias = None, None, None, None, None, None
        self.new_canvas()
        self.random_figure()
        self.timer.start(self.INTERVAL_FOR_TIMER)
        self.initUI()

    def initUI(self):
        self.timer.timeout.connect(self.move_down)

    def new_canvas(self):
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=self.WHITE)
        draw = ImageDraw.Draw(image)
        image.save('main_canvas.jpg')
        for i in range(self.HEIGHT // self.RID_SQUARED):
            draw.line((0, self.RID_SQUARED + (self.RID_SQUARED * i), self.WIDTH,
                       self.RID_SQUARED + (self.RID_SQUARED * i)), fill=self.GRAY)
        for j in range(self.WIDTH // self.RID_SQUARED):
            draw.line((self.RID_SQUARED + (self.RID_SQUARED * j), 0,
                       (self.RID_SQUARED + (self.RID_SQUARED * j), self.HEIGHT)), fill=self.GRAY)
        image.save('main_canvas.jpg')
        image.save('canvas_with_figures.jpg')
        pixmap = QPixmap('main_canvas.jpg')
        self.label.setPixmap(pixmap)

    def random_figure(self):
        self.INTERVAL_FOR_TIMER = 650
        new_random_num = random.randint(0, 6)
        while new_random_num == self.random_num:
            new_random_num = random.randint(0, 6)
        self.random_num = new_random_num
        self.coords_of_figure = copy.deepcopy(self.figures_in_the_matrix[self.random_num][0])
        self.bias = [self.figures_in_the_matrix[self.random_num][1][0],
                     self.figures_in_the_matrix[self.random_num][1][1]]
        self.bias[1] += 1
        if not self.check_figure(self.coords_of_figure, self.bias):
            self.game_over()
        else:
            self.draw_image()

    def check_figure(self, figure, bias):
        for coord in figure:
            x, y = coord[0] + bias[0], coord[1] + bias[1]
            if not (0 <= x < len(self.matrix[0]) and 0 <= y < len(self.matrix)):
                #print('boundary', x, y, len(self.matrix), len(self.matrix[0]))
                return False
            if self.matrix[y][x][0] != '-':
                #print('matrix', x, y, self.matrix[y][x])
                return False
        return True

    def rotate_figure(self):
        global stopper
        if not stopper:
            new_figure = [(-y, x) for x, y in self.coords_of_figure]
            if self.check_figure(new_figure, self.bias):
                self.coords_of_figure = new_figure
                self.draw_image()

    def move_left(self):
        global stopper
        if not stopper:
            new_bias = [self.bias[0] - 1, self.bias[1]]
            if self.check_figure(self.coords_of_figure, new_bias):
                self.bias = new_bias
                self.draw_image()

    def move_right(self):
        global stopper
        if not stopper:
            new_bias = [self.bias[0] + 1, self.bias[1]]
            if self.check_figure(self.coords_of_figure, new_bias):
                self.bias = new_bias
                self.draw_image()

    def move_down(self):
        global stopper
        if not stopper:
            new_bias = [self.bias[0], self.bias[1] + 1]
            if self.check_figure(self.coords_of_figure, new_bias):
                self.bias = new_bias
                self.draw_image()
            else:
                #print("can't move down")
                for coord in self.coords_of_figure:
                    x, y = coord[0] + self.bias[0], coord[1] + self.bias[1]
                    self.matrix[y][x] = ['X', self.COLOURS[self.random_num]]
                self.coords_of_figure = []
                self.delete_line()
                self.random_figure()

    def game_over(self):
        global pause
        global stopper
        stopper = True
        pause.show()
        pause.game_end_window()

    def delete_line(self):
        lines = 0
        for num, line in enumerate(self.matrix):
            bell = True
            for element in line:
                if element[0] == '-':
                    bell = False
                    break
            if bell:
                lines += 1
                time_matrix = []
                time_matrix.append([['-', None] for _ in range(self.WIDTH // self.RID_SQUARED)])
                for num_1, element_1 in enumerate(self.matrix):
                    if num != num_1:
                        time_matrix.append(element_1)
                self.matrix = copy.deepcopy(time_matrix)
        self.lines += lines
        if lines == 1:
            self.score += 10
        elif lines == 2:
            self.score += 30
        elif lines == 3:
            self.score += 70
        elif lines == 4:
            self.score += 150
        self.label_2.setText('Линии: ' + str(self.lines))
        self.label_3.setText('Очки: ' + str(self.score))
        self.draw_image()

    def draw_image(self):
        image = Image.open('main_canvas.jpg')
        draw = ImageDraw.Draw(image)
        for y, line in enumerate(self.matrix):
            for x, element in enumerate(line):
                if element[1] is not None:
                    draw.rectangle(self.matrix_canvas[x, y][0], fill=element[1])
        for coord in self.coords_of_figure:
            x, y = coord[0] + self.bias[0], coord[1] + self.bias[1]
            draw.rectangle(self.matrix_canvas[x, y][0], fill=self.COLOURS[self.random_num])
        image.save('canvas_with_figures.jpg')
        pixmap = QPixmap('canvas_with_figures.jpg')
        self.label.setPixmap(pixmap)

    def run(self):
        global pause
        global stopper
        stopper = True
        pause.show()

    def new_game(self, value_end):
        global ALL_COUNTS
        global stopper
        stopper = False
        if value_end:
            if self.score != 0:
                ALL_COUNTS += f'{self.score};{self.lines};{datetime.datetime.now()}\n'
        with open('table just in case.txt', 'w') as f:
            f.write(ALL_COUNTS)
        self.score = 0
        self.lines = 0
        self.label_2.setText("Линии: 0")
        self.label_3.setText("Очки: 0")
        self.INTERVAL_FOR_TIMER = 1050
        self.HEIGHT = 600
        self.WIDTH = 300
        self.RID_SQUARED = 30
        self.WHITE, self.GRAY = (255, 255, 255), (127, 118, 121)
        self.lock = threading.Lock()
        self.random_num = 0

        self.matrix = [[['-', None] for _ in range(self.WIDTH // self.RID_SQUARED)] for _ in
                       range(self.HEIGHT // self.RID_SQUARED)]
        self.COLOURS = {0: (255, 255, 51),
                        1: (31, 174, 233),
                        2: (186, 85, 211),
                        3: (0, 0, 194),
                        4: (255, 160, 0),
                        5: (51, 255, 51),
                        6: (255, 78, 51)}
        self.figures_in_the_matrix = [[[[0, 0], [1, 0], [0, 1], [1, 1]], [4, -1]],
                                      [[[-2, 0], [-1, 0], [0, 0], [1, 0]], [5, 0]],
                                      [[[0, -1], [-1, 0], [0, 0], [1, 0]], [4, 0]],
                                      [[[1, -1], [1, 0], [0, 0], [-1, 0]], [4, 0]],
                                      [[[-1, -1], [-1, 0], [0, 0], [1, 0]], [4, 0]],
                                      [[[-1, 1], [0, 1], [0, 0], [1, 0]], [4, -1]],
                                      [[[-1, 0], [0, 0], [0, 1], [1, 1]], [4, -1]]]
        self.matrix_canvas = {}
        for x in range(self.WIDTH // self.RID_SQUARED):
            for y in range(self.HEIGHT // self.RID_SQUARED):
                self.matrix_canvas[x, y] = [[(x * self.RID_SQUARED, y * self.RID_SQUARED), (
                    (x + 1) * self.RID_SQUARED, (y + 1) * self.RID_SQUARED)], None]
        # pprint.pprint(self.matrix_canvas)
        self.bell, self.random_num, self.matrix_for_this_figure, self.new_figure, \
        self.coords_of_figure, self.bias = None, None, None, None, None, None
        self.new_canvas()
        self.random_figure()

    def get_lines_and_score(self):
        return [self.score, self.lines]


class Ui_Pause(object):
    def setupUi(self, tetris):
        tetris.setObjectName("tetris")
        tetris.resize(224, 365)
        self.label = QtWidgets.QLabel(tetris)
        self.label.setGeometry(QtCore.QRect(200, 10, 300, 600))
        self.label.setText("")
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(tetris)
        self.label_2.setGeometry(QtCore.QRect(20, 10, 201, 41))
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(22)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("color: rgb(48, 45, 93);")
        self.label_2.setObjectName("label_2")
        self.pushButton_2 = QtWidgets.QPushButton(tetris)
        self.pushButton_2.setGeometry(QtCore.QRect(50, 120, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Rockwell")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(tetris)
        self.pushButton_3.setGeometry(QtCore.QRect(50, 170, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Rockwell")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_3.setFont(font)
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton = QtWidgets.QPushButton(tetris)
        self.pushButton.setGeometry(QtCore.QRect(50, 70, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Rockwell")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")
        self.checkBox = QtWidgets.QCheckBox(tetris)
        self.checkBox.setGeometry(QtCore.QRect(50, 250, 121, 17))
        font = QtGui.QFont()
        font.setFamily("Rockwell")
        font.setPointSize(9)
        self.checkBox.setFont(font)
        self.checkBox.setObjectName("checkBox")
        self.horizontalSlider = QtWidgets.QSlider(tetris)
        self.horizontalSlider.setGeometry(QtCore.QRect(40, 280, 141, 16))
        self.horizontalSlider.setStyleSheet("")
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setProperty("value", 100)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.label_3 = QtWidgets.QLabel(tetris)
        self.label_3.setGeometry(QtCore.QRect(50, 70, 161, 16))
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.label_3.setFont(font)
        self.label_3.setStyleSheet("")
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(tetris)
        self.label_4.setGeometry(QtCore.QRect(50, 90, 121, 16))
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setStyleSheet("color: rgb(255, 85, 0);")
        self.label_4.setObjectName("label_4")
        self.pushButton_4 = QtWidgets.QPushButton(tetris)
        self.pushButton_4.setGeometry(QtCore.QRect(50, 310, 111, 23))
        self.pushButton_4.setStyleSheet("color: rgb(173, 176, 182);")
        self.pushButton_4.setObjectName("pushButton_4")
        self.label_2.setGeometry(QtCore.QRect(60, 10, 101, 41))

        self.retranslateUi(tetris)
        QtCore.QMetaObject.connectSlotsByName(tetris)

    def retranslateUi(self, tetris):
        _translate = QtCore.QCoreApplication.translate
        tetris.setWindowTitle(_translate("tetris", "  "))
        self.label_2.setText(_translate("tetris", "ПАУЗА"))
        self.pushButton_2.setText(_translate("tetris", "НАЧАТЬ ЗАНОВО"))
        self.pushButton_3.setText(_translate("tetris", "ВЫЙТИ"))
        self.pushButton.setText(_translate("tetris", "ПРОДОЛЖИТЬ"))
        self.checkBox.setText(_translate("tetris", "Включить музыку"))
        self.label_3.setText(_translate("tetris", "Ваш счёт:"))
        self.label_4.setText(_translate("tetris", "НОВЫЙ РЕКОРД!"))
        self.pushButton_4.setText(_translate("tetris", "Таблица рекордов"))


class Pause(QWidget, Ui_Pause):
    def __init__(self):
        super().__init__()
        self.value_end = False
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        self.checkBox.setChecked(True)
        self.label_3.hide()
        self.label_4.hide()
        self.bell = False
        self.media = QtCore.QUrl.fromLocalFile('music_for_tetris.mp3')
        self.content = QMediaContent(self.media)
        self.player = QMediaPlayer()
        self.player.setMedia(self.content)
        self.records_window = None
        self.player.play()
        self.change_value(100)
        self.main()

    def main(self):
        self.pushButton.clicked.connect(self.hide_program)
        self.pushButton_2.clicked.connect(self.new_game)
        self.pushButton_3.clicked.connect(self.close_the_program)
        self.checkBox.stateChanged.connect(self.play_music)
        self.player.stateChanged.connect(self.play_music)
        self.horizontalSlider.valueChanged[int].connect(self.change_value)
        self.pushButton_4.clicked.connect(self.records)

    def play_music(self):
        if self.checkBox.isChecked():
            if self.player.State() == 0:
                self.player.play()
        else:
            self.player.stop()

    def hide_program(self):
        global pause
        global stopper
        self.pushButton.show()
        self.label_2.setText('ПАУЗА')
        self.label_3.hide()
        self.label_4.hide()
        self.label_2.setGeometry(QtCore.QRect(60, 10, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(21)
        self.label_2.setFont(font)
        stopper = False
        self.value_end = False
        pause.hide()

    def new_game(self):
        global ex
        ex.new_game(self.value_end)
        self.hide_program()
        return

    def close_the_program(self):
        global ex
        global ALL_COUNTS
        global my_file
        score, line = ex.get_lines_and_score()
        if line != 0:
            ALL_COUNTS += f'{score};{line};{datetime.datetime.now()}\n'
        with open('table just in case.txt', 'w') as f:
            f.write(ALL_COUNTS)
        my_file.write(ALL_COUNTS)
        my_file.close()
        print('Выход')
        exit(0)

    def game_end_window(self):
        global ex
        global ALL_COUNTS
        self.value_end = True
        self.pushButton.hide()
        self.label_2.setGeometry(10, 10, 201, 41)
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(18)
        self.label_2.setFont(font)
        self.label_2.setText('ВЫ ПРОИГРАЛИ!')
        self.label_3.show()
        score, lines = ex.get_lines_and_score()
        self.label_3.setText(f'Ваш счёт: {score}')

    def change_value(self, value):
        self.player.setVolume(value)

    def records(self):
        self.records_window = Records()
        self.records_window.show()


class Ui_Records(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(493, 300)
        self.tableWidget = QtWidgets.QTableWidget(Dialog)
        self.tableWidget.setEnabled(True)
        self.tableWidget.setGeometry(QtCore.QRect(50, 80, 411, 192))
        self.tableWidget.setAutoScrollMargin(13)
        self.tableWidget.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.tableWidget.setTextElideMode(QtCore.Qt.ElideMiddle)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(9)
        item.setFont(font)
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(9)
        item.setFont(font)
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Century Gothic")
        font.setPointSize(9)
        item.setFont(font)
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(220, 30, 101, 16))
        self.label.setStyleSheet("font: 12pt \"Century Gothic\";")
        self.label.setObjectName("label")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "RECORDS"))
        self.tableWidget.setSortingEnabled(False)
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "Счет"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "Линии"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Dialog", "Дата"))
        self.label.setText(_translate("Dialog", "РЕКОРДЫ"))


class Records(QWidget, Ui_Records):
    def __init__(self):
        global ALL_COUNTS
        super().__init__()
        self.setupUi(self)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setColumnWidth(2, 205)
        if len(ALL_COUNTS) != 0:
            all_lines = ALL_COUNTS.split('\n')[:-1]
            all_lines.sort(key=lambda x: int(x.split(';')[0]))
            all_lines = reversed(all_lines)
            for num, line in enumerate(all_lines):
                rowPosition = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowPosition)
                for num_1, item in enumerate(line.split(';')):
                    self.tableWidget.setItem(rowPosition, num_1, QTableWidgetItem(item))


if __name__ == '__main__':
    try:
        with open('high_score_table.txt', 'r') as f:
            ALL_COUNTS = f.read()
        my_file = open("high_score_table.txt", "w")
    except FileNotFoundError:
        my_file = open("high_score_table.txt", "w")
        with open('high_score_table.txt', 'r') as f:
            ALL_COUNTS = f.read()
        with open('table just in case.txt', 'w') as f:
            f.write('')
    with open('table just in case.txt', 'r') as f:
        text = f.read()
    if text != ALL_COUNTS:
        ALL_COUNTS = text
    stopper = False
    app = QApplication(sys.argv)
    pause = Pause()
    pause.show()
    pause.hide()
    ex = Example()
    ex.show()
    keyboard.add_hotkey('Right', ex.move_right)
    keyboard.add_hotkey('Left', ex.move_left)
    keyboard.add_hotkey('Down', ex.move_down)
    keyboard.add_hotkey('Up', ex.rotate_figure)
    keyboard.add_hotkey('Esc', ex.run)
    sys.exit(app.exec())