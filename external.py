import sys
from multiprocessing import Process, Lock, Value
import random
import signal
import threading
import socket
import os
import time
import sysv_ipc
import concurrent.futures
import select
import tkinter as tk


endWorld, trumpElection, fuelShortage = 0, 0, 0
initTemp = 18
initPrice = 0.1740
delay = 5000


def stockManager(prodRate, consRate, stock):
    stock += prodRate
    stock -= consRate
    return stock


def home(keyMsg, keyEng, s, prodRate, consRate):
    pid = os.getpid()
    stock = s
    print(f'| I am home {pid} and my initial stock is {stock} kWh |')
    # while True:
    # stock = stockManager(prodRate, consRate, stock)
    # time.sleep(5)
    mqMsg = sysv_ipc.MessageQueue(keyMsg)
    mqEng = sysv_ipc.MessageQueue(keyEng)
    while True:
        stock = stockManager(prodRate, consRate, stock)
        time.sleep(5)
        if stock > 10:
            stock = donEnergie(stock, mqMsg, mqEng, pid)
        elif stock < 10:
            stock = demandeEnergie(stock, mqMsg, mqEng, pid)
        else:
            pass
        print(f'Home {pid} : current stock is {stock} kWh')


def demandeEnergie(stock, mqMsg, mqEng, pid):
    m = (str(10 - stock)).encode()
    mqMsg.send(m, type=pid)
    # print(f'need message sent, pid is {pid} \n')
    eng, t = mqEng.receive(type=pid)
    eng = int(eng.decode())
    # print(f'{pid} receiving {eng} \n')
    stock += eng
    return stock


def donEnergie(stock, mqMsg, mqEng, pid):
    pidH = 0
    m, pidH = mqMsg.receive()
    need = int(m.decode())
    # print(f'{pidH} needs {need} \n')
    if (stock - need >= 10):
        send = str(need).encode()
        stock -= need
    else:
        send = str(stock - 10).encode()
        stock = 10
    mqEng.send(send, type=pidH)
    print(f'Home {pid} :  is sending {send.decode()} to home {pidH}')
    return stock

def handler(sig, frame):
    global endWorld, trumpElection, fuelShortage
    if sig == signal.SIGUSR1:
        print("fin du monde")
        print("--------------------------------------------------")
        endWorld = 1
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


def external():
    while True:
        r = random.randint(0, 10)
        if r == 0:
            sig = signal.SIGUSR1
            os.kill(os.getppid(), sig)
        elif r == 1:
            sig = signal.SIGUSR2
            os.kill(os.getppid(), sig)
        elif r == 2:
            sig = signal.SIGALRM
            os.kill(os.getppid(), sig)
        else:
            print("--------------------------------------------------")
        time.sleep(5)


def priceCalcul(price, temp):
    global endWorld, trumpElection, fuelShortage
    a = 0.00003
    b1 = 0.05
    b2 = 0.005
    b3 = 0.005
    g = 0.99
    t = temp.value
    p = price.value
    price.value = g * p + a * (t * t - 40 * t + 375) + b1 * endWorld + b2 * trumpElection + b3 * fuelShortage
    print(f'Current price {price.value:.4f} €/kWh')



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
        print(f'Current temperature : {temp.value} °C')
        time.sleep(5)



def market(temp, price):
    print(f'|          Initial price : {price} €/kWh           |')
    externalProcess = Process(target=external)
    externalProcess.start()
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGALRM, handler)
    while True:
        priceCalcul(price, temp)
        time.sleep(5)
    externalProcess.join()




if __name__ == "__main__":
    print("__________________________________________________")

    sharedTemp = Value('I', initTemp)
    sharedPrice = Value('f', initPrice)
    temp = initTemp
    price = initPrice

    displayTemp = tk.Tk()
    displayTemp.title("Display Temperature")
    displayTemp.geometry('300x200+660+320')
    labelTemp = tk.Label(displayTemp, text=f'\n\nInitial temperature : \n\n{temp} °C')
    labelTemp.config(font=('verdana', 12))
    labelTemp.pack()

    displayPrice = tk.Tk()
    displayPrice.title("Display Price")
    displayPrice.geometry('300x200+960+320')
    labelPrice = tk.Label(displayPrice, text=f'\n\nInitial price : \n\n{price:.4f} €/kWh')
    labelPrice.config(font=('verdana', 12))
    labelPrice.pack()

    keyMsg = 51
    keyEng = 61
    mqMsg = sysv_ipc.MessageQueue(keyMsg, sysv_ipc.IPC_CREX)
    mqEng = sysv_ipc.MessageQueue(keyEng, sysv_ipc.IPC_CREX)
    #mqMsg = sysv_ipc.MessageQueue(keyMsg)
    #mqEng = sysv_ipc.MessageQueue(keyEng)
    h = Process(target=home, args=(keyMsg, keyEng, 10, 2, 1,))
    h1 = Process(target=home, args=(keyMsg, keyEng, 10, 1, 2,))
    h2 = Process(target=home, args=(keyMsg, keyEng, 10, 2, 1,))
    marketProcess = Process(target=market, args=(sharedTemp, sharedPrice,))
    weatherProcess = Process(target=weather, args=(sharedTemp,))
    h.start()
    h1.start()
    h2.start()
    marketProcess.start()
    weatherProcess.start()

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
        price = sharedPrice.value
        labelPrice.config(text=f'\n\nCurrent price : \n\n{price:.4f} €/kWh')
        displayPrice.after(delay, update_price)


    update_temp()
    update_price()
    displayTemp.mainloop()
    displayPrice.mainloop()
    h.join()
    h1.join()
    h2.join()
    marketProcess.join()
    weatherProcess.join()
    mqMsg.remove()
    mqEng.remove()