import schedule
import time

discrete_sampling = True

def job():
    print("I'm working ..")

def job2():
    print("It's the 17th second of the minute.")

def job3():
    print(".")

if discrete_sampling == True:

    #schedule.every(1).to(2).minutes.do(job)
    #schedule.every().minute.at(":17").do(job2)
    schedule.every(3).seconds.do(job3)

while True:
    schedule.run_pending()
    time.sleep(3)
    discrete_sampling = False
