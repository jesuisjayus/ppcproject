import sys
from multiprocessing import Process, Array, Value
import random 
import time

def weather(mem):
    while True:
        r = random.randint(-1,1)
        match r:
            case -1:
                if(mem.value > 0):
                    mem.value += r
            case 1:
                if(mem.value < 30):
                    mem.value += r
        print("Current temperature : ", mem.value, "°C")
        time.sleep(1)






if __name__=="__main__":

    shared_memory = Value('I', 18)
    
    w = Process(target=weather, args=(shared_memory, ))
    w.start()
    w.join()