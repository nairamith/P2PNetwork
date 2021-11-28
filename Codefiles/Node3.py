import time

import socketio
import random
import eventlet
from threading import Thread, Event
import csv

IP = "localhost"
thread = Thread()
thread_stop_event = Event()

thread_sensor = Thread()

purpose = "T"
lane = 1
is_super = 0
supernode = ""
speed_dict = {}
supernodes = {}

platoon_speed = -1
port = 5003

host = "http://" + IP + ":" + str(port)
controller = "http://localhost:5000"

sio_client_controller = socketio.Client()
sio_client_supernode = socketio.Client()
sio_server = socketio.Server()

app = socketio.WSGIApp(sio_server, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})


@sio_client_controller.event
def connect():
    print('connection established')


@sio_client_controller.event
def disconnect():
    print('disconnected from server')


# Request to register
def register():
    print("=======================================================")
    print("Registering on controller")
    print("=======================================================")
    sio_client_controller.connect(controller)
    sio_client_controller.emit('register', {"purpose": purpose, "id": host, "lane": lane})
    sio_client_controller.sleep(2)


# Response from the controller for the registration
@sio_server.event
def cluster_info(sid, data):
    global is_super
    global supernode
    is_super = data["is_super"]
    supernode = data["supernode"]
    print("=======================================================")
    print("Assigned ", supernode, "as super_node")
    print("Moving to lane: ", data["lane"])
    print("=======================================================")


@sio_server.event
def SensorReading(sid, data):
    speed_dict[data["host"]] = data["speed"]


@sio_server.event
def supernodes(sid, data):
    supernodes = data
    print(supernodes)


# Function to start listening on the given post
def serve_app(_sio, _app):
    app = socketio.Middleware(_sio, _app)
    eventlet.wsgi.server(eventlet.listen(('', port)), app)


# Function to Emit sensor details to super node
def send_message():
    print("Sending sensor info To SuperNode")
    file = open("./data/Node1.csv")
    csv_reader = csv.reader(file)
    sio_client_supernode.connect(supernode)
    print("=======================================================")
    print("Sending Sensor info to supernode", supernode)
    print("=======================================================")
    for row in csv_reader:
        x = row[0]
        y = row[1]
        speed = row[2]
        radarF = row[3]
        radarB = row[4]
        radarL = row[5]
        radarR = row[6]
        oxygen = row[7]
        if platoon_speed >= 0:
            speed = platoon_speed
        if not is_super:
            sio_client_supernode.emit('SensorReading', {'speed': str(speed), 'radarF': radarF,
                                                        "radarB": radarB, "radarL": radarL,
                                                        "radarR": radarR, "oxygen": oxygen,
                                                        "host": host})
        else:
            speed_dict[host] = speed


# Function to start a thread to start sending message
def get_sensor_info():
    thread_sensor = Thread(send_message())
    thread_sensor.daemon = True
    thread_sensor.start()


thread = Thread(target=serve_app, args=(sio_server, app))
thread.daemon = True
thread.start()

register()

get_sensor_info()


def send_agg_cluster_info():
    while 1:
        cluster_speed = sum([int(x) for x in speed_dict.values()]) / len(speed_dict)
        sio_client_controller.emit("heart_beats", {"id": host, "cluster_speed": cluster_speed,
                                                   "cluster_count": len(speed_dict)})
        time.sleep(10)


if is_super:
    thread_controller = Thread(target=send_agg_cluster_info)
    thread_controller.daemon = True
    thread_controller.start()

while 1:
    ""
# print(speed_dict)
# print(sum([int(x) for x in speed_dict.values()])/len(speed_dict))