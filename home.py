import sys
import sysv_ipc
from multiprocessing import Process, Array, Value
import os
import random 
import time



def stockManager(prodRate, consRate, stock):
    stock += prodRate
    stock -= consRate
    return stock

    
def home(keyMsg, keyEng, prodRate, consRate):
    pid=os.getpid()
    stock = 10
    print("I am ",pid," and my initial stock home is ",stock)
    #while True:
    stock = stockManager(prodRate, consRate, stock)
    time.sleep(1)
    mqMsg = sysv_ipc.MessageQueue(keyMsg)
    mqEng = sysv_ipc.MessageQueue(keyEng)
    while True:
        stock = stockManager(prodRate, consRate, stock)
        time.sleep(1)
        if stock>10 :
            stock = donEnergie(stock,mqMsg,mqEng,pid)
        elif stock<10:
            stock = demandeEnergie(stock,mqMsg,mqEng,pid)
        print(f'home {pid} : my current stock is {stock} \n')

def demandeEnergie(stock, mqMsg, mqEng, pid):
    m = (str(10 - stock)).encode()
    mqMsg.send(m, type=pid)
    print(f'need message sent, pid is {pid} \n')
    eng, t = mqEng.receive(type=pid)
    eng = int(eng.decode())
    print(f'receiving {eng} \n')
    stock += eng
    return stock

def donEnergie(stock, mqMsg, mqEng, pid):
    pidH=0
    m, pidH = mqMsg.receive()
    need = int(m.decode())
    print(f'{pidH} needs {need} \n')
    if (stock - need >= 10):
        send = str(need).encode()
        stock -= need
    else:
        send = str(stock - 10).encode()
        stock = 10
    mqEng.send(send, type=pidH)
    print(f'{pid} is sending {send.decode()} to {pidH} \n')
    return stock


if __name__ == "__main__":
    keyMsg = 5
    keyEng = 6
    mqMsg = sysv_ipc.MessageQueue(keyMsg, sysv_ipc.IPC_CREX)
    mqEng = sysv_ipc.MessageQueue(keyEng, sysv_ipc.IPC_CREX)
    #mqMsg = sysv_ipc.MessageQueue(keyMsg)
    #mqEng = sysv_ipc.MessageQueue(keyEng)
    h = Process(target=home, args=(keyMsg, keyEng, 2, 1, ))
    h1 = Process(target=home, args=(keyMsg, keyEng, 1, 2, ))
    h2 = Process(target=home, args=(keyMsg, keyEng, 1, 2, ))
    h.start()
    h1.start()
    h2.start()
    h.join()
    h1.join()
    h2.join()
    mqMsg.remove()
    mqEng.remove()


    