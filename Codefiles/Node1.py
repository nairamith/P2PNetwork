import socketio
import random
import eventlet
from threading import Thread, Event
import socket

IP = "localhost"
thread = Thread()
thread_stop_event = Event()


purpose = "F"
is_super = 0
supernode = ""
port = 5001

host = "http://" + IP + ":" + str(port)

sio_client = socketio.Client()
sio_server = socketio.Server()

app = socketio.WSGIApp(sio_server, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})


@sio_client.event
def connect():
    print('connection established')
    # sio.start_background_task(sendMessage())

@sio_client.event
def disconnect():
    print('disconnected from server')

# def sendMessage():
#     while 1:
#         print("Sending Message")
#         sio_client.emit('SensorReading', {'speed': str(random.random())})
#         sio_client.sleep(5)


# Request to ask from controller for list of supernodes
def request_supernodes():
    sio_client.connect('http://localhost:5000')
    sio_client.emit('request_supernodes', purpose)
    sio_client.disconnect()


# The cluster list as response from controller. A response to the request request_supernodes
@sio_server.event
def cluster_list(sid, data):
    print("Received ", data, "from ", sid)


# Request to register as supernode
def register_supernode():
    print("IS socket connected", sio_client.connected)
    sio_client.connect('http://localhost:5000')
    sio_client.emit('supernode_registration', {'ID': host, 'purpose': purpose})


# Response to supernode registration
@sio_server.event
def registration_response(sid, data):
    is_super = data["is_super_node"]
    print("I am Super")



# Request to ask from controller for list of supernodes
def register():
    print("=======================================================")
    print("Registering on controller")
    print("=======================================================")
    sio_client.connect('http://localhost:5000')
    sio_client.emit('register', {"purpose": purpose, "id": host})
    # sio_client.disconnect()


@sio_server.event
def cluster_info(sid, data):
    is_super = data["is_super"]
    supernode = data["supernode"]
    print("=======================================================")
    print("Assigned ", supernode, "as super_node")
    print("=======================================================")




def serve_app(_sio, _app):
    app = socketio.Middleware(_sio, _app)
    eventlet.wsgi.server(eventlet.listen(('', port)), app)


thread = Thread(target=serve_app, args=(sio_server, app))
thread.daemon = True
thread.start()
# request_supernodes()
# register_supernode()
register()
