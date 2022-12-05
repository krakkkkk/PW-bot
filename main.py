import bson
from bson.codec_options import CodecOptions
import socket as sock
import collections, struct
import datetime
import datetime, time, threading

client = None
synctime = None

SERVER_IP = "44.194.163.69"
SERVER_PORT = 10001

logintokens = None

# If you don't how to get them that's unfortunate..
coid = 'your coid'
token = 'your token'

worldName = 'blackperson'

packetQueue = []

# start the bot
def Connect():
    global client
    client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    global SERVER_IP
    print (f'Connecting to {SERVER_IP}')
    client.connect((SERVER_IP, SERVER_PORT))
    pushPacket({'ID': 'VChk', 'OS': 'WindowsPlayer', 'OSt': 3})
    sendAll()
    pushPacket({ "ID": "gLSI" });
    return client

# Stops the bot from running
def Disconnect():
    global client
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
    packetCount = len(packetQueue)
    i = 0
    for x in packetQueue:
        print('Client: ')
        print(x)
        packet[f'm{i}'] = packetQueue[i]
        i += 1
    packet["mc"] = packetCount
    pkt = bson.encode(packet)
    
    
    buf = bytearray(4 + len(pkt))
    buf[0:4] = struct.pack('<I', 4 + len(pkt))
    buf[4:] = pkt
    
    client.sendall(buf)
    packetQueue.clear()

# what the program must do when receiving a packet
def onPacket(data):
    global client
    
    if not data:
        return
    else:
        try:
            packets = bson.decode(data)
        except:
            print("ERROR")
            Reconnect()
            return
    
        if packets['mc'] is None or packets['mc'] <= 0:
            return
    
        packetCount = packets['mc']
    
        print ("Server:")
        for i in range(packetCount):
            packet = packets[f'm{i}']
            print(packet)
        
            pktID = packet["ID"]
        
            if pktID == 'VChk':
                pushPacket({ "ID": "GPd", "CoID": coid, "Tk": token, "cgy": 877 })
            
            elif pktID == 'OoIP':
                Redirect(sock.gethostbyname(packet["IP"]))
            
            elif pktID == 'GPd':
                pushPacket({ "ID": "TTjW", "W": worldName, "Amt": 0 })
            
            elif pktID == 'GWC':
                global synctime
                synctime = threading.Timer(2, SyncTimeTick)
                synctime.start()
                pushPacket({ "ID": "RtP" })
            
            elif pktID == 'TTjW':
                pushPacket({ "ID": "Gw", "eID": "", "W": worldName })
            
        
        sendAll()

def TimeStamp():
    #epochTime = (datetime.datetime.utcnow().timestamp() - 621355968000000000) / 10000
    dateNow = (datetime.datetime.utcnow().timestamp() * 10000) + 621355968000000000
    return dateNow
    
def SyncTimeTick():
    print (TimeStamp())
    pushPacket({ "ID": "ST", "STime": TimeStamp() })
    sendAll()
    global synctime
    synctime = threading.Timer(2, SyncTimeTick).run()

if __name__ == '__main__':
    Connect()
    while True:
        data = client.recv(4096 * 248)
        if not data:
            break
        print(data)
        onPacket(data[4:])
