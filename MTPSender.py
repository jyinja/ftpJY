## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more if you need)
import threading
import unreliable_channel
import socket
import sys
import zlib #source: https://www.kite.com/python/examples/1939/zlib-generate-a-crc-checksum-and-check-it-after-decompression
import select


## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.
# client_port
packettype = 'DATA'
next_seq_number = 0
length = 1472 #stated on end of page 1 of specs
checksum = 0#sets up checksum in create_packet
window_size = 0#gotten from command line arg
window_base = 0
dup_ack_count = 0
client_port = 0
timeout = 500
HEAD = {"type":hex(0x0000),"seqNum":hex(next_seq_number),"length":hex(length),"checksum":hex(checksum)} #HEAD dictionary stores attributes of the header and hex(0x0000) will be zero representing a DATA packet
packets=[]
headers=[]

## we will need a lock to protect against concurrent threads
lock = threading.Lock()

##make DATA packets for sender
def create_packet(ptype,seqnum,leng,datamsg):
    # Two types of packets, data and ack
    # crc32 available through zlib library

    #packettype = ptype
    #next_seq_number = seqnum
    #length = leng
    strng = ""
    strng = strng + ptype+" "+str(seqnum)+" "+str(leng)+" "
    checksum = zlib.crc32(datamsg.encode()) #some data parameter has to go into the parenthesis here (the string of the data packet)
    strng = strng+str(checksum)
    headers.append(strng)
    return 0

##extract ACK
def extract_packet_info(packet):
    # extract the packet data after receiving
    #test: print("goop:: "+packet)
    #print(packet.split(" | ")[0].split(" "))
    return packet.split(" | ")[0].split(" ")

def receive_thread(socket):
    while True:
        #receive packet, but using our unreliable channel
        try:
            socket.settimeout(timeout)
            packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
        except socket.timeout:
            f.write("Timeout for packet seqNum="+packet_from_server.decode()[1]+"\n...\n")

        #call extract_packet_info
        ackmsg = extract_packet_info(packet_from_server.decode( ))
        #check for corruption, take steps accordingly

        #update window size, timer, triple dup acks



def main():
    next_seq_numer = 0
    responsive = False
    if (len(sys.argv)!=6):
        print("Either not enough arguments or too many arguments. Program requires receiver IP, receiver Port, window size, input file name, sender log file name. Program ending...")
        sys.exit()
    #read command line args
    receiverIP = sys.argv[1] #sample like 127.0.0.1
    receiverPort = int(sys.argv[2]) #sample like 53161
    window_size = int(sys.argv[3])
    inputfile = sys.argv[4]
    senderlog = sys.argv[5]

    #open log file and start logging
    f = open(senderlog,"w") #open in write mode, remember to close file at end
    f2= open(inputfile,"r")#open input file in read mode so can be split into packets
    #open client socket and bind
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #UDP
    except socket.error:
        print("Connection socket failed...exiting...")
        exit()
    recv_tuple = (receiverIP, receiverPort)
    ##s.setsockopt(SOL_SOCKET, SO_REUSEADDR,1)#this allows address and port to be reused, call before bind and the source: https://stackoverflow.com/questions/12362542/python-server-only-one-usage-of-each-socket-address-is-normally-permitted
    s.bind(recv_tuple)#binding done here

    #start receive thread (this code was given)
    recv_thread = threading.Thread(target=receive_thread,args=(s,)) #originally target=rec_thread but changed to target=receive_thread and the args is s (s is client socket)
    recv_thread.start()

    #take input file and split it into packets (use create_packet)
    while True:
        line = f2.read(length-30).strip()
        if line == '':
            #either end of file or just a blank
            break
        ##print("line: "+line)
        packets.append(line)
    print("finished reading input file...")
    for i in range(len(packets)):
        create_packet(packettype,i,length,packets[i]) #create packet adds to the headers array to supply header information
        ##next_seq_number = next_seq_number + 1
    print("created packets")
    #while there are packets to send:
    start = 0
    while start <len(packets):
        #send packets to server using unreliable_channel.send_packet()
        try:
            print("sending...")
            s.settimeout(timeout)
            unreliable_channel.send_packet(s,str(headers[start]+" | "+packets[start]).encode(),recv_tuple) #unsure if encode is needed, send a string of header and packetmsg with | dividing them
            f.write("Packet sent; type="+headers[start].split(" ")[0]+"; seqNum="+headers[start].split(" ")[1]+"; length="+headers[start].split(" ")[2] + "; checksum="+headers[start].split(" ")[3] + "\n...\n")
        except socket.timeout:
            f.write("Timeout for packet seqNum="+headers[start].split(" ")[1]+"\n...\n")
            #continue
            break#testing purposes

        #update the window size, timer, etc, while window_base less than window_size: print out the packets
        f.write("Updating window;\n#show seqNum of "+str(window_size)+" packets in the window with one bit status (0: sent but not acked, 1: not sent)\n")
        f.write("Window state: ["+str(window_base)+"\n")
        for q in range(3):
            #extract the ACK packet
            recv_data, tup_addr = unreliable_channel.recv_packet(s)#the recv_data will be strictly the DATA
            if recv_data and tup_addr:#seeks a response from recv packet and break out of the triple ack system if received
                responsive = True
                break
        if responsive:#if response received then we will log that received packet
            ackmsg = extract_packet_info(recv_data)
            f.write("Packet received; type="+ackmsg[0]+"; seqNum="+ackmsg[1]+"; length="+ackmsg[2]+"; checksum_in_packet="+ackmsg[3]+"; \n")
            f.write("checksum_calculated="+str(checksum))
            if str(checksum) == head.split(" ")[3]:
                f.write("; status=NOT_CORRUPTED;\n...\n")
            else:
                f.write("; status=CORRUPT\n...\n")
        elif responsive==False:#else if we log a triple dup ack
            f.write("Triple dup acks received for packet seqNum="+head.split(" ")[1]+"\n...\n")
            break
        start = start+1
    print("sent packets...")
    print("updated window...")
    print("logged information...")
    s.close()
    f.close()#finally close
    f2.close()

main()
