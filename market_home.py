import concurrent.futures
import os
import random
import select
import signal
import socket
import sysv_ipc
import threading
import time
import tkinter as tk
from multiprocessing import Process, Value, Lock

serv = True
PORT = 7607
initStock = 3
HOST = "localhost"
worldWar, trumpElection, fuelShortage = 0, 0, 0
initTemp = 18
initPrice = 0.1740
delay = 1000

def home(s, tradePol, keyMsg, keyEng, prodRate, consRate):
    global PORT
    global serv
    stockHome = s
    pid = os.getpid()
    print(f'my pid is {pid} and my stock is {stockHome}')
    mqMsg = sysv_ipc.MessageQueue(keyMsg)
    mqEng = sysv_ipc.MessageQueue(keyEng)
    while True:
        stockHome=stockManager(prodRate, consRate, stockHome);
        stockHome=tradePolicy(tradePol, stockHome, pid, mqMsg, mqEng)
        time.sleep(delay/1000)
        #print(f'my pid is {pid} and my stock is {stockHome}')
def stockManager(prodRate, consRate, stockHome):
    stockHome += prodRate
    stockHome -= consRate
    return stockHome


def tradePolicy(policy, stockHome, pid, mqMsg, mqEng):#1 don, 2 vente, 3 vente si personne a qui donner
    if stockHome>10:
        match policy:
            case 1:
                stockHome = donEnergie(stockHome, mqMsg, mqEng, pid)
                print(f'my pid is {pid} and my new stock is {stockHome}')
            case 2:
                typeTransac = 2 #surplus
                stockHome=homeSelling(typeTransac, pid, stockHome)
                print(f'my pid is {pid} and my new stock is {stockHome}')
            case 3:
                stockHome=debarras(stockHome, mqMsg, mqEng, pid)
                print(f'my pid is {pid} and my new stock is {stockHome}')
    elif stockHome<10 :
        stockHome=homeRestock(stockHome, pid, mqMsg, mqEng)
        print(f'my pid is {pid} and my new stock is {stockHome}')
    else:
        pass
    return stockHome


def donEnergie(stockHome, mqMsg, mqEng, pid):
    pidH=0
    try:
        #print("hello")
        m, pidH = mqMsg.receive(block=False)
        need = int(m.decode())
        #print(f'{pidH} needs {need} \n')
        if (stockHome - need >= 10):
            send = str(need).encode()
            stockHome -= need
        else:
            send = str(stockHome - 10).encode()
            stockHome = 10
        mqEng.send(send, type=pidH)
        #print("hello")
        print(f'{pid} is sending {send.decode()} to {pidH} \n')
    except sysv_ipc.BusyError:
        print("personne ne veut mon energie, miskina")
        pass
    return stockHome
def homeSelling(typeTransac, pid, stockHome):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as home_socket:
        home_socket.connect((HOST, PORT))
        m = f"{typeTransac} {pid} {abs(10-stockHome)}"  #type,PID,qty
        home_socket.sendall(m.encode())
        purchase = home_socket.recv(1024)
        purchase = purchase.decode().split()
        stockHome -= int(purchase[1])
        print(f'{pid} : sending {purchase[1]} to the market')
        print(f'{pid} my new stock is {stockHome}')
    return stockHome
def debarras(stockHome, mqMsg, mqEng, pid):
    pidH=0
    try :
        m, pidH = mqMsg.receive(block=False)
        need = int(m.decode())
        #print(f'{pidH} needs {need} \n')
        if (stockHome - need >= 10):
            send = str(need).encode()
            stockHome -= need
        else:
            send = str(stockHome - 10).encode()
            stockHome = 10
        mqEng.send(send, type=pidH)
        print(f'{pid} is sending {send.decode()} to {pidH} \n')
    except sysv_ipc.QueueEmptyError:
        typeTransac=1
        stockHome=homeSelling(typeTransac, pid, stockHome)
    return stockHome


def homeRestock (stockHome, pid, mqMsg, mqEng): #envoi dans mqMsg pk besoin si qqun a à donner : reponse si pas de réponse dans mqEnd : achat
    m = (str(10 - stockHome)).encode()
    mqMsg.send(m, type=pid)
    try:
        eng, t = mqEng.receive(block=False,type=pid)
        eng = int(eng.decode())
        #print(f'{pid} receiving {eng} \n')
        stockHome += eng
    except sysv_ipc.BusyError:
        #print("hello3\n")
        typeTransac=1
        print("j'achete")
        stockHome=homeBuying(typeTransac, pid, stockHome)
    return stockHome
def homeBuying(typeTransac, pid, stockHome):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as home_socket:
        home_socket.connect((HOST, PORT))
        m = f"{typeTransac} {pid} {abs(10-stockHome)}"  #type,PID,qty
        home_socket.sendall(m.encode())
        purchase = home_socket.recv(1024)
        purchase = purchase.decode().split()
        if int(purchase[1]) != 0:
            stockHome += int(purchase[1])
            print(f'{pid} : receiving {purchase[1]} from the market')
            print(f'{pid} my new stock is {stockHome}')
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
                print("--------------------------------------------------")
        time.sleep(delay/1000)
def handler(sig, frame):
    global worldWar, trumpElection, fuelShortage
    if sig == signal.SIGUSR1:
        if worldWar == 0:
            print("World war")
            print("--------------------------------------------------")
            worldWar = 1
        else:
            print("End of world war")
            print("--------------------------------------------------")
            worldWar = 0
    elif sig == signal.SIGUSR2:
        if trumpElection == 0:
            print("Start of Trump election")
            print("--------------------------------------------------")
            trumpElection = 1
        else:
            print("End of Trump election")
            print("--------------------------------------------------")
            trumpElection = 0
    elif sig == signal.SIGALRM:
        if fuelShortage == 0:
            print("Start of fuel shortage")
            print("--------------------------------------------------")
            fuelShortage = 1
        else:
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
    print(f'|          Initial temperature : {temp.value} °C           |')
    print("¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯")
    while True:
        r = random.randint(-1, 1)
        match r:
            case -1:
                if temp.value > 0:
                    temp.value += r
            case 1:
                if temp.value < 35:
                    temp.value += r
        #print(f'Current temperature : {temp.value} °C')
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
    price.value = g * p + a * (t * t - 40 * t + 375) + b1 * worldWar + b2 * trumpElection + b3 * fuelShortage
    mutex.release()
    #print(f'Current price {price.value:.4f} €/kWh')

    #externalProcess = Process(target=external)
    #externalProcess.start()
    #externalProcess.join()


def market(mutex, temp, price, stock):
    print(f'|          Initial price : {price.value:.4f} €/kWh           |')
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
            while serv:
                priceCalcul(price, temp)
                readable, writable, error = select.select([market_socket], [], [], 1)
                if market_socket in readable:
                    home_socket, address = market_socket.accept()
                    executor.submit(MarketTransaction, home_socket, address, mutex, price, temp, stock)
    externalProcess.join()
def MarketTransaction(home_socket, address, mutex, stock):
    with home_socket:
        #print(f'Connected to home: {address}')
        data = home_socket.recv(1024)
        if not data:
            #priceCalcul(price, temp)
            print("No data received from the client")
        else:
            print("Data received:", data.decode())
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
            # else pour gestion d'erreur
            print("stock is ", stock.value)
            mutex.release()



if __name__ == "__main__":
    print("__________________________________________________")

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
    mutex = threading.Lock()
    keyMsg = 170
    keyEng = 270
    mqMsg = sysv_ipc.MessageQueue(keyMsg, sysv_ipc.IPC_CREX)
    mqEng = sysv_ipc.MessageQueue(keyEng, sysv_ipc.IPC_CREX)
    #mqMsg = sysv_ipc.MessageQueue(keyMsg)
    #mqEng = sysv_ipc.MessageQueue(keyEng)
    home1 = Process(target=home, args=(7, 2, keyMsg, keyEng, 1, 1))
    home2 = Process(target=home, args=(10, 2, keyMsg, keyEng, 2, 1))
    home3 = Process(target=home, args=(10, 1, keyMsg, keyEng, 1, 1))
    weatherProcess = Process(target=weather, args=(sharedTemp,))
    marketProcess = Process(target=market, args=(mutex, sharedTemp, sharedPrice, sharedStock,))
    weatherProcess.start()
    marketProcess.start()
    time.sleep(0.5)

    home1.start()
    home2.start()
    home3.start()


    #market(mutex, sharedTemp, sharedPrice)

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
    weatherProcess.join()
    marketProcess.join()
    mqMsg.remove()
    mqEng.remove()
