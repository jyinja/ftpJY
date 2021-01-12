## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish

## import (add more if you need)
import unreliable_channel
import sys
import socket
import zlib #source: https://www.kite.com/python/examples/1939/zlib-generate-a-crc-checksum-and-check-it-after-decompression
import select

##define header fields, initial values
packettype = 'ACK'
next_seq_number = 0#what seq num is expected
length = 1472 #stated on end of page 1 of the specs, ACK is length 16
checksum = 0
timeout = 500
placeholder_ip = "127.0.0.1" #localhost ip
headers = []
head = ""
HEAD = {"type":hex(0x0001),"seqNum":hex(next_seq_number),"length":hex(length),"checksum":hex(checksum)} #HEAD dictionary stores attributes of the header and hex(0x0000) will be zero representing a DATA packet

##Make ACK packets for receiver to send to sender
def create_packet(ptype,seqnum,leng,datamsg):
    # Two types of packets, data and ack
    # crc32 available through zlib library
    strng = "" #if you split with a space character, then index 0 is packet type, index 1 is seqnum, 2 is length, 3 is checksum
    strng = strng + ptype+" "+str(seqnum)+" "+str(leng)+" "
    checksum = zlib.crc32(datamsg.encode()) #some data parameter has to go into the parenthesis here (the string of the data packet)
    strng = strng+str(checksum)
    headers.append(strng)
    return strng

##Extract the DATA packet received from the sender
def extract_packet_info(data):
    # extract the packet data after receiving
    data = data.decode().strip()
    nothead = data.split(" | ")[1]
    head = data.split(" | ")[0]
    return nothead


def main():
    if(len(sys.argv)!=4):
        print("Either not enough arguments or too many arguments. Program Ending...")
        sys.exit()
    #read command line args
    receiverPort = int(sys.argv[1])
    outputfile = sys.argv[2]
    receiverlog = sys.argv[3]

    #open log file and start logging
    f=open(receiverlog,"w")#since this is open in write mode, everytime program is run a brand new log file is produced (override last one)
    f2=open(outputfile,"w")

    #open server socket and bind
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #unsure if this is needed or not:
    s.bind(("",receiverPort))

    index = 0
    while True:
        #receive packet, but using our unreliable channel
        #packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
        #then call extract_packet_info
        #check for corruption and lost packets, send ack accordingly
        packet_from_server, server_addr = unreliable_channel.recv_packet(s) #this is the function from unreliable channel passing in socket s
        thedata = extract_packet_info(packet_from_server)
        f.write("Packet received; type="+head.split(" ")[0]+"; seqNum="+head.split(" ")[1]+"; length="+head.split(" ")[2]+"; checksum_in_packet="+head.split(" ")[3]+";\n")
        f.write("checksum_calculated="+str(checksum))
        f2.write(thedata)#write to outputfile the DATA strictly, so whatever is not in the header

        ackpack = create_packet(packettype,index,16,thedata) #creates new packet for every received message from sender
        if str(checksum) == head.split(" ")[3]:
            f.write("; status=NOT_CORRUPTED\n...\n")
        elif int(head.split(" ")[1]) != next_seq_number:
            f.write("; status=OUT_OF_ORDER_PACKET\n...\n")
        else:
            f.write("; status=CORRUPT\n...\n")

        try:
            s.settimeout(timeout)
            unreliable_channel.send_packet(s, ackpack.encode(),server_addr)
        except socket.timeout:
            print(ackpack.split(" ")[1]+" seqNum timed out...")
            continue
        next_seq_number = next_seq_number+1
        index = index+1
        #break

    s.close()
    f.close()
    f2.close()#finally close everything

main()

