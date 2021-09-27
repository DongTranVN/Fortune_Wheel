from machine import Pin,UART, PWM
import utime
# Core 2 
import _thread

#-----Sensor_ban_dau-----#
Sensor_Quang = Pin(11, Pin.IN, Pin.PULL_UP)

#-----Coin-----#
# Chân Coin kết nối với interrupt
Coin = Pin(1, Pin.IN, Pin.PULL_UP)
CounterCoin = 0

#-----Encoder-----#
# Pin Encoder connect with interrupt GP0
Encoder = Pin(0, Pin.IN, Pin.PULL_UP)
CounterEncoder = 0
# Số vòng quay của Encoder
rotation2 = 0

#-----Mode play-----#
# Khi ở chế độ chơi, chân GP14 sẽ xuất mức cao, button Play nhấn sẽ ngắt kiểu Falling
# Khi Number_Coin > 0 thì kéo chân Control_Irq lên  mức cao
Control_Irq = Pin(14, Pin.OUT, value = 0)
# Biến dùng để check khi button Play nhấn.
Check_Play = 0
# Button connect interrupt
Button_Play = Pin(9, Pin.IN, Pin.PULL_UP)

#-----Biến Save Pluse từ Pi4 gửi về----- #
Pulse = 0
Save_Pulse = 0

#----- Uart ----- #
# declare UART 0
uart0 = UART(0, baudrate=9600, tx=Pin(12), rx=Pin(13))
rxPulse = ""
rxPulse1 = ""
Cut_rxPulse = ""
Save_Cut_rxPulse = 0

#----- Step-----#
# Vi bước 1/16 .3200 bước/ vòng
# Hướng quay của step : DIR
# Pul cấp xung cho Step.
# EN thả nổi chế độ enable
# Pin control direction Step
DIR = Pin(3, Pin.OUT)
# Direction Step
DIR.on()
# ----Pin PWM----#

#PUL = PWM(Pin(2))
#PUL.freq(1000)
PUL = Pin(2, Pin.OUT)
PUL.off()
# Số vòng quay của Step
rotation1 = 0

#-----Khai báo điểm, xung-----#
# Initialization list Pulse and list Point
Pulse_list = [160,320,480,640,800,960,1120,1280,1440,1600,1760,1920,2080,2240,2400,2560,2720,2880,3040, 3200]
Point_list = [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]
#Biến chạy
Index1 = 0
#Biến lưu điểm
Save_Point1 = 0
Save_Point2 = 0
Minus_Point = 0


#----- Gửi và nhận điểm từ NFC-----#
Pulse_NFC = 0
# Biến gửi điểm cho Pi4
txPoint_NFC= ""
A_main = Pin(7, Pin.OUT)
A_main.off()
S_main = Pin(8, Pin.IN, Pin.PULL_UP)

#----- Fix điểm lỗi-----#
Button_Fix = Pin(6, Pin.IN, Pin.PULL_UP)

#----Hàm check vị trí ban đầu khi khởi động------#
#def Sensor_Start():
while(Sensor_Quang.value() != 0):

    # Run Motor
    #PUL.duty_u16(52428)
    PUL.on()
    utime.sleep(1)
    PUL.off()
    utime.sleep(1)

    # Stop Motor
PUL.off()


#----- Interrupt khi có Coin----- #
def CoinStart(pin):
    # Khi ngắt
    global CounterCoin
    CounterCoin += 1
    print("Number_Coin=", CounterCoin)
    # Send Number_Coin lên Pi4
    #txData = b'Number_Coin\n\r'
    
    txCoin1 = 'Number_Coin:'
    uart0.write("Number_Coin:%d\n\r" % (CounterCoin))
    #txCoin2 = str(CounterCoin)
    #uart0.write(txCoin1)
    #utime.sleep(0.1)
    #uart0.write(txCoin2)
    #utime.sleep(0.1)
    #uart0.write("\n\r")
    
# interrupt when coin wire trigger, FALLING
Coin.irq(trigger = Pin.IRQ_FALLING, handler = CoinStart)

#----- Khi Coin > 0  ----- #
# Khi button Play nhấn, nhảy vào hàm ngắt.
def Bt_Play_Irq(pin):
    global Check_Play 
    Check_Play = 1
# Ngắt khi nhấn Button 
Button_Play.irq(trigger = Pin.IRQ_FALLING, handler = Bt_Play_Irq)


    
#----- Interrupt khi có Encoder-----#
def Counter_Encoder(pin):
    global CounterEncoder, rotation2
    CounterEncoder += 1
    # 3200 pulse/ rotation
    if(CounterEncoder >= 3200):
    # Nếu vòng quay < 14 
        if(rotation2 < 14):
            rotation2 += 1
            CounterEncoder = 0
        elif(rotation2 >= 14):
            rotation2 = 0
            CounterEncoder = 0
#  Interrupt đếm xung          
Encoder.irq(trigger = Pin.IRQ_FALLING, handler = Counter_Encoder)

            
#----- Core 2 Uart_Receive -----#
def Uart():
    global rxPulse, rxPulse1
    while True:
        print("Core 2 ")
        if uart0.any() > 0:
            # Pi4 send data with syntax : "Xung:1000"
            rxPulse1  = uart0.readline()
            rxPulse = rxPulse1  
        print(rxPulse)
        #Clear buffer
        rxPulse1 =""

_thread.start_new_thread(Uart, ())

    

#---- Hàm gửi xung Encoder lên Pi4----#                  
def Send_Pulse_to_Pi4(CounterEncoder):
    txEncoder = ""
    txEncoder = str(CounterEncoder)
    uart0.write("Encoder_Pulse:%s \n\r" % (txEncoder))
    
# -----Hàm tính điểm-----#
def Score(Pulse):
    global Index1, Save_Point1, Save_Point2
    global Pulse_list, Point_list
    # Scoring from Pulse of Pi4.        
    Index1 = (Pulse_list.index(Pulse))
    
    Save_Point1 = Point_list[Index1]
    print(Save_Point1)
    # Kéo chân A.main()
    A_main.value(1)
    if(Save_Point2 > 0):
        Save_Point2 = Save_Point1 + Minus_Point
        Minus_Point = Minus_Point + Save_Point1
    elif(Save_Point2 == 0):
        Save_Point2 = Save_Point1
        Minus_Point = Save_Point1
    
#-----Function play-----#
def Play():
    print("Function Play")
    global CounterCoin, Check_Play, rxPulse,  Cut_rxPulse, rotation1, Save_Pulse, Pulse, CounterEncoder

    while(CounterCoin > 0):
        Control_Irq.on()
        utime.sleep(2)
        # When push button start
        if(Check_Play == 1):
            #Tắt điều kiện ngắt button start
            Control_Irq.off()
            #Send request Point to Pi4
            txNumber_Point = "Number_Point\n\r"
            uart0.write(txNumber_Point)
            utime.sleep(2)
         
            # Data Point from Pi4 to Pico
            # Pi4 send data with syntax : Xung:1000
            if('Xung' in rxPulse):
                Cut_rxPulse = rxPulse[5: ]
                #Clear rxPulse
                #rxPulse =""
                Pulse = int(Cut_rxPulse)
                print(Pulse)
               
                # Run step
                # Khi bắt đầu quay ở vị trí khác tọa độ 0
                if(rotation1 >=14 and rotation1 <=15):
                    for i1 in range(3200 - Save_Pulse):
                        PUL.on()
                        utime.sleep(2)
                        PUL.off()
                        utime.sleep(2)
                        #PUL.duty_u16(52428)
                    rotation1 += 1  
                           
                # Khi quay tới vòng 15. Reset vòng về 0
                if(rotation1 >= 15):
                    rotation1 = 0
             
                # 65535 là tương đương 100% pulse width
                if(rotation1 < 14):
                    # Width = 80%
                    for i2 in range(14*3200):
                        PUL.on()
                        utime.sleep(2)
                        PUL.off()
                        utime.sleep(2)

                        #PUL.duty_u16(52428)
                        if(i2%3200==0):
                            rotation1 += 1
                    print(rotation1)
                      
                # Khi tới vòng quay > 14, tiến hành chạy tới số xung mà pi gửi về.
                if(rotation1 >= 14):
                    # 20% width
                    for i3 in range(Pulse):
                        PUL.on()
                        utime.sleep(4)
                        PUL.off()
                        utime.sleep(4)
                        #PUL.duty_u16(13107)
                # Lưu giá trị Pulse
                Save_Pulse = Pulse
                # Hàm gửi xung Encoder lên Pi4
                Send_Pulse_to_Pi4(CounterEncoder)
                #Hàm tính điểm
                Score(Pulse)
                # Gán biến  Check_Play = 0, kết thúc một lượt chơi 
                Check_Play = 0
                # minus number coin
                CounterCoin -=1
                if(CounterCoin <= 0):
                    CounterCoin = 0
                
#----- Ngắt khi nhận Pulse từ NFC-----#
def Smain_irq(pin):
    global Pulse_NFC,txPoint_NFC, Save_Point2, Minus_Point
    Pulse_NFC += 1
    Minus_Point -= 1

    if(Pulse_NFC <  Save_Point2):
        A_main.value(1)
    if(Pulse_NFC >= Save_Point2):
        A_main.value(0)
        Minus_Point = 0
        Pulse_NFC = 0
        Save_Point2 = 0
    uart0.write("Point_NFC:%d\n\r" % (Pulse_NFC))
S_main.irq(trigger = Pin.IRQ_FALLING, handler =  Smain_irq)

#----- Irq fix point-----#
def Fix_Point(pin):
    A_main.value(1)
    uart0.write("Fix_Point \n\r")
Button_Fix.irq(trigger = Pin.IRQ_FALLING, handler =  Fix_Point)

#----- Check xung -----#
def Check_Pulse():
    global rxPulse,  Cut_rxPulse, Pulse, rotation1, Save_Pulse, CounterEncoder
    # Pi4 send Pulse with syntax: Check:2000
    if ('Check' in rxPulse):
        Cut_rxPulse = rxPulse[6: ]
        #Clear rxPulse
        #rxPulse =""
        Pulse = int(Cut_rxPulse)
        print("Ham Check_Pulse:",Pulse)
        # Run step
        # Khi bắt đầu quay ở vị trí khác tọa độ 0
        if(rotation1 >=14 and rotation1 <=15):
            for i1 in range(3200 - Save_Pulse):
                PUL.on()
                utime.sleep(2)
                PUL.off()
                utime.sleep(2)
            rotation1 += 1
        # Khi quay tới vòng 15. Reset vòng về 0
        if(rotation1 >= 15):
            rotation1 = 0
        if(rotation1 < 14):
            for i3 in range(Pulse):
                PUL.on()
                utime.sleep(4)
                PUL.off()
                utime.sleep(4)
        Save_Pulse = Pulse
        # Send Pulse encoder to Pi4
        Send_Pulse_to_Pi4(CounterEncoder)

#----- Hàm Fix lỗi vị trí, nếu không đúng reset về trạng thái ban đầu------#
def Fix_Location():
    global CounterEncoder, rotation1, rotation2, Pulse, Save_Pulse
    # Khi bị lệch vị trí thì sẽ chạy về vị trí ban đầu
    if("Start" in rxPulse):
        while(Sensor_Quang.value() != 0):
            # Run Motor
            #PUL.duty_u16(52428)
            PUL.on()
            utime.sleep(1)
            PUL.off()
            utime.sleep(1)
    # Stop Motor
    PUL.off()
    CounterEncoder = 0
    rotation1 = 0
    rotation2 = 0
    Pulse = 0
    Save_Pulse = 0

while True:
    print("Mode normal")
    utime.sleep(2)
    print("Mode play game")
    Play()
    Check_Pulse()
    Fix_Location()


   



    
        
