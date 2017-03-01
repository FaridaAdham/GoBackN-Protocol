import socket
import time
import sys
import random
import hashlib
from os import curdir, sep, linesep
from random import randrange
import socket

# Client class
class GBNClient:
    def __init__(self, host='localhost'):
        self.sendport = 0
        self.last_sent_ackn = -1  # Last acknownlegded sequence number
        self.expected_seqn = 0  # Expected packet sequence number
        self.N = 6  # Window size of the server
        self.num_active = 0  # Specifies the number of packets in window
        self.writeptr = 0  # Write pointer to write packets to file
        self.rwindow = [None] * self.N
        self.filetowrite =''
        # Starts the socket to listen to server
        self.server_address = 0
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        #self.sock.bind((host, sendport))
        self.counter = 0
        self.WholeData = ''


    
    # Function to receive data from server and write in log file
    def receiving(self):
        fName = 'clientLog.txt'
        self.logf = open(curdir + sep + fName, 'w+')
        self.receiveMessage()
        self.logf.close()


    # Function to return the check sum of the datagram
    def chsum(self, datagram):
        return str(datagram.split('||||')[0])

    # Function to check if the received check sum is equal to 
    # the check sum of the datagram received
    def checkonchecksum(self,datagram):
        rdata = self.data(datagram)
        chsum = self.chsum(datagram)
        nchsum = self.checkingsum(rdata)
        if chsum == nchsum
            return True
        else
            return False


    # Function to remove the Packet from Window
    def removeFromWindow(self, byte):
        index = self.rwindow.index(byte)
        self.rwindow[index] = None
        self.num_active = self.num_active - 1

    
    # Funtion to Return the sequence number of the datagram
    def seqno(self, datagram):
        return int(datagram.split('||||')[1])  # |||| is used as the delimiter between sequence number and data

    # Function to Return the data part of the datagram
    def data(self, datagram):
        return datagram.split('||||')[3]

    
    # Function to calculate check sum of data
    def checkingsum(self,data):
        hash_md5 = hashlib.md5()
        hash_md5.update(data)
        return hash_md5.hexdigest()
    
    # Function to Check to see if space is available in window to add new packet
    def canAddToWindow(self):
        return self.num_active < self.N

    # Function to create a datapacket to be sent
    def mkDatagram(self, seqno, winsize):
        winsize = str(winsize)
        checksum = self.checkingsum(winsize)
        return str(checksum) + '||||' + str(seqno) + '||||' + winsize  # acknowledges with variable window

    # Function to Add packets to the window
    def addToWindow(self, datagram):
        seqn = self.seqno(datagram)
        if (self.rwindow[seqn % self.N] == None):
            if (self.seqno(datagram) == self.expected_seqn):
                print 'Received Packet No.', self.seqno(datagram)
                self.logf.write(str(time.time()) + " [s] " + str(self.seqno(datagram)) + " Received\n")
                self.rwindow[seqn % self.N] = datagram
                self.num_active = self.num_active + 1
            elif (self.seqno(datagram) > self.expected_seqn):
                print 'Packet Added to window buffer', self.seqno(datagram)
                self.rwindow[seqn % self.N] = datagram
                self.num_active = self.num_active + 1
        # Discarding Existing packets
        else:
            print 'Already in window buffer', self.seqno(datagram)

    # Function to send acknowledgement to the server
    def sendAck(self, datagram, counter):
        self.last_sent_ackn = self.seqno(datagram) + counter
        if (counter == 0):
            print 'Sending Ack for Packet No.', self.seqno(datagram)
            self.sock.sendto(str(datagram), self.server_address)
            self.logf.write(str(time.time()) + " [s] " + str(self.seqno(datagram)) + " Ack\n")
        elif (counter > 0):
            print 'Sending CumulativeAck for Packet No.', self.seqno(datagram)
            self.sock.sendto(str(datagram), self.server_address)
            self.logf.write(str(time.time()) + " [s] " + str(self.seqno(datagram)) + " Ack\n")

    # Function to write the packets from window to file
    def MakeWholeData(self):
        self.WholeData = self.WholeData + str(self.data(self.rwindow[self.writeptr]))
        self.removeFromWindow(self.rwindow[self.writeptr])
        self.writeptr += 1
        if (self.writeptr >= self.N):
            self.writeptr = 0

    # Recieves the packets from server
    def receiveMessage(self):
        while 1:
            datagram, addr = self.sock.recvfrom(4096)
            self.server_address = addr
            # EOF sequence to stop the server
            counter = 0
            if (datagram == '|!@#$%^&'):
                with  open(self.filetowrite, 'wb') as f:
                    f.write(self.WholeData)
                    f.close()
                break
            # Add to window if there is space in window and if sequence number is excpected sequence
            elif self.seqno(datagram) == self.expected_seqn:
                if (self.canAddToWindow() == True):
                    self.addToWindow(datagram)
                    while (self.rwindow[(self.seqno(datagram) + counter) % self.N] != None):
                        self.MakeWholeData()
                        counter += 1
                    datagram = self.mkDatagram(self.expected_seqn + counter - 1, self.N)
                self.sendAck(datagram, counter - 1)
                if (counter == 0):
                    self.expected_seqn = self.expected_seqn + 1
                else:
                    self.expected_seqn = self.expected_seqn + counter
            else:
                # For Buffering out of order packets
                if (self.canAddToWindow() == True):
                    self.addToWindow(datagram)
            


# Main Function
if __name__ == '__main__':
    port = 60000
    address = ('localhost',port)
    csocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    print '  ****The Commands Syntax should be as follows :'
    print '             GET file-name source-host-name (source-port-number)'
    request = raw_input("  Request :  ")
    request_array = request.split()
    req = request_array[0]
    if  len(request_array) == 4 or len(request_array) == 3:
        #checks if the request method is only post or get nothing else.
        if req == 'GET' or req == 'get':
            filename_array = request_array[1]
            filename_array = filename_array.split('.')
            filename = filename_array[0] +'_received_from_server'
            filetosave = filename +'.' + filename_array[1]
            print filename
        else:
            #if the Request Method isn't get or post
            print '\n  ***Invalid Request Method !!***\n'
    else:
        print '\n  ***Invalid Request Method !!***\n'
    csocket.sendto(request,address)
    Port_No = randrange(30000, 50000)
    client = GBNClient()
    client.filetowrite = filetosave
    client.sendport = Port_No
    client.sock = csocket
    client.server_address = address
    client.receiving()

input()