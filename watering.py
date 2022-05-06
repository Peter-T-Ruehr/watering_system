# sudo pigpiod

global window_open
window_open = False

# stream: enthought blog raspberry pi sensor and actuator control
import time
from time import localtime, strftime

import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) # GPIO.BCM

import pigpio

import tkinter as tk 
from tkinter import messagebox

from gpiozero import CPUTemperature

import threading

global interval
interval = 10*60 # seconds

watering_time = 3 * 60 # [20,20,3,120,100] # minutes
watering_clock_hour = 9
watering_clock_minute = interval/60

# PINs
# window servo = 7
#global pump_relay_pin
pump_relay_pin = 40
#global moist_relay_pin
moist_relay_pin = 23
#global moist_sens_pins
moist_sens_pins = [21] # 27 is not allowed ,19,21,23

off = 1
on = 0

# water level printing
water_levels = []

#global pump_relay_pin
GPIO.setup(pump_relay_pin, GPIO.OUT)
GPIO.output(pump_relay_pin, off)

#global moist_relay_pin
GPIO.setup(moist_relay_pin, GPIO.OUT)
GPIO.output(moist_relay_pin, on)

#global moist_sens_pins
for pin in moist_sens_pins:
    GPIO.setup(pin, GPIO.IN)

#GPIO Pins zuweisen
GPIO_TRIGGER = 10
GPIO_ECHO = 8
 
#Richtung der GPIO-Pins festlegen (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

servo_state = -1
    
def Pump_switch(value):
    print("PUMP ", value)
    global pump_relay_pin
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pump_relay_pin, GPIO.OUT)
    GPIO.output(pump_relay_pin, value)
    if value == on:
        pump_on['state']='disabled'
        pump_off['state']='normal'
    elif value == off:
        pump_on['state']='normal'
        pump_off['state']='disabled'

def Read_CPU_temp():
    global temp_CPU
    temp_file = open('/sys/class/thermal/thermal_zone0/temp')
    temp_CPU_ = temp_file.read()
    temp_file.close()
    temp_CPU = int(temp_CPU_)/1000
    
def Read_moisture():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(moist_relay_pin, GPIO.OUT)
    GPIO.output(moist_relay_pin, off)
    time.sleep(1) # probably not necessary
#    print("measuring...")
    #moist_sens_pins = [21] # 27 is not allowed ,19,21,23
    for pin in moist_sens_pins:
#        GPIO.setup(pin, GPIO.IN)
        GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    global wet
    wet = GPIO.input(moist_sens_pins[0])
    GPIO.output(moist_relay_pin, on)
    # print(wet)
#    if wet:
#        print("wet")
#    else:
#        print("dry")

def Read_water_level():
    global water_levels
    repeats = 100
    distances = []
    for i in range(repeats):
        # setze Trigger auf HIGH
        GPIO.output(GPIO_TRIGGER, True)
     
        # setze Trigger nach 0.01ms aus LOW
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGER, False)
     
        StartZeit = time.time()
        StopZeit = time.time()
        
        # speichere Startzeit
        while GPIO.input(GPIO_ECHO) == 0:
            StartZeit = time.time()
        
        # speichere Ankunftszeit
        while GPIO.input(GPIO_ECHO) == 1:
            StopZeit = time.time()
     
        # Zeit Differenz zwischen Start und Ankunft
        TimeElapsed = StopZeit - StartZeit
        # mit der Schallgeschwindigkeit (34300 cm/s) multiplizieren
        # und durch 2 teilen, da hin und zurueck
        distances.append((TimeElapsed * 34300) / 2)
        
        time.sleep(0.01)
    
    distance = round(sum(distances)/repeats, 1) # 36 -
    
    if distance < 28: # 25 min range of JSN-SR04T
        distance_perc = 100
    elif distance >= 28 & distance <= 60:
        distance_perc = (36-distance)*100/12.5
    else :
        distance_perc = 0
        
    
    #print(distance_perc)
    water_levels.append(distance_perc)
    # print(distance)
    if len(water_levels) > 10:
        water_levels.pop(0)
        
    #print(water_levels)
    for i in range(len(water_levels)):
        n = int(water_levels[i]*(40/100))
        print("="*n)
    
    # print ("distance = %.1f cm" % distance)
    
    return distance

def Check_values():
    
    if(temp_CPU > 75):
        print("CPU too warm.")
        temp_check_CPU = 2
    else:
        print("CPU temperature good.")
        temp_check_CPU = 1
        
def Correct_values():
    print("doing nothing....")
    

def ExitApplication():
    MsgBox = tk.messagebox.askquestion ('Exit Application','Quit automatic watering?',icon = 'warning')
    if MsgBox == 'yes':
        GPIO.cleanup()
        root.destroy()
        exit()
    else:
        tk.messagebox.showinfo('Return','The plants love you!')

def Run():
    start_animation['state']='disabled'
    Loop_thread = threading.Thread(target=Loop)
    Loop_thread.start()
    
def Loop():
    while True:
        
        # read moistures
        Read_moisture()
        
        # read CPU temp
        Read_CPU_temp()
        
        # read water tank level
        distance = Read_water_level()
        
        print(temp_CPU) # , wet , temp_CPU
        # check if values are in line with desired values
        Check_values()
        
        Correct_values()
        
        # check time and water plants twice a day
        print(strftime("%Y-%m-%d %H:%M:%S", localtime()))
        hour = int(strftime("%H", localtime()))
        minute = int(strftime("%M", localtime()))
        #print(hour, ":", minute)
        if hour == watering_clock_hour and minute <= watering_clock_minute and distance >= 0 and distance <= 50: # and minute < 2: #(interval/60):
            print("watering plants (morning)...")
            Pump_switch(on)
            time.sleep(watering_time)
            Pump_switch(off)
                
        # wait for interval seconds
        time.sleep(interval - time.time() % interval)
        

            
root = tk.Tk() 
root.title("Watering System v.0.1")

# Fixing the window size. 
# root.geometry(width=300, height=70) 
root.minsize(width=300, height=70) 
label = tk.Label(root, text="Greenhouse", fg="black", font="Verdana 14 bold") 
#label.pack()

start_animation = tk.Button(root, text='Start watering',  
width=20, state='normal', command=Run)

pump_on = tk.Button(root, text='PUMP on',  
width=10, state='normal', command=lambda: Pump_switch(on))

pump_off = tk.Button(root, text='PUMP off',  
width=10, state='normal', command=lambda: Pump_switch(off))

end = tk.Button(root, text='Exit', 
width=8, state='normal', command=ExitApplication)


r=0
start_animation.grid(row=r,column=0, columnspan = 2)
r+=1
pump_on.grid(row=r,column=0) 
pump_off.grid(row=r,column=1)
r+=1
end.grid(row=r,column=1)

pump_off['state']='disabled'
root.mainloop()

