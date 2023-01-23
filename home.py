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
    stock1 = 10
    while True:
        stock1 = stockManager(prodRate, consRate, stock1)
        time.sleep(1)
        mqMsg = sysv_ipc.MessageQueue(keyMsg)
        mqEng = sysv_ipc.MessageQueue(keyEng)
        m, pid = mqMsg.receive()
        need = int(m.decode())
        print(f'{pid} needs {need} \n')
        if (stock1 - need >= 10):
            send = str(need).encode()
            stock1 -= need
        else:
            send = str(stock1 - 10).encode()
            stock1 = 10
        mqEng.send(send, type=pid)
        print(f'sending {send.decode()} to {pid} \n')
        print(f'home : my current stock is {stock1} \n')

def homeBis(keyMsg, keyEng, prodRate, consRate):
    stock2 = 10
    while True:
        stock2 = stockManager(prodRate, consRate, stock2)
        time.sleep(1)
        mqMsg = sysv_ipc.MessageQueue(keyMsg)
        mqEng = sysv_ipc.MessageQueue(keyEng)
        m = (str(10 - stock2)).encode()
        mqMsg.send(m, type=os.getpid())
        print(f'need message sent, pid is {os.getpid()} \n')
        eng, t = mqEng.receive(type=os.getpid())
        eng = int(eng.decode())
        print(f'receiving {eng} \n')
        stock2 += eng
        print(f'homeBis : my current stock is {stock2} \n')





if __name__ == "__main__":
    keyMsg = 3
    keyEng = 4
    mqMsg = sysv_ipc.MessageQueue(keyMsg, sysv_ipc.IPC_CREX)
    mqEng = sysv_ipc.MessageQueue(keyEng, sysv_ipc.IPC_CREX)
    h = Process(target=home, args=(keyMsg, keyEng, 2, 1, ))
    h1 = Process(target=homeBis, args=(keyMsg, keyEng, 1, 2, ))
    h.start()
    h1.start()
    h.join()
    h1.join()
    mqMsg.remove()
    mqEng.remove()

    