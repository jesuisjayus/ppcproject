import concurrent.futures
import os
import random
import select
import signal
import socket
import sysv_ipc
import time
import tkinter as tk
from threading import Lock
from multiprocessing import Process, Value


PORT = 6666
HOST = "localhost"
worldWar, trumpElection, fuelShortage = 0, 0, 0
initStock = 15
initTemp = 18
initPrice = 0.1740
delay = 1000
threshold = 30


def home(s, tradePol, keyMsg, keyEng, prodRate, consRate):
    global PORT
    stockHome = s
    pid = os.getpid()
    print(f'my pid is {pid} and my stock is {stockHome}')
    mqMsg = sysv_ipc.MessageQueue(keyMsg)
    mqEng = sysv_ipc.MessageQueue(keyEng)
    while True:
        stockHome=stockManager(prodRate, consRate, stockHome);
        stockHome=tradePolicy(tradePol, stockHome, pid, mqMsg, mqEng)
        time.sleep(delay/1000)
def stockManager(prodRate, consRate, stockHome):
    stockHome += prodRate
    stockHome -= consRate
    return stockHome


def tradePolicy(policy, stockHome, pid, mqMsg, mqEng):#1 don, 2 vente, 3 vente si personne a qui donner
    if stockHome>threshold:
        match policy:
            case 1:
                stockHome = donEnergie(stockHome, mqMsg, mqEng, pid)
            case 2:
                typeTransac = 2 #surplus
                stockHome=homeSelling(typeTransac, pid, stockHome)
            case 3:
                stockHome=debarras(stockHome, mqMsg, mqEng, pid)
    elif stockHome<threshold :
        stockHome=homeRestock(stockHome, pid, mqMsg, mqEng)
    else:
        pass
    return stockHome


def donEnergie(stockHome, mqMsg, mqEng, pid):
    pidH=0
    try:
        m, pidH = mqMsg.receive(block=False)
        need = int(m.decode())
        if (stockHome - need >= threshold):
            send = str(need).encode()
            stockHome -= need
        else:
            send = str(stockHome - threshold).encode()
            stockHome = threshold
        mqEng.send(send, type=pidH)
        print(f'{pid} is sending {send.decode()} to {pidH}, my new stock is {stockHome} kWh')
    except sysv_ipc.BusyError:
        pass
    return stockHome
def homeSelling(typeTransac, pid, stockHome):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as home_socket:
        home_socket.connect((HOST, PORT))
        m = f"{typeTransac} {pid} {abs(threshold-stockHome)}"  #type,PID,qty
        home_socket.sendall(m.encode())
        purchase = home_socket.recv(1024)
        purchase = purchase.decode().split()
        stockHome -= int(purchase[1])
        print(f'{pid} is sending {purchase[1]} to the market, my new stock is {stockHome}')
    return stockHome
def debarras(stockHome, mqMsg, mqEng, pid):
    pidH=0
    try:
        m, pidH = mqMsg.receive(block=False)
        need = int(m.decode())
        #print(f'{pidH} needs {need} \n')
        if (stockHome - need >= threshold):
            send = str(need).encode()
            stockHome -= need
        else:
            send = str(stockHome - threshold).encode()
            stockHome = threshold
        mqEng.send(send, type=pidH)
        print(f'{pid} is sending {send.decode()} to {pidH}, my new stock is {stockHome} kWh')
    except sysv_ipc.BusyError:
        typeTransac=1
        stockHome=homeSelling(typeTransac, pid, stockHome)
    return stockHome


def homeRestock (stockHome, pid, mqMsg, mqEng): #envoi dans mqMsg pk besoin si qqun a à donner : reponse si pas de réponse dans mqEnd : achat
    m = (str(threshold - stockHome)).encode()
    mqMsg.send(m, type=pid)
    try:
        eng, t = mqEng.receive(block=False, type=pid)
        eng = int(eng.decode())
        stockHome += eng
    except sysv_ipc.BusyError:
        typeTransac = 1
        stockHome = homeBuying(typeTransac, pid, stockHome)
    return stockHome


def homeBuying(typeTransac, pid, stockHome):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as home_socket:
        home_socket.connect((HOST, PORT))
        m = f"{typeTransac} {pid} {abs(threshold-stockHome)}"  #type,PID,qty
        home_socket.sendall(m.encode())
        purchase = home_socket.recv(1024)
        purchase = purchase.decode().split()
        if int(purchase[1]) != 0:
            stockHome += int(purchase[1])
            print(f'{pid} : receiving {purchase[1]} from the market, my new stock is {stockHome}')
    return stockHome


def external():
    while True:
        r = random.randint(0, 20)
        match r:
            case 0:
                sig = signal.SIGUSR1
                os.kill(os.getppid(), sig)
            case 1:
                sig = signal.SIGUSR2
            case 2:
                sig = signal.SIGALRM
                os.kill(os.getppid(), sig)
            case other:
                pass
        time.sleep(delay/1000)
def handler(sig, frame):
    global worldWar, trumpElection, fuelShortage
    if sig == signal.SIGUSR1:
        if worldWar == 0:
            print("--------------------------------------------------")
            print("World war")
            print("--------------------------------------------------")
            worldWar = 1
        else:
            print("--------------------------------------------------")
            print("End of world war")
            print("--------------------------------------------------")
            worldWar = 0
    elif sig == signal.SIGUSR2:
        if trumpElection == 0:
            print("--------------------------------------------------")
            print("Start of Trump election")
            print("--------------------------------------------------")
            trumpElection = 1
        else:
            print("--------------------------------------------------")
            print("End of Trump election")
            print("--------------------------------------------------")
            trumpElection = 0
    elif sig == signal.SIGALRM:
        if fuelShortage == 0:
            print("--------------------------------------------------")
            print("Start of fuel shortage")
            print("--------------------------------------------------")
            fuelShortage = 1
        else:
            print("--------------------------------------------------")
            print("End of fuel shortage")
            print("--------------------------------------------------")
            fuelShortage = 0

def handlerC(sig, frame):
    print('CTRL+C was pressed. Exit program')
    mqEng.remove()
    mqMsg.remove()
    displayMarket.destroy()
    displayTemp.destroy()




def weather(temp):
    mutex = Lock()
    while True:
        r = random.randint(-1, 1)
        mutex.acquire()
        match r:
            case -1:
                if temp.value > 0:
                    temp.value += r
            case 1:
                if temp.value < 35:
                    temp.value += r
        mutex.release()
        time.sleep(delay/1000)
def priceCalcul(price, temp):
    mutex = Lock()
    global worldWar, trumpElection, fuelShortage
    a = 0.00003
    b1 = 0.05
    b2 = 0.005
    b3 = 0.005
    g = 0.99
    t = temp.value
    p = price.value
    mutex.acquire()
    price.value = g * p + a * (t * t - 40 * t + 375) #+ b1 * worldWar + b2 * trumpElection + b3 * fuelShortage
    mutex.release()


def market(temp, price, stock):
    externalProcess = Process(target=external)
    externalProcess.start()
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGALRM, handler)
    global PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_socket:
        market_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        market_socket.bind((HOST, PORT))
        market_socket.listen(8)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            while True:
                priceCalcul(price, temp)
                readable, writable, error = select.select([market_socket], [], [], 1)
                if market_socket in readable:
                    home_socket, address = market_socket.accept()
                    executor.submit(MarketTransaction, home_socket, address, stock)
    externalProcess.join()
def MarketTransaction(home_socket, address, stock):
    mutex = Lock()
    with home_socket:
        data = home_socket.recv(1024)
        if not data:
            print("No data received from the client")
        else:
            data = data.decode().split()
            [typeTransac, pid, qty] = data
            qty = int(qty)
            mutex.acquire()
            if typeTransac == "1":
                if qty <= stock.value:
                    sale = f'{pid} {qty}'
                    stock.value -= qty
                    home_socket.sendto(sale.encode(), address)
                else:
                    sale = f'{pid} {stock.value}'
                    stock.value = 0
                    home_socket.sendto(sale.encode(), address)
            elif typeTransac == "2":
                stock.value += qty
                purchase = f'{pid} {qty}'
                home_socket.sendto(purchase.encode(), address)
            else:
                pass
            mutex.release()



if __name__ == "__main__":

    signal.signal(signal.SIGINT, handlerC)

    sharedTemp = Value('I', initTemp)
    sharedPrice = Value('f', initPrice)
    sharedStock = Value('I', initStock)
    temp = initTemp
    price = initPrice
    stock = initStock

    displayTemp = tk.Tk()
    displayTemp.title("Temperature")
    displayTemp.geometry('300x200+660+320')
    labelTemp = tk.Label(displayTemp, text=f'\n\nInitial temperature : \n\n{temp} °C')
    labelTemp.config(font=('verdana', 12))
    labelTemp.pack()

    displayMarket = tk.Tk()
    displayMarket.title("Market")
    displayMarket.geometry('300x200+960+320')
    labelMarket = tk.Label(displayMarket, text=f'\nInitial price : \n\n{price:.4f} €/kWh\n\n Market Stock : {stock} kWh')
    labelMarket.config(font=('verdana', 12))
    labelMarket.pack()

    sharedTemp = Value('I', initTemp)
    sharedPrice = Value('f', initPrice)
    temp = initTemp
    price = initPrice

    keyMsg = 170
    keyEng = 270
    mqMsg = sysv_ipc.MessageQueue(keyMsg, sysv_ipc.IPC_CREX)
    mqEng = sysv_ipc.MessageQueue(keyEng, sysv_ipc.IPC_CREX)

    home1 = Process(target=home, args=(35, 1, keyMsg, keyEng, 1, 2))
    home2 = Process(target=home, args=(28, 2, keyMsg, keyEng, 1, 1))
    home3 = Process(target=home, args=(32, 3, keyMsg, keyEng, 2, 1))
    home4 = Process(target=home, args=(29, 1, keyMsg, keyEng, 1, 3,))
    weatherProcess = Process(target=weather, args=(sharedTemp,))
    marketProcess = Process(target=market, args=(sharedTemp, sharedPrice, sharedStock,))

    weatherProcess.start()
    marketProcess.start()
    time.sleep(0.2)

    home1.start()
    home2.start()
    home3.start()
    home4.start()

    def update_temp():
        temp = sharedTemp.value
        labelTemp.config(text=f'\n\nCurrent temperature : \n\n{temp} °C')
        if temp >= 25:
            labelTemp.config(fg="red")
        elif temp <= 10:
            labelTemp.config(fg="blue")
        else:
            labelTemp.config(fg="green")
        displayTemp.after(delay, update_temp)
    def update_price():
        stock = sharedStock.value
        price = sharedPrice.value
        labelMarket.config(text=f'\nCurrent price : \n\n{price:.4f} €/kWh\n\n Market stock : {stock} kWh')
        displayMarket.after(delay, update_price)

    update_temp()
    update_price()
    displayTemp.mainloop()
    displayMarket.mainloop()

    home1.join()
    home2.join()
    home3.join()
    home4.join()
    weatherProcess.join()
    marketProcess.join()
