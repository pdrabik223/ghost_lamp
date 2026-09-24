# ghost_lamp
ma a lamp for halloween

I hate that I have to re invent it every fucking time 

```py
    hal_pwr = Pin(15, Pin.OUT, value = 1)
    hal_sensor_pin = Pin(14, Pin.IN, Pin.PULL_UP)
```

             ┌───────[  ]───────┐
           1 │● GP0       VSYS ●│ 40 - LED STRIP PWR
           2 │● GP1       VBUS ●│ 39
           3 │● GND        GND ●│ 38 - LED STRIP GND
           4 │● GP2         EN ●│ 37
           5 │● GP3       3.3V ●│ 36
           6 │● GP4    ADC REF ●│ 35
           7 │● GP5       GP28 ●│ 34
           8 │● GND        GND ●│ 33
           9 │● GP6       GP27 ●│ 32
          10 │● GP7       GP26 ●│ 31
          11 │● GP8  RUN/RESET ●│ 30
          12 │● GP9       GP22 ●│ 29
          13 │● GND        GND ●│ 28
          14 │● GP10      GP21 ●│ 27
          15 │● GP11      GP20 ●│ 26
          16 │● GP12      GP19 ●│ 25
          17 │● GP14      GP18 ●│ 24
HAL GND - 18 │● GND        GND ●│ 23   
HAL PWR - 19 │● GP14      GP17 ●│ 22    
HAL SIG - 20 │● GP15      GP16 ●│ 21 - LED STRIP DATA
             └──────────────────┘
