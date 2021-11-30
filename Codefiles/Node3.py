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


purpose = "Y"
lane = 1
is_super = 0
supernode = ""
speed_dict = {}
supernodes = {}
stop_flag=0

platoon_speed = -1
port = 33003

host = "http://" + IP + ":" + str(port)
controller = "http://localhost:33000"


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


@sio_server.event
def cluster_speed(sid, data):
    global platoon_speed
    platoon_speed = data["speed"]
    print("=============Received cluster regulation of ", data["speed"], "=======================")
    control_node_speed()


@sio_server.event
def regulated_speed(sid, data):
    global platoon_speed
    global stop_flag
    print("Received regulation from supernode with speed", data["speed"])
    platoon_speed = data["speed"]
    if data["speed"] == 0:
        stop_flag = 2


# Get list of supernodes
@sio_server.event
def supernodes(sid, data):
    global supernodes
    supernodes = data
    print("=================Received Supernodes list====================")
    print(supernodes)

# Response from the controller for the registration
@sio_server.event
def cluster_info(sid, data):
    global is_super
    global supernode
    global lane
    is_super = data["is_super"]
    supernode = data["supernode"]
    lane = data["lane"]
    if is_super:
        print("=======================================================")
        print("==============Assigned as super_node===================")
        print("===============Moving to lane: ", data["lane"],"==========")
        print("=======================================================")
    else:
        print("=======================================================")
        print("Assigned ", supernode, "as super_node")
        print("Moving to lane: ", data["lane"])
        print("=======================================================")


# Get reading from peers. Only in case of a supernode
@sio_server.event
def SensorReading(sid, data):
    print("==========Recieved sensor reading from ", data["host"], "==============")
    print(data)
    speed_dict[data["host"]] = data["speed"]


@sio_server.event
def turn(sid, data):
    global platoon_speed
    direction = data["direction"]
    turn_lane = data["lane"]
    print(data)
    if (direction == "Left" and lane < turn_lane) or (direction == "Right" and lane > turn_lane):
        print("============================================================")
        print("============Waiting for other platoon to turn left==========")
        platoon_speed = 0
        control_node_speed()


def control_node_speed():
    for k,v in speed_dict.items():
        if k != host:
            sio_client_supernode.connect(k)
            sio_client_supernode.emit("regulated_speed", {"speed": platoon_speed})
            time.sleep(2)
            sio_client_supernode.disconnect()


# Request to register
def register():
    print("=======================================================")
    print("=============Registering on controller=================")
    print("=======================================================")
    sio_client_controller.connect(controller)
    sio_client_controller.emit('register', {"purpose": purpose, "id": host, "lane": lane})
    sio_client_controller.sleep(2)


# Function to Emit sensor details to super node
def send_message():
    global stop_flag
    file = open("./data/test_node3.csv")
    csv_reader = csv.reader(file)

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
        print("Stop flag is ", stop_flag)
        if stop_flag > 0:
            speed = 0
            stop_flag -= 1
        if not is_super:
            print("==============================================================")
            print("========Sending Sensor info to supernode", supernode, "=======")
            print("==============================================================")
            sio_client_supernode.connect(supernode)
            sio_client_supernode.emit('SensorReading', {'speed': str(speed), 'radarF': radarF,
                                                        "radarB": radarB, "radarL": radarL,
                                                        "radarR": radarR, "oxygen": oxygen,
                                                        "host": host})
            time.sleep(2)
            sio_client_supernode.disconnect()
        else:
            speed_dict[host] = speed
        time.sleep(3)
    if is_super:
        print(supernodes)
        for peer_supernode in supernodes:
            if peer_supernode["supernode"] != host:
                print("--------------------------------------------------")
                print("Sending turn directions to peer super nodes", peer_supernode["supernode"])
                sio_client_supernode.connect(peer_supernode["supernode"])
                sio_client_supernode.emit("turn", {"direction": "Left", "lane": lane})
                time.sleep(0.5)
                sio_client_supernode.disconnect()


# Function to start a thread to start sending sensor details
def get_sensor_info():
    thread_sensor = Thread(send_message())
    thread_sensor.daemon = True
    thread_sensor.start()


# Function to send aggregated cluster details to the controller.
def send_heartbeats():
    while 1:
        if is_super:
            print("==================================================================")
            print("=======================Sending heartbeat==========================")
            print("==================================================================")
            cluster_speed = sum([int(x) for x in speed_dict.values()]) / max(len(speed_dict),1)
            sio_client_controller.emit("heart_beats", {"id": host, "cluster_speed": cluster_speed,
                                                       "cluster_count": len(speed_dict)})
            time.sleep(10)


thread_controller = Thread(target=send_heartbeats)
thread_controller.daemon = True
thread_controller.start()

# Function to start listening on the given post
def serve_app(_sio, _app):
    app = socketio.Middleware(_sio, _app)
    eventlet.wsgi.server(eventlet.listen(('', port)), app)


thread = Thread(target=serve_app, args=(sio_server, app))
thread.daemon = True
thread.start()



register()

get_sensor_info()




while 1:
    ""
    # print(platoon_speed)
# print(speed_dict)
# print(sum([int(x) for x in speed_dict.values()])/len(speed_dict))
