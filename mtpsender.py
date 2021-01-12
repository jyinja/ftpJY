## import (add more if you need)
import threading
import unreliable_channel
import socket
import sys
import zlib #source: https://www.kite.com/python/examples/1939/zlib-generate-a-crc-checksum-and-check-it-after-decompression
import select

## we will need a lock to protect against concurrent threads
lock = threading.Lock()
seq = 0
univCS=""#universal checksum for checksum checking
window = []#array that we will add seqnum of packets to
lastackseq = -1 #last ack seq num
dup_ack_count = 0
window_base=0
window_size = sys.argv[3]

for j in range(int(sys.argv[3])): #set up initial window
    window.append(str(j)+"(1)")
##make DATA packets for sender
def create_packet(ptype,seqnum,leng,datamsg):
    # Two types of packets, data and ack
    # crc32 available through zlib library

    #packettype = ptype
    #next_seq_number = seqnum
    #length = leng
    strng = ""
    strng = strng + str(ptype)+" "+str(seqnum)+" "+str(leng)+" "
    checksum = zlib.crc32(datamsg.encode() ) #some data parameter has to go into the parenthesis here (the string of the data packet)
    print("cs "+str(checksum))
    strng = strng+str(checksum)[0:4] #take first 4 bytes of checksum
    ##headers.append(strng)
    strng = strng+"_._" #special character to separate header from data
    print("head "+strng)
    return strng

def receive_thread(sock,filep):
    try:
        global lastackseq#these are global
        global dup_ack_count
        global seq
        global window
        global univCS
        global window_base
        while True:
            #receive packet, but using our unreliable channel
            sock.settimeout(5)
            packet_from_server, server_addr = unreliable_channel.recv_packet(s)

            ##filep.write("Timeout for packet seqNum="+packet_from_server.decode().split(" ")[1]+"\n...\n")

            #call extract_packet_info
            ackmsg = packet_from_server.decode( )
            print("ackmsg "+ackmsg)
            #check for corruption, take steps accordingly
            filep.write("Packet received; type=ACK; seqNum="+ackmsg.split(" ")[1]+"; length=16; checksum_in_packet="+ackmsg.split(" ")[3][0:4]+";\nchecksum_calculated="+univCS+"; status=")
            if ackmsg.split(" ")[3][0:4]==univCS:
                filep.write("NOT_CORRUPT;\n...\n")
            else:
                filep.write("CORRUPT;\n...\n")
            if lastackseq == -1:
                lastackseq = int(ackmsg.split(" ")[1])
                #filep.write("last ack seqnum: "+str(lastackseq) )
            elif lastackseq == int(ackmsg.split(" ")[1]):
                dup_ack_count = dup_ack_count+1
            elif lastackseq!=int(ackmsg.split(" ")[1]):
                dup_ack_count = 0 #reset duplicate ack count variable
                lastackseq = int(ackmsg.split(" ")[1])#set up new last ack pack seq val
                #filep.write("elif, last ack seqnum: "+str(lastackseq) )
            #update window size, timer, triple dup acks
            filep.write("Updating window;\n#show seqNum of "+sys.argv[3]+" packets in the window with one bit status (0: sent & acked, 1: not sent)\n")
            filep.write("Window state: "+str(window[window_base:window_base+int(sys.argv[3])]) +"\n...\n")#prints out window state from base zero up to index specified on command line
            #window_base = window_base+1
            window.append(str(window_base+int(sys.argv[3]))+"(1)")
            if(dup_ack_count >= 3):
                filep.write("Triple dup acks received for packet seqNum="+ackmsg.split(" ")[1]+"\n...\n")
                dup_ack_count = 0#reset
    except socket.timeout:
        print("receive_thread: timeout")
        filep.write("Timeout for packet seqNum="+str(seq)+"\n...\n")

if (len(sys.argv)!=6):
    print("Either not enough arguments or too many arguments. Program requires receiver IP, receiver Port, window size, input file name, sender log file name. Program ending...")
    sys.exit()
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)



host =sys.argv[1]
port = int(sys.argv[2])
buf =1472#originally 1024, 1472 bytes is mtp header plus the data so the data we read needs to be slightly less so that we can also send header
addr = (host,port)
##MOVEDseq = 0
##s.bind(addr) #for some reason bind causes an error
logging = open(sys.argv[5],"w")
#start receive thread (this code was given)
recv_thread = threading.Thread(target=receive_thread,args=(s,logging,)) #originally target=rec_thread but changed to target=receive_thread and the args is s (s is client socket)
recv_thread.start()##possibly need to continuously receive

#header format is going to be like '0_seq_leng_checksum_._'


file_name=sys.argv[4]

#s.sendto(file_name,addr)
buff = 1472-20-10#minus 20 for header and 10 for possible corruption!
f=open(file_name,"r")

data = f.read(buff).strip()
##buff =1472-len(create_packet(0,seq,1472,data ))#allocated bytes for header
h=create_packet(0,seq,1472,data)#h is the header which will attach onto our read data
##print(str(seq)+"----"+data)
while (data):
    try:
        ##s.sendto(data.encode(),addr)
        while seq!=lastackseq: #originally dup_ack_count<3 and seq!=lastackseq, while not reached triple duplicate ack and also the last ack seqnum does not match the seqnum, then continuously send packet
            unreliable_channel.send_packet(s,str(h+data).encode(),addr)
            logging.write("\nPacket sent; type=DATA; seqNum="+h.split(" ")[1]+"; length=1472; checksum="+h.split(" ")[3][0:4]+"\n...\n")
            univCS = h.split(" ")[3][0:4]
            if not h.split(" ")[1]+"(0)" in window:
                window.pop(int(h.split(" ")[1]))
                #window.append(h.split(" ")[1]+"(0)")
                window.insert(int(h.split(" ")[1]), h.split(" ")[1]+"(0)")
            print ("sending...seq:"+str(seq)+" lack ack seq:"+str(lastackseq))

        data = f.read(buff).strip()
        seq = seq+1#increment for next seq num
        h=create_packet(0,seq,1472,data)#h is the header which will attach onto our read data

        ##print(str(seq)+"----"+data)

    except socket.timeout:
        s.close()
        f.close()
        logging.write("Timeout for packet seqNum="+h.split(" ")[1]+"\n...\n")
        logging.close()

print("closed")
