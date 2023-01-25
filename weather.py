import sys
from multiprocessing import Process, Array, Value
import random 
import time

def weather(mem):
    prix = 0.1740
    a = 0.00003
    b = 0.99
    while True:
        r = random.randint(-1,1)
        match r:
            case -1:
                if(mem.value > 0):
                    mem.value += r
            case 1:
                if(mem.value < 35):
                    mem.value += r
        print("Current temperature : ", mem.value, "°C")
        t = mem.value
        prix = b*prix + a*(t*t-40*t+375)
        print(f"le prix est de {prix}")
        time.sleep(0.5)






if __name__=="__main__":

    shared_memory = Value('I', 32)
    
    w = Process(target=weather, args=(shared_memory, ))
    w.start()
    w.join()