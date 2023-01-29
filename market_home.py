import sys
from multiprocessing import Process,Array, Value
import threading
import socket
from queue import Queue
import os
import concurrent.futures
import sysv_ipc
import random 
import select
import time


serv = True
PORT = 6661
stock = 0
HOST = "localhost"


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
        time.sleep(2)
        print(f'my pid is {pid} and my stock is {stockHome}')

def tradePolicy(policy, stockHome, pid, mqMsg, mqEng, mqNeed):
    if stockHome>10:
        if policy==1:
            stockHome = donEnergie(stockHome, mqMsg, mqEng, pid)
        elif policy==2:
            typeTransac = 2 #surplus
            stockHome=homeSelling(typeTransac, pid, stockHome)
        elif policy ==3:
            stockHome=debarras(stockHome, mqMsg, mqEng, pid)
        else:
            a=1
            #gestion errreur argument
    elif stockHome<10 :
        stockHome=homeRestock(stockHome, pid, mqMsg, mqEng, mqNeed)
    else:
        pass
    return stockHome

""" def tradePolicy1(policy, stockHome, pid): #1 don, 2 vente, 3 vente si personne a qui donner
    if policy==1:
        if stockHome>10 :
            stockHome = donEnergie(stockHome, mqMsg, mqEng, pid)
        elif stockHome<10:
            stockHome = demandeEnergie(stockHome, mqMsg, mqEng, pid)
        else:
            pass
    elif policy==2:
        if stockHome < 10:
            typeTransac = 1 #needs
            stockHome=homeTransaction(typeTransac, pid, stockHome)
        elif stockHome > 10:
            typeTransac = 2 #surplus
            stockHome=homeTransaction(typeTransac, pid, stockHome)
        else:
            pass
    elif policy==3:
        pass
    else:
        pass
    return stockHome """

def debarras(stockHome, mqMsg, mqEng, pid):
    pidH=0
    try :
        m, pidH = mqMsg.receive()
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
         



    return stockHome
def stockManager(prodRate, consRate, stockHome):
    stockHome += prodRate
    stockHome -= consRate
    return stockHome

def homeRestock (stockHome, pid, mqMsg, mqEng, mqNeed): #envoi dans mqMsg pk besoin si qqun a à donner : reponse si pas de rpéonse dans mqEnd : achat
    m = (str(10 - stockHome)).encode()
    mqMsg.send(m, type=pid)
    print("hello\n")
    try:
        print("hello2\n")
        eng, t = mqEng.receive(block=False,type=pid)
        eng = int(eng.decode())
        #print(f'{pid} receiving {eng} \n')
        stockHome += eng
    except sysv_ipc.BusyError:
        print("hello3\n")
        typeTransac=1
        stockHome=homeBuying(typeTransac, pid, stockHome)
    return stockHome
    
""" def demandeEnergie(stockHome, mqMsg, mqEng, pid):
    m = (str(10 - stockHome)).encode()
    mqMsg.send(m, type=pid)
    #print(f'need message sent, pid is {pid} \n')
    try:
        eng, t = mqEng.receive(type=pid)
        eng = int(eng.decode())
        #print(f'{pid} receiving {eng} \n')
        stockHome += eng
    except sysv_ipc.QueueEmptyError:
        stockHome=homeTransaction(1, pid, stockHome)
    return stockHome """

def donEnergie(stockHome, mqMsg, mqEng, pid):
    pidH=0
    m, pidH = mqMsg.receive()
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
    return stockHome


""" def homeTransaction(typeTransac, pid, stockHome):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as home_socket:
        home_socket.connect((HOST, PORT))
        m = f"{typeTransac} {pid} {abs(10-stockHome)}"  #type,PID,qty
        home_socket.sendall(m.encode())
        purchase = home_socket.recv(1024)
        purchase = purchase.decode().split()
        if typeTransac == 1:
            if int(purchase[1]) != 0:
                stockHome += int(purchase[1])
                print(f'{pid} : receiving {purchase[1]} from the market')
                print(f'{pid} my new stock is {stockHome}')
        elif typeTransac == 2:
            stockHome -= int(purchase[1])
            print(f'{pid} : sending {purchase[1]} to the market')
            print(f'{pid} my new stock is {stockHome}')
    return stockHome """

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
    print("external")


def MarketTransaction(home_socket, address, mutex):
    global stock
    with home_socket:
        #print(f'Connected to home: {address}')
        data = home_socket.recv(1024)
        data = data.decode().split()
        [typeTransac, pid, qty] = data
        qty = int(qty)
        mutex.acquire()
        if typeTransac == "1":
            if qty <= stock:
                sale = f'{pid} {qty}'
                stock -= qty
                home_socket.sendto(sale.encode(), address)
            else:
                sale = f'{pid} {stock}'
                stock = 0
                home_socket.sendto(sale.encode(), address)
        elif typeTransac == "2":
            stock += qty
            purchase = f'{pid} {qty}'
            home_socket.sendto(purchase.encode(), address)
        # else pour gestion d'erreur
        print("stock is ",stock)
        mutex.release()


def market(mutex):
    price = 0.1740
    global PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_socket:
        market_socket.bind((HOST, PORT))
        market_socket.listen(8)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            while serv:
                readable, writable, error = select.select([market_socket], [], [], 1)
                if market_socket in readable:
                    home_socket, address = market_socket.accept()
                    executor.submit(MarketTransaction, home_socket, address, mutex)



    #externalProcess = Process(target=external)
    #externalProcess.start()
    #externalProcess.join()

""" import sysv_ipc
queue_key = 1234
queue = sysv_ipc.MessageQueue(queue_key)
try:
    message, message_type = queue.receive(block=False)
    print("Queue is not empty")
except sysv_ipc.QueueEmptyError:
    print("Queue is empty") """



if __name__ == "__main__":
    mutex = threading.Lock()
    keyMsg = 101
    keyEng = 202
    keyNeed = 303
    #mqMsg = sysv_ipc.MessageQueue(keyMsg, sysv_ipc.IPC_CREX)
    #mqEng = sysv_ipc.MessageQueue(keyEng, sysv_ipc.IPC_CREX)
    mqMsg = sysv_ipc.MessageQueue(keyMsg)
    mqEng = sysv_ipc.MessageQueue(keyEng)
    home1 = Process(target=home, args=(10, 3, keyMsg, keyEng, keyNeed, 3, 1))
    home2 = Process(target=home, args=(10, 1, keyMsg, keyEng, keyNeed, 1, 1))
    home3 = Process(target=home, args=(7, 1, keyMsg, keyEng, keyNeed, 1, 1))
    home1.start()
    home2.start()
    home3.start()
    market(mutex)
    home1.join()
    home2.join()
    home3.join()
    mqMsg.remove()
    mqEng.remove()
    mqNeed.remove()
