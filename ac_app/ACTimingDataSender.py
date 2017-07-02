# coding=utf-8
import ac
import acsys
import os
import sys
import os.path
import struct
import math
import mmap
import time
import platform
import json
import threading
# import queue

from operator import attrgetter
# FIXME Вывести URL из строки HTTP-заголовка
# Это тупая копия из sim_info, пока не разберусь как следует с импортом
AC_UNKNOWN = -1
AC_PRACTICE = 0
AC_QUALIFY = 1
AC_RACE = 2
AC_HOTLAP = 3
AC_TIME_ATTACK = 4
AC_DRIFT = 5
AC_DRAG = 6

AC_NO_FLAG = 0
AC_BLUE_FLAG = 1
AC_YELLOW_FLAG = 2
AC_BLACK_FLAG = 3
AC_WHITE_FLAG = 4
AC_CHECKERED_FLAG = 5
AC_PENALTY_FLAG = 6

# web-сервер
SERVER_ADDR = "localhost"
SERVER_PORT = 8080
APP_URL = "/ACTiming2/live"

def postLogMessage(msg):
    # Отправка сообщений в лог Assetto Corsa (Documents\Assetto Corsa\logs\py_log.txt)
    ac.log("ACTimingDataSender: " + msg)


# Подключение библиотек
if platform.architecture()[0] == "64bit":
    sysdir = os.path.dirname(__file__) + '/stdlib64'
else:
    sysdir = os.path.dirname(__file__) + '/stdlib'
sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";.;./third_party"

from third_party.sim_info import SimInfo
info = SimInfo()

try:
    import socket
except ImportError as e:
#    import traceback
#    ac.console(str(e))
#    ac.console(traceback.format_exc(e))
#    ac.console("Could not import socket. Maybe you need to copy the correct _socket.pyd into the correct stdlib-dir of this plugin"
    postLogMessage("Cannot import socket")


class HTTPPostThread(threading.Thread):
    """
    Реализует отправку HTTP POST запросов в отдельном потоке, не блокируя игру.
    """
    def __init__(self):
        super().__init__()
        self.data = ""
        # self.queue = queue.Queue()
        self.stop = False

    def put(self, packet):
        self.data = packet

    def start(self):
        #postLogMessage("HTTP sender thread started")
        return super().start()

    def run(self):
        httpconn = None
        # Модуль http отказывается работать в AC по неясным причинам. Пошлём POST руками.
        try:
            httpconn = socket.socket()
            #postLogMessage("Socket created")
            httpconn.connect((SERVER_ADDR, SERVER_PORT))
            #postLogMessage("Connected to web server")
            #postLogMessage("Data:" + self.data)
            httpconn.sendall(bytes(self.data[:], 'UTF-8'))
            #postLogMessage("Send OK")
        except Exception as e:
            postLogMessage("Cannot post data to server" + repr(e))
        finally:
            httpconn.close()

carList = {}
def getCarName(car):
    # return car;
    try:
        if car not in carList:
            fname = os.getcwd() + '\\content\\cars\\' + car + '\\ui\\ui_car.json'
            postLogMessage('opening carinfo file ' + fname)
            f = open(fname)
            postLogMessage('file open OK')
            for line in f:
                postLogMessage('read line ' + line)
                if line.find("name") == -1:
                    continue
                keyval = line.split(':')
                if len(keyval) > 1 and ('name' in keyval[0]):
                    postLogMessage(keyval[1])
                    carName = keyval[1][2:-3]
                    postLogMessage('Got car name ' + carName + ' from JSON')
                    carList[car] = carName
                    f.close()
                    return carName
            f.close()
        carName = carList[car];
        postLogMessage('Got car name ' + carName + ' from dictionary');
        return carName;
    except Exception as ex:
        print(ex)
        postLogMessage("Cannot retrieve car name from ui_car.json");
        return car;

class CarInfo:
    """
    Содержит данные о машине/игроке, занимающем машину.
    """
    # см. acsys.CS.*

    def __init__(self, carId):
        self.carId = carId  # ID - номер машины в списке
        self.driverName = ac.getDriverName(carId)  # имя игрока
        self.carName = getCarName(ac.getCarName(carId))  # машина
        # TODO: брать название машины из конфигов: например, вместо ks_bmw_m235i_racing будет BMW M235i Racing
        self.lapsCompleted = 0  # завершено кругов
        self.lastLap = ac.getCarState(self.carId, acsys.CS.LastLap)  # время последнего пройденного круга в мс
        self.bestLap = ac.getCarState(self.carId, acsys.CS.BestLap)  # время лучшего круга сессии в мс
        self.qualifiedTime = 0  # время, поставленное в квалификации (сохраняется для сортировки пилотов на старте)
        self.totalTime = 0      # суммарное время кругов (время гонки, в остальных сессиях не имеет смысла)
        self.totalDistance = 0  # суммарная дистанция (для сортировки в гонке)
        self.isInPitlane = ac.isCarInPitlane(carId) # машина на пит-лейне
        self.isInPit = ac.isCarInPit(carId) # машина в боксах
        self.lapPostTime = 0    # момент времени (по session_time), когда было поставлено время в практике/квалификации


class Leaderboard:
    """
    Содержит основную информацию о сессии, а также имеет методы для формирования JSON-представления данных.
    """
    MAX_CARS = 36  # обусловлено максимальным количеством мест на Nordschleife Touristenfahrten, где машин больше всего
    FALLBACK_STR = '{"session": -1}'  # JSON-строка, отправляемая при остановке игры

    def __init__(self):
        self.carList = []
        for i in range(0, self.MAX_CARS):
            self.carList.append(None)
        self.session = -1
        self.session_time = 0  # оставшееся время: в гонке начинается с 30 минут и отсчитывает вниз, в том числе и в минус
        self.sessionLapCount = 0
        self.jsonfile = open("leaderboard.json", "w+")
        self.sessionLapCount = 0
        self.slotCount = 0
        self.carsCount = 0
        self.flag = AC_NO_FLAG

    def updateSession(self):
        # Вернёт True, если сессия сменилась. Кроме того, обновляет саму информацию о сессии.
        newSession = info.graphics.session
        newSessionTime = info.graphics.sessionTimeLeft
        isUpdated = False
        if newSession != self.session or newSessionTime > self.session_time:
            isUpdated = True
            self.session = newSession
        self.session_time = newSessionTime
        self.sessionLapCount = info.graphics.numberOfLaps  # число кругов в гонке
        self.flag = info.graphics.flag
        return isUpdated

    def updateCarList(self):
        # Обновляет список машин/пилотов (прежде всего всё-таки пилотов).
        # Игроки могут меняться в ходе сессии. Если игрок вышел, его "забываем"
        # Нового игрока добавляем в список, обнулив пройденную дистанцию
        for carId in range(0, self.MAX_CARS):
            if self.carList[carId] is None:  # если машины не было
                # проверяем её существование в игре, если есть - добавляем
                driverName = str(ac.getDriverName(carId))  # эта странная штука возвращает либо строку, либо число -1
                if driverName != "-1":
                    self.carList[carId] = CarInfo(carId)
            else:  # машина (была) занята, проверим, занята ли она сейчас и кем
                driverName = str(ac.getDriverName(carId))
                if str(driverName) == "-1":  # ушёл
                    self.carList[carId] = None
                elif driverName != self.carList[carId].driverName:  # сменился
                    self.carList[carId] = CarInfo(carId)

    def resetTiming(self, transferTime=False):
        """
        Сбрасывает данные для каждого пилота в начале новой сессии.
        """
        for car in self.carList:
            if car is not None:
                car.totalTime = 0
                car.totalDistance = 0
                car.lapsCompleted = 0
                car.lastLap = 0
                if transferTime:  # Если перешли к гонке, нужно сохранить время с предыдущей сессии (практики или квалификации)
                    car.qualifiedLap = car.bestLap
                    # TODO сохранить время постановки круга в lapPostTime на случай равной квалификации
                    # (такое вполне возможно, как в игре, так и в реальности - привет, F1, Херес-1997)
                else:
                    car.qualifiedLap = 0
                    car.lapPostTime = 0
                car.bestLap = 0

    def updateTiming(self):
        """
        Рядовое обновление данных
        """
        for car in self.carList:
            if car is not None:
                # Если количество кругов, пройденных пилотом, в игре больше, чем в структуре car, обновляем данные по кругам
                newLapsCompleted = ac.getCarState(car.carId, acsys.CS.LapCount)
                if car.lapsCompleted < newLapsCompleted:
                    car.lapsCompleted = newLapsCompleted
                    car.lastLap = ac.getCarState(car.carId, acsys.CS.LastLap)
                    car.bestLap = ac.getCarState(car.carId, acsys.CS.BestLap)
                    car.totalTime += car.lastLap
                    car.lapPostTime = self.session_time
                # Общая дистанция должна обновляться постоянно, иначе сортировка в гонке будет случайной
                car.totalDistance = car.lapsCompleted + ac.getCarState(car.carId, acsys.CS.NormalizedSplinePosition)
                car.isInPitlane = ac.isCarInPitlane(car.carId)
                car.isInPit = ac.isCarInPit(car.carId)
        # self.session_time = info.graphics.sessionTimeLeft

    def doHttpPost(self, json):
        header = "POST /ACTiming2/live HTTP/1.1\r\nHost: {}:{}\r\nAccept-Encoding: identity\r\nContent-Length: {}\r\nContent-type: application/json\r\n\r\n".format(SERVER_ADDR, str(SERVER_PORT), str(len(json)))
        # postLogMessage(header)
        message = header + json
        httpThread = HTTPPostThread()
        httpThread.put(message)
        httpThread.start()        # TODO Реализовать через очередь

    def sendLeaderboardData(self):
        """
        Вызывается после обновления всех данных. Подготавливает данные к отправке.
        """
        # postLogMessage("sendLeaderboardData")
        cars_sorted = []
        # Выбираем машины, реально занятые игроками / FIXME в мультиплеере может быть истинно (car is not None), но реально пилота нет
        carsNotNone = [car for car in self.carList if car is not None]
        postLogMessage("Non-empty cars: " + str(len(carsNotNone)))
        if self.session == AC_RACE:
            ''' Сортировка по totalDistance покажет положение пилотов в любой момент гонки. Сортировка по totalTime
            позволит определять положение только в конце каждого круга (и в принципе, именно так работает
            лайв-тайминг в реальных гонках, например, F1 или DTM), при этом надо сохранять квалификационное время,
            чтобы получить корректный порядок на первом круге (игра это время не сохраняет в lastLap).
            '''
            finished = [car for car in carsNotNone if car.lapsCompleted == self.sessionLapCount]
            if len(finished) > 0:
                finished = sorted(finished, key=attrgetter('totalTime'), reverse=False)
            # postLogMessage("Finished cars list created with len = " + str(len(finished)) + "; lap count is " + str(self.sessionLapCount))
            carsToSort = [car for car in carsNotNone if car.lapsCompleted < self.sessionLapCount]
            # postLogMessage("Non-finished cars list created with len = " + str(len(finished)))
            if self.session_time < 30 * 60000:  # FIXME грязный хак, может сломаться после обновления игры
                cars_sorted = sorted(carsToSort, key=attrgetter('totalDistance'), reverse=True)
            else:
                cars_sorted = sorted(carsToSort, key=attrgetter('qualifiedTime'), reverse=False)
            cars_sorted = finished + cars_sorted
            # postLogMessage("Created full car list")
        else:
            '''
            В практике/квалификации сортируем по лучшему времени круга. В начале это время равно 0:00.000, и необходимо,
            чтобы оно не "всплывало" при сортировке. Поэтому тех, кто время не поставил, сортируем по ID.
            '''
            carsToSort = [car for car in carsNotNone if car.bestLap > 0]
            carsWithNoLaps = [car for car in carsNotNone if car not in carsToSort]
            cars_sorted = sorted(carsToSort, key=attrgetter('bestLap', 'carId'), reverse=False) + \
                          sorted(carsWithNoLaps, key=attrgetter('carId'), reverse=False)

        # Сохраняем данные в JSON и готовим к отправке.
        output_obj = {"session": self.session,                # текущая сессия (int)
                      "timeLeft": self.session_time,          # оставшееся время (int мс, клиент преобразует)
                      "numberOfLaps": self.sessionLapCount,
                      "flag": self.flag }   # число кругов в гонке FIXME а в квале как?
        cars_json_list = []
        for car in cars_sorted:
            carObj = dict()
            carObj["carId"] = car.carId
            carObj["driverName"] = car.driverName
            carObj["carName"] = car.carName
            carObj["lapsCompleted"] = car.lapsCompleted
            carObj["lastLap"] = car.lastLap
            carObj["bestLap"] = car.bestLap
            carObj["totalDistance"] = car.totalDistance  # общая дистанция
            carObj["totalTime"] = car.totalTime      # общее время в гонке
            carObj["lapPostTime"] = car.lapPostTime
            carObj["isInPitlane"] = car.isInPitlane
            carObj["isInPit"] = car.isInPit
            cars_json_list.append(carObj)
        output_obj["cars"] = cars_json_list
        jsonstr = json.dumps(output_obj)
        # Отправляем
        self.doHttpPost(jsonstr)

        # Запись в файл для тестового скрипта httpstub.py
        try:
            self.jsonfile.write(jsonstr + "\n")
            #postLogMessage("JSON written")
        except:
            postLogMessage("Unable to write JSON data to file")

    def shutdown(self):
        self.jsonfile.write(self.FALLBACK_STR)
        self.doHttpPost(self.FALLBACK_STR)
        self.jsonfile.close()

leaderboard = None
label = None  # текстовое поле на экране
runtime = 0   # время работы приложения
UPDATE_INTERVAL = 1  # интервал обновления в секундах (float)

def acMain(ac_version):
    # При запуске приложения создаётся небольшое окно и выполняется инициализация.
    global label, leaderboard #, httpThread
    name = "ACTimingDataSender"
    appWindow = ac.newApp(name)
    ac.setSize(appWindow, 200, 70)
    label = ac.addLabel(appWindow, "Label here")
    ac.setPosition(label, 3, 30)
    postLogMessage("ACTiming HTTP plugin OK")
    leaderboard = Leaderboard()
    postLogMessage("Leaderboard created")
    postLogMessage("Running directory: " + __file__);
    return name  # Возвращается имя приложения - требование AC

def acUpdate(deltaT):
    # Вызывается каждый кадр. deltaT - интервал времени между вызовами функции.
    global runtime, label, leaderboard
    # Если игра на паузе или в режиме повтора - делать нечего
    if info.graphics.status != 2:  # AC_LIVE
        return
    runtime += deltaT
    #ac.setText(label, "Session time left: " + str(info.graphics.sessionTimeLeft))
    if runtime > UPDATE_INTERVAL:  # настало время обновить данные
        # postLogMessage("Building car list")
        leaderboard.updateCarList()
        # # Если сменилась игровая сессия
        if leaderboard.updateSession():
            postLogMessage("Session has changed")
            leaderboard.resetTiming()  # обнуляем время/дистанцию для каждого пилота
        # postLogMessage("Updating timing")
        leaderboard.updateTiming()     # обновляем данные
        # postLogMessage("Dumping leaderboard to JSON")
        leaderboard.sendLeaderboardData()  # сортируем, пакуем, отправляем
        runtime = 0
    ac.setText(label, "State: OK")

def acShutdown():
    """
    Действия при закрытии AC
    """
    global leaderboard
    leaderboard.shutdown()
