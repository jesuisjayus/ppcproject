import sys
from multiprocessing import Process, Lock
import threading 
import socket
import os
import concurrent.futures
import select


global PORT
PORT = 6666



def fakeHome(s):
    HOST = "localhost"
    global PORT
    stockHome = s
    pid = os.getpid()
    print(f'my pid is {pid} and my stock is {stockHome}')
    if stockHome < 10:
        typeTransac = 1 #needs
    else:
        typeTransac = 2 #surplus
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as home_socket:
        home_socket.connect((HOST, PORT))
        m = f"{typeTransac} {pid} {abs(10-stockHome)}"  #type,PID,qty
        home_socket.sendall(m.encode())
        purchase = home_socket.recv(1024)
        purchase = purchase.decode().split()
        if typeTransac == 1:
            stockHome += int(purchase[1])
        elif typeTransac == 2:
            stockHome -= int(purchase[1])
        print(f'{pid} my new stock is {stockHome}')



def external():
    print("external")


def transaction(home_socket, address, stock, mutex):
    with home_socket:
        print(f'Connected to home: {address}')
        data = home_socket.recv(1024)
        data = data.decode().split()
        [typeTransac, pid, qty] = data
        qty = int(qty)
        print(f'transac {typeTransac}')
        if typeTransac == "1":
            if qty <= stock:
                mutex.aquire()
                sale = f'{pid} {qty}'
                stock -= qty
                home_socket.sendto(sale.encode(), address)
                mutex.release()
            else:
                mutex.aquire()
                sale = f'{pid} {stock}'
                stock = 0
                home_socket.sendto(sale.encode(), address)
                mutex.release()
        elif typeTransac == "2":
            mutex.aquire()
            stock += qty
            purchase = f'{pid} {qty}'
            print(f'p : {purchase}')
            home_socket.sendto(purchase.encode(), address)
            mutex.release()
        # else pour gestion d'erreur

        return stock


def market(mutex):
    stock = 1
    price = 0.1740
    HOST = "localhost"
    global PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_socket:
        market_socket.bind((HOST, PORT))
        market_socket.listen(2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            while True:
                readable, writable, error = select.select([market_socket], [], [], 1)
                if market_socket in readable:
                    home_socket, address = market_socket.accept()
                    mutex.acquire()
                    stock = executor.submit(transaction, home_socket, address, stock, mutex)
                    mutex.release()


    #externalProcess = Process(target=external)
    #externalProcess.start()
    #externalProcess.join()
if __name__ == "__main__":
    mutex = Lock()
    marketProcess = Process(target=market, args=(mutex,))
    home = Process(target=fakeHome, args=(12,))
    home2 = Process(target=fakeHome, args=(8,))
    marketProcess.start()
    home.start()
    home2.start()
    marketProcess.join()
    home.join()
    home2.join()
