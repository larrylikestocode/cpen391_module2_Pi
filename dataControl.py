import requests
import serial
from escpos.printer import Usb
import uuid
import requests
import time
import picamera
import pygame
from lineDistance import *



# define state
IDLE = 0
READ_DATA  = 1
SEND_DATA  = 2
PRINT_DATA = 3
START_CAM  = 4
DATA_LEN   = 23

# define Tag
#FIRST_NAME_T = b'F'
#LAST_NAME_T  = b'L'
#BIRTH_DATA_T = b'B'
#HEART_RATE_T = b'H'
#BLOOD_OXY_T  = b'O'
#BODY_TEM_T   = b'T'

FIRST_NAME_T = 70
LAST_NAME_T  = 76
BIRTH_DATA_T = 66
HEART_RATE_T = 72
BLOOD_OXY_T  = 79
BODY_TEM_T   = 84
SYMPTOMS_T   = 83
CAMERA_T     = 67  
TIME_T       = 71

# global variable
firstName = ""
lastName = ""
birthDate = "" 
heartRate = 0
bloodOxyGen = 0.0
temperature = 0.0
uId = ""
symptoms =""
height = 0
timeStamp = ""

# serial setup
ser = serial.Serial("/dev/ttyS0") #Open named port
ser.baudrate = 115200
ser.timeout = 5 
    

# printer setup
p = Usb(0x04b8, 0x0202)
p.set("left")

# https setup
SERVER_URL = "https://kiosk.391.cpen.jeffries.io/patients"


# camera module
camera = picamera.PiCamera()
FILE_NAME = 'photos/demo_pic.jpg'


# display window setup
green = (124,239,89)


# helper function
def parseData(data):
    i =2;
    j =0
    num_data ="" 
    while data[i] != 63:
        num_data = num_data+ chr(data[i])
        print(num_data)
        i = i+1        
    num = float(num_data)
    return num
            

def parseName(data):
    i = 2
    while data[i] !=63:
        i = i+1
    name = data[2:i] # TOCHECK
    return name.decode("utf-8")
    



def printHelper():
    global firstName
    global lastName
    global heartRate
    global bloodOxyGen
    global temperature
    global birthDate
    global symptoms
    global timeStamp
    global height
    p.text("HEALTHY STATUS SUMMARY\n")
    fNstr ="First Name   :     " + firstName +"\n" 
    lNstr ="Last Name    :     " + lastName + "\n"
    hRstr ="Heart Rate   :     " + str(heartRate) +" "+"BPM" +"\n"
    bOstr ="Blood Oxygen :     " + str(bloodOxyGen) +"%" +"\n"
    bTstr ="Temperature  :     " + str(temperature) +"C"+"\n"
    bDate ="Birth Date   :     " + birthDate[0:2] + "/" +birthDate[2:4]+"/"+birthDate[4:8] + "\n" #TODO add //
    bHeight="Height       :     " + str(round(height)) + "in." + "\n"
    bTime ="Check-In time:     "+ timeStamp + "\n"
    p.text(fNstr)
    p.text(lNstr)

    p.text("\n")

    p.text(hRstr)
    p.text(bOstr)
    p.text(bTstr)
    p.text(bDate)
    p.text(bHeight)
    p.text(bTime)
    p.set("center")
    p.text("\n")
    p.text("\n")
    uidUrl = "https://kiosk.391.cpen.jeffries.io/patients/" + uId;
    p.qr(uidUrl,True)
    p.image("hospitalLogo.jpg")
    p.text("\n")
    p.text("\n")
    p.text("\n")
    p.text("\n")
    p.cut()

def takePhotoHelper():
    global camera
    camera.resolution =(1600,700)
    camera.start_preview()
    time.sleep(8)
    camera.capture(FILE_NAME)
    camera.stop_preview()


def printText(txtText, font, size, x,y,color):
    #
    pygame.init()
    screen = pygame.display.set_mode((400,300))
    pygame.display.set_caption("Hospital")
    setFont = pygame.font.SysFont(font,size)
    label   = setFont.render(txtText, 1,color)
    screen.blit(label,(x,y))
    pygame.display.flip()
    time.sleep(3)
    pygame.display.quit()
    pygame.quit()



    
# state transition function 
def idle_state():
    start = ser.read(1)
    print(start)
    if(start == b'1'):# global variable
        ser.write(bytes("1",'UTF-8'))
        return START_CAM
    elif start == b'2':
        ser.write(bytes("1",'UTF-8'))
        return READ_DATA
    else:
        return IDLE




def camera_state():
    global height
    start = ser.read(1)
    print(start)
    if(start != b'C'):# global variable
        return IDLE
    else:
        takePhotoHelper()
        height = cameraModule(FILE_NAME)
        printText("Your Height is " +str(round(height)),"MS Comic Sans",40,60,10,green)
        ser.write(bytes("1",'UTF-8'))
#        print("the height string is " +heightStr )
        return IDLE






# TODO INCOMPLETE NEED To parse the data     
def read_state():
    data = ser.read(DATA_LEN)
    print("the received data is")
    print(data)
    print("data 0 is")
    print(data[0])
    global firstName
    global lastName
    global heartRate
    global bloodOxyGen
    global temperature
    global birthDate
    global symptoms
    global timeStamp

#    print("the first name is " + firstName)
#    print("the last name is " + lastname)
#    print("the heartrate is" + str(heartRate))
#    print("the oxygen is" + str(bloodOxyGen))
#    print("the temperature is " + str(temperature))
    if data[0] == FIRST_NAME_T:
        #
        firstName = parseName(data)
        ser.write(bytes("1",'UTF-8'))
        print("first name is " + firstName)
        return READ_DATA

    elif data[0] == LAST_NAME_T:
        #
        lastName = parseName(data)
        ser.write(bytes("1",'UTF-8'))
        print("last name is " + lastName)
        return READ_DATA

    elif data[0] == BIRTH_DATA_T:
        #
        # TODO ASK FOR BIRTHDAY TYPE DDMMYYYY
        birthDate = parseName(data)
        print("state birthDate is " + birthDate)
        ser.write(bytes("1",'UTF-8'))
        return READ_DATA

    elif data[0] == HEART_RATE_T:
        #
        heartRate = int(parseData(data))
        ser.write(bytes("1",'UTF-8'))
        print("the heartrate is " + str(heartRate))
        return READ_DATA

    elif data[0] == BLOOD_OXY_T:
        #
        bloodOxyGen = parseData(data)
        ser.write(bytes("1",'UTF-8'))
        return READ_DATA
    
    elif data[0] == SYMPTOMS_T:
        symptoms = parseName(data)
        ser.write(bytes("1",'UTF-8'))
        return READ_DATA

    elif data[0] == TIME_T:
        timeStamp = parseName(data)
        ser.write(bytes("1",'UTF-8'))
        return  READ_DATA        
        
    elif data[0] == BODY_TEM_T:
        #
        temperature = parseData(data)
        ser.write(bytes("1",'UTF-8'))
        return SEND_DATA
    else:
        ser.write(bytes("0",'UTF-8'))        
        return IDLE


def send_state():
    global firstName
    global lastName
    global heartRate
    global bloodOxyGen
    global temperature
    global uId
    global height
    global symptoms
    uId = str(uuid.uuid4())
    headers = {'Authorization':'Bearer db7ca5d78326750ff353a7d8c0724598b0b51161858d1c201d7cebb0e87d943c3031480864dc1af4df7bcb4f3953f52405af0a332d399a39e7d13df084b3cab39fd7858f70cacf79ae59467cb5a39649eaf3356eff2f0ca61179'}
    payload = {'spo2':str(bloodOxyGen), 'heart_rate':str(heartRate), 'temperature':str(temperature), 'given_name':firstName,'family_name':lastName, 'birth_date':birthDate, 'uuid':uId, 'symptoms':symptoms,'height': round(height)}
    r = requests.post(SERVER_URL,json = payload, headers = headers)
    print(r.text)




# Initially wait for the start bit 
state = IDLE; # 0 for idle
while True:
    if state == IDLE:
        # check for update
        state = idle_state()
        print("current state IDLE")
    elif state == START_CAM:
        # check for update
        state = camera_state()
        print("current state START_CAM")
    elif state == READ_DATA:
        # check for update
        state = read_state()
        print("current state READ_DATA")
    elif state == SEND_DATA:
        # TODO https request
        state = send_state()
        state =PRINT_DATA 
        print("current state SEND_DATA")
    elif state == PRINT_DATA:    
        state = IDLE
        print("the first name is " + firstName)
        print("the last name is " + lastName)
        print("the heartrate is" + str(heartRate))
        print("the oxygen is" + str(bloodOxyGen))
        print("the temperature is " + str(temperature))
        print("the birthdate is" + birthDate)
        print("the symptoms is:" + symptoms)
        printHelper()
 #       print("current state PRINT_DATA" +birthDate)
    else:
        state = IDLE



