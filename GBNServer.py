import time
from threading import Thread
import sys
import random
import hashlib
from os import curdir, sep, linesep
from random import randrange
import socket


# Thread for the server to send data 
class GBNServer(Thread):
    # Constructor to intialize the variables
    def __init__(self,Port_No,c_addr,filename):
        Thread.__init__(self)
        self.filename = filename
        self.host = 'localhost'
        self.sport = Port_No
        self.current_seqn = 0  # current sequence number be sent
        self.num_active = 0  # number of spaces filled in the sender window
        self.LAST_SENT_SEQN = -1  # Last sent sequence to the server
        self.sws = 7  # Sender Sindow Size
        self.window = [None] * self.sws  # list which will contain window
        self.last_acked_seqn = self.LAST_SENT_SEQN  # last acknowdgement recived
        # Starts the socket to listen to client
        self.client_address = c_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)  # Set Timeout as 5sec
        self.sock.bind((self.host, self.sport))
        self.window = [None] * 100
        self.flag = 0
        self.logf = 0
        print "  ***** New thread started for "+ str(self.client_address)



    # Function to return the check sum of the datagram
    def chsum(self, datagram):
        return str(datagram.split('||||')[0])

    # Function to return the window size of the datagram  
    def wsize(self, datagram):
        return str(datagram.split('||||')[2])

    # Function to check if the received check sum is equal to 
    # the check sum of the datagram received 
    def checkonchecksum(self,datagram):
        rwsize = self.wsize(datagram)
        chsum = self.chsum(datagram)
        nchsum = self.checkingsum(rwsize)
        if chsum == nchsum
            return True
        else
            return False

    # Function to make Chunks of Data
    def split(self, data, n):
        while data:
            yield data[:n]
            data = data[n:]

    # Condition to check If there is space available in Sender Window
    def canAddToWindow(self):
        return self.num_active < self.sws

    # Making a Datagram Packet for Sending
    def makeDatagram(self, seqno, packetdata):
        packetsize = len(packetdata)
        checksum = self.checkingsum(packetdata)
        return str(checksum) + '||||' + str(seqno) + '||||' + str(packetsize) + '||||' + str(packetdata)

    # Function to send Packets
    def sendDatagram(self, packet):
        i = random.randint(0, 30)
        if (i > 10):
            print 'Send Packet No.', self.seqno(packet)
            self.logf.write(str(time.time()) + " [c] " + str(self.seqno(packet)) + " Send" + '\n')
            self.sock.sendto(packet, self.client_address)
        else:
            print'Dropped Packet No.', self.seqno(packet)
            self.logf.write(str(time.time()) + " [c] " + str(self.seqno(packet)) + " Dropped \n")

    # Function to add packets to the window
    def addToWindow(self, byte):
        self.window[self.num_active] = byte
        self.LAST_SENT_SEQN = self.current_seqn
        self.current_seqn = (self.current_seqn + 1)
        self.num_active = self.num_active + 1
        self.sendDatagram(byte)

    # Function to calculate check sum of data
    def checkingsum(self,data):
        hash_md5 = hashlib.md5()
        hash_md5.update(data)
        return hash_md5.hexdigest()


    # Funtion to extract Packet No. from the datagram
    def seqno(self, datagram):
        return int(datagram.split('||||')[1])

    # Function to get the receiver window size
    def rwnd(self, datagram):
        return int(datagram.split('||||')[2])

    # Function to pop packets from Sender Window
    def removeFromWindow(self, datagram):
        index = 0
        self.window.pop(index)
        self.window.append(None)
        self.num_active = self.num_active - 1;
        self.last_acked_seqn = self.seqno(datagram)  # last ack sequence for logging

    # Function to check Acknowledgements
    def acceptAcks(self):
        try:
            datagram, address = self.sock.recvfrom(4096)
        except socket.timeout:
            print 'Connection timed out'
            self.logf.write(str(time.time()) + " [c] " + str(self.last_acked_seqn + 1) + " Timeout\n")
            return False
        print 'Received Ack No.', self.seqno(datagram)
        if self.seqno(datagram) == self.last_acked_seqn + 1:
            self.sws = self.rwnd(datagram)
            self.removeFromWindow(datagram)
            return True
        elif self.seqno(datagram) < self.last_acked_seqn + 1:
            return False
        # Handling Cumulative ACKs
        elif self.seqno(datagram) > self.last_acked_seqn + 1:
            self.sws = self.rwnd(datagram)
            self.counter = self.last_acked_seqn
            while (self.counter < self.seqno(datagram)):
                self.removeFromWindow(datagram)
                self.counter += 1
            return True

    # Function to Resend complete window
    def resendWindow(self):
        current = 0
        while (current < self.num_active):
            self.logf.write(str(time.time()) + " [c] " + str(self.seqno(self.window[current])) + " Retransmit\n")
            print 'Retransmit Packet No.', self.seqno(self.window[current])
            self.sock.sendto(self.window[current], self.client_address)
            current += 1

    # Function to send End of File message
    def sendEOF(self):
        self.sock.sendto('|!@#$%^&', self.client_address)

    # Function to manage flow of Data Packets
    def sendMessage(self, datalist, listlength):
        currentPacket = 0
        while (currentPacket < listlength or self.last_acked_seqn != listlength - 1):
            while (self.canAddToWindow() == True and currentPacket < listlength):
                datagram = self.makeDatagram(currentPacket, datalist[currentPacket])
                self.addToWindow(datagram)
                currentPacket += 1
            if (self.acceptAcks() == False):
                self.resendWindow()
        self.sendEOF()

    # Runnuing function of each thread    
    def run(self):
        try:
            f = open(self.filename, "rb")
            data = f.read()
            m = list(self.split(data, 512))
            f.close()
        except IOError:
            print 'File Unavailable'
        fName = 'serverLog.txt'
        self.logf = open(curdir + sep + fName, 'w+')
        self.sendMessage(m, len(m))
        self.logf.close()

Port_No = 60000
server_address = ('localhost',Port_No)
serversocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
serversocket.bind(('localhost', Port_No))
threads = []
senders = []
i = 0
print 'Server listening....'

while True:
    data , c_addr = serversocket.recvfrom(1024)
    print '******Got connection from', c_addr
    print'Server received : ', repr(data)
    data = data.split()
    spaces = '\n   ***Client Request : '
    #printing out the Request.
    #lw el data feeha 4 kalemat .
    if len(data) == 4:
        req = data[0]
        filename = data[1]
        hostname = data[2]
        portnumber = data[3]
        print spaces,req,filename,hostname,portnumber

    #lw el data feeha 3 kalemat .
    elif len(data) == 3:
        req = data[0]
        filename = data[1]
        hostname = data[2]
        print spaces,req,filename,hostname
    Port_No = randrange(30000, 50000)
    newthread = GBNServer(Port_No,c_addr,filename)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()
     
input()