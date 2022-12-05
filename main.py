import bson
from bson.codec_options import CodecOptions
import socket as sock
import collections
import struct
import datetime
import datetime
import time
import threading
import math
import lzma

client = None
sync_time = None

SERVER_IP = "44.194.163.69"
SERVER_PORT = 10001

dc = True

World = None
spawned = False
x = 0
y = 0

# If you don't know how to get them that's unfortunate...
coid = 'us-east-1:1e3cd066-5161-434a-ba7c-9efc63855277'
token = 'Ra1p5QAiRvScDoZKqHSC1jGc3eDBraxPb9o6nPVrscI='

worldName = 'kraksclear'

packetQueue = []

# start the bot
def Connect():
    global client, dc, spawned, World, SERVER_IP
    dc = False

    World = None
    spawned = False

    client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    print(f'Connecting to {SERVER_IP}')
    client.connect((SERVER_IP, SERVER_PORT))
    pushPacket({'ID': 'VChk', 'OS': 'WindowsPlayer', 'OSt': 3})
    sendAll()
    pushPacket({"ID": "gLSI"})
    return client


# Stops the bot from running
def Disconnect():
    global dc, client
    dc = True
    client.close()
    packetQueue.clear()
    client = None


# Reconnect if any errors
def Reconnect():
    print('RECONNECTING DUE TO AN ERROR!')
    Disconnect()
    Connect()


# redirect the ip the one pixel worlds requested
def Redirect(ip):
    global client
    Disconnect()
    global SERVER_IP
    SERVER_IP = ip
    print("redirecting to " + ip)
    Connect()


# add a packet to the queue
def pushPacket(packet):
    packetQueue.append(packet)


# Send all the packets and empty the queue
def sendAll():
    global client
    packet = {}
    i = 0
    for x in packetQueue:
        print('Client: ')
        print(x)
        packet[f'm{i}'] = packetQueue[i]
        i += 1
    packet["mc"] = len(packetQueue)
    pkt = bson.encode(packet)

    buf = bytearray(4 + len(pkt))
    buf[0:4] = struct.pack('<I', 4 + len(pkt))
    buf[4:] = pkt

    client.sendall(buf)
    packetQueue.clear()




# what the program must do when receiving a packet
def onPacket(data_received):
    global client, spawned, World, sync_time

    if not data_received:
        return
    else:
        try:
            packets = bson.decode(data_received)
        except:
            print("ERROR")
            Reconnect()
            return

        if packets['mc'] is None or packets['mc'] <= 0:
            return

        for i in range(packets['mc']):
            packet = packets[f'm{i}']
            print("Server:")
            print(packet)
            print(onWorld(), spawned)
            if onWorld() and spawned is False:
                spawned = True
                spawn_x = World["WorldStartPoint"]["x"] / 3.2
                spawn_y = World["WorldStartPoint"]["y"] / 3.2
                print(spawn_x, spawn_y)
                sendMove(spawn_x, spawn_y)

            pkt_id = packet["ID"]

            if pkt_id == 'VChk':
                pushPacket({"ID": "GPd", "CoID": coid, "Tk": token, "cgy": 877})

            elif pkt_id == 'OoIP':
                Redirect(sock.gethostbyname(packet["IP"]))

            elif pkt_id == 'GPd':
                pushPacket({"ID": "TTjW", "W": worldName, "Amt": 0})

            elif pkt_id == 'TTjW':
                pushPacket({"ID": "Gw", "eID": "", "W": worldName})

            elif pkt_id == 'GWC':

                World = bson.decode(lzma.decompress(data=packet["W"]))
                World["LoadTime"] = TimeStamp()

                pushPacket({"ID": "RtP"})

                sync_time = threading.Timer(2, SyncTimeTick)
                sync_time.start()

        sendAll()

def TimeStamp():
    return (datetime.datetime.utcnow().timestamp() * 10000) + 621355968000000000

def onWorld():
    global World
    if World is None:
        return False
    bob = TimeStamp() - World["LoadTime"] >= 2000
    print(f'ON WORLD {bob}')
    return bob

def sendMove(pos_x, pos_y):
    new_x = int(math.floor(pos_x * 3.2))
    new_y = int(math.floor(pos_y * 3.2))
    global x, y

    if x != new_x or y != new_y:
        buf = bytearray(8)
        buf[0:4] = new_x.to_bytes(4)
        buf[4:8] = new_y.to_bytes(4)
        print(buf)

        pushPacket({"ID": "mp", "pM": buf})

    pushPacket({"ID": "mP", "t": TimeStamp(), "x": pos_x, "y": pos_y, "a": 1, "d": 7})

    x = pos_x
    y = pos_y

    sendAll()

def SyncTimeTick():
    global dc, spawned, sync_time
    if dc is not True:
        pushPacket({"ID": "ST", "STime": TimeStamp()})
        sendAll()
        sync_time = threading.Timer(2, SyncTimeTick).run()


if __name__ == '__main__':
    Connect()
    while True:
        data = client.recv(4096 * 64)
        if not data:
            break
        onPacket(data[4:])
