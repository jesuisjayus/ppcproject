import sys
from multiprocessing import Process, Lock, Value
import random
import signal
import threading
import socket
import os
import time
import concurrent.futures
import select

global endWorld, trumpElection, fuelShortage, end
endWorld, trumpElection, fuelShortage, end = 0, 0, 0, True


def handler(sig, frame):
    global endWorld, trumpElection, fuelShortage, end
    if sig == signal.SIGUSR1:
        print("fin du monde")
        end = False
    elif sig == signal.SIGUSR2:
        if trumpElection == 0:
            print("Start of Trump election")
            trumpElection = 1
        else:
            print("End of Trump election")
            trumpElection = 0
    elif sig == signal.SIGALRM:
        if fuelShortage == 0:
            print("Start of fuel shortage")
            fuelShortage = 1
        else:
            print("End of fuel shortage")
            fuelShortage = 0


def external():
    while end:
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
            pass
        time.sleep(5)


def priceCalcul(prix, mem):
    global endWorld, trumpElection, fuelShortage
    a = 0.00003
    b1 = 0.05
    b2 = 0.005
    b3 = 0.005
    g = 0.99
    t = mem.value
    prix = g * prix + a * (t * t - 40 * t + 375) + b1 * endWorld + b2 * trumpElection + b3 * fuelShortage
    print(f"le prix est de {prix}")
    return prix



def weather(mem):
    while end:
        r = random.randint(-1,1)
        match r:
            case -1:
                if(mem.value > 0):
                    mem.value += r
            case 1:
                if(mem.value < 35):
                    mem.value += r
        print("Current temperature : ", mem.value, "°C")
        time.sleep(5)



def market(mem):
    price = 0.1740
    externalProcess = Process(target=external)
    externalProcess.start()
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGALRM, handler)
    while end:
        price = priceCalcul(price, mem)
        time.sleep(5)
    externalProcess.join()




if __name__ == "__main__":
    shared_memory = Value('I', 18)
    weatherProcess = Process(target=weather, args=(shared_memory,))
    marketProcess = Process(target=market, args=(shared_memory,))
    weatherProcess.start()
    marketProcess.start()
    weatherProcess.join()
    marketProcess.join()
