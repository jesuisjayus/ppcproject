import sys
from multiprocessing import Process
import threading
import socket
import os
import concurrent.futures
import select
import time


serv = True
PORT = 6667
stock = 0
HOST = "localhost"


def fakeHome(s):
    global PORT
    global serv
    stockHome = s
    pid = os.getpid()
    print(f'my pid is {pid} and my stock is {stockHome}')
    while True:
        if stockHome < 10:
            typeTransac = 1 #needs
        elif stockHome > 10:
            typeTransac = 2 #surplus
        else:
            typeTransac = 0
        stockHome=homeTransaction(typeTransac,pid,stockHome)

def homeTransaction(typeTransac,pid,stockHome):
    if typeTransac != 0:
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
    else:
        pass
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



if __name__ == "__main__":
    mutex = threading.Lock()
    home = Process(target=fakeHome, args=(8,))
    home2 = Process(target=fakeHome, args=(12,))
    home3 = Process(target=fakeHome, args=(15,))
    home.start()
    home2.start()
    home3.start()
    market(mutex)
    home.join()
    home2.join()
    home3.join()
