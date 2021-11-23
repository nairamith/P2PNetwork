import socketio
import random

sio = socketio.Client()

@sio.event
def connect():
    print('connection established')
    sio.start_background_task(sendMessage())


def sendMessage():
    while 1:
        print("Sending Message")
        sio.emit('SensorReading', {'speed': str(random.random())})
        sio.sleep(5)

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('http://localhost:5000')
sio.wait()