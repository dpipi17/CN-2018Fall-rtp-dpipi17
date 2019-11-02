import sys
import getopt

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.sackMode = sackMode
        self.debug = debug

    # Main sending loop.
    def start(self):
      # add things here

        # HandShake
        firstAck = b''
        for _ in range(0,60):
            
            hello = self.make_packet('syn', 0, '')
            self.send(hello)
            firstAck = self.receive(1)
            
            if firstAck is None:
                continue

            break
    
        if not firstAck:
            return
        

        # Split Packet
        seqNum = 1
        data = self.infile.read()
        dataDict = dict()

        key = 1
        currIndex = 0
        chunkSize = 1400
        while True:     
            currData = b''
            if currIndex + chunkSize < len(data):
                dataDict[key] = (data[currIndex : currIndex + chunkSize], False)
            else:
                dataDict[key] = (data[currIndex:], False)
                break
            
            currIndex += chunkSize
            key += 1
        
        
        # Send Data
        while True:
            if seqNum > key:
                break
            
            for packetInd in range(seqNum, min(seqNum + 7, key) + 1):
                if not dataDict[packetInd][1]:
                    currPacketDat = dataDict[packetInd][0]
                    message = self.make_packet('dat', packetInd, currPacketDat)
                    
                    self.send(message)

            recievedMessages = []
            counterDict = dict()
            flag = False

            while True: 
                
                if flag:
                    break

                recievedMessage = self.receive(0.5)
                if recievedMessage is None:
                    break

                if Checksum.validate_checksum(recievedMessage):
                    splittedPac = self.split_packet(recievedMessage)
                    recievedMessages.append(splittedPac)


                    if splittedPac[0] == 'ack':
                        pacNum = splittedPac[1]
                        if pacNum in counterDict:
                            counterDict[pacNum] = counterDict[pacNum] + 1
                        else:
                            counterDict[pacNum] = 1

                        if counterDict[pacNum] >= 4:
                            seqNum = int(pacNum)
                            flag = True

            if flag:
                continue
            
            for msg in recievedMessages:
                if msg[0] == 'sack':
                    selAckArr = msg[1].split(';')

                    sentPackets = []
                    seqNum = max(seqNum, int(selAckArr[0]))
                    
                    if len(selAckArr) > 1 and selAckArr[1] != '':
                        selAckArrSecond = selAckArr[1].split(',')

                        for ack in selAckArrSecond:
                            if ack != '':
                                sentPackets.append(int(ack))

                        for pacInd in sentPackets:
                            dataDict[pacInd] = (dataDict[pacInd][0], True)

                else:
                    seqNum = max(seqNum, int(msg[1]))
                
             
        # say goodbye
        bye = self.make_packet('fin', seqNum, '')
        self.send(bye)



        
'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"
        print "-k | --sack Enable selective acknowledgement mode"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest,port,filename,debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
