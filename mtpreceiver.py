## import (add more if you need)
import unreliable_channel
import sys
import socket
import zlib #source: https://www.kite.com/python/examples/1939/zlib-generate-a-crc-checksum-and-check-it-after-decompression
import select

##Make ACK packets for receiver to send to sender
def create_packet(ptype,seqnum,leng,datamsg):
    # Two types of packets, data and ack
    # crc32 available through zlib library
    strng = "" #if you split with a space character, then index 0 is packet type, index 1 is seqnum, 2 is length, 3 is checksum
    strng = strng + str(ptype)+" "+str(seqnum)+" "+str(leng)+" "
    checksum = zlib.crc32(datamsg.encode()) #some data parameter has to go into the parenthesis here (the string of the data packet)
    strng = strng+str(checksum)[0:4]
    ##headers.append(strng)
    print("ackhead " + strng)
    return strng

if(len(sys.argv)!=4):
    print("Either not enough arguments or too many arguments. Program requires port, output file name, and receiver log file name. Program Ending...")
    sys.exit()


host="0.0.0.0"
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(("",port))

addr = (host,port)
buf=1472
seq=0
#data,addr = s.recvfrom(buf)
#print ("Received File: "+data.strip())
f = open(sys.argv[2],'w')#replace data.strip with sys.argv[2] which is name of outputfile and did w instead of wb
logging = open(sys.argv[3],"w")
##data,addr = s.recvfrom(buf)
data, addr = unreliable_channel.recv_packet(s)
print("received...\n"+data.decode())
acknowledgement = create_packet(1,data.decode().split("_._")[0].split(" ")[1], 16, data.decode().split("_._")[1])
logging.write("Packet received; type=DATA; seqNum="+data.decode().split("_._")[0].split(" ")[1]+"; length=1472; checksum_in_packet="+data.decode().split("_._")[0].split(" ")[3]+"\nchecksum_calculated="+acknowledgement.split(" ")[3]+"; status=")

##unreliable_channel.send_packet(s,acknowledgement.encode(), addr)#SEND ACK ACCORDINGLY
##logging.write("Packet sent; type=ACK; seqNum="+acknowledgement.split(" ")[1]+"; length=16; checksum_in_packet="+acknowledgement.split(" ")[3])

if str(seq) != data.decode().split("_._")[0].split(" ")[1]:
    logging.write("OUT_OF_ORDER_PACKET")
    if(data.decode().split("_._")[0].split(" ")[3] == acknowledgement.split(" ")[3]):
        logging.write(",NOT_CORRUPT\n...\n")#handle log file information
    else:
        logging.write(",CORRUPT\n...\n")
elif str(seq) == data.decode().split("_._")[0].split(" ")[1]:
    #handles first packet when not out of order
    if(data.decode().split("_._")[0].split(" ")[3] == acknowledgement.split(" ")[3]):
        logging.write("NOT_CORRUPT\n...\n")#handle log file information
    else:
        logging.write("CORRUPT\n...\n")
    seq=seq+1#just internally keep track of an expected seq number

unreliable_channel.send_packet(s,acknowledgement.encode(), addr)#SEND ACK ACCORDINGLY
logging.write("Packet sent; type=ACK; seqNum="+acknowledgement.split(" ")[1]+"; length=16; checksum_in_packet="+acknowledgement.split(" ")[3]+"\n...\n")
print("listening")
try:
    while(data):
        print("received...")
        print(data.decode())
        f.write(data.decode().split("_._")[1]) #split at the special character to only write the data
        s.settimeout(5)
        ##data,addr = s.recvfrom(buf)
        data, addr = unreliable_channel.recv_packet(s)
        acknowledgement=create_packet(1,data.decode().split("_._")[0].split(" ")[1], 16, data.decode().split("_._")[1])#create ack packets for second data packet and onward
        logging.write("Packet received; type=DATA; seqNum="+data.decode().split("_._")[0].split(" ")[1]+"; length=1472; checksum_in_packet="+data.decode().split("_._")[0].split(" ")[3]+"\nchecksum_calculated="+acknowledgement.split(" ")[3]+"; status=")

        ##unreliable_channel.send_packet(s,acknowledgement.encode(), addr)#SEND ACK ACCORDINGLY
        ##logging.write("Packet sent; type=ACK; seqNum="+acknowledgement.split(" ")[1]+"; length=16; checksum_in_packet="+acknowledgement.split(" ")[3])

        if str(seq) != data.decode().split("_._")[0].split(" ")[1]: #check if sequence number is in order
            logging.write("OUT_OF_ORDER_PACKET")
            if(data.decode().split("_._")[0].split(" ")[3] == acknowledgement.split(" ")[3]):
                logging.write(",NOT_CORRUPT\n...\n")#handle log file information
            elif (data.decode().split("_._")[0].split(" ")[3] != acknowledgement.split(" ")[3]):
                logging.write(",CORRUPT\n...\n")
        elif str(seq) == data.decode().split("_._")[0].split(" ")[1]:
            if(data.decode().split("_._")[0].split(" ")[3] == acknowledgement.split(" ")[3]):
                logging.write("NOT_CORRUPT\n...\n")#handle log file information
            elif (data.decode().split("_._")[0].split(" ")[3] != acknowledgement.split(" ")[3]):
                logging.write("CORRUPT\n...\n")
            seq=seq+1
        ##seq=seq+1#just internally keep track of an expected seq number

        unreliable_channel.send_packet(s,acknowledgement.encode(), addr)#SEND ACK ACCORDINGLY
        logging.write("Packet sent; type=ACK; seqNum="+acknowledgement.split(" ")[1]+"; length=16; checksum_in_packet="+acknowledgement.split(" ")[3]+"\n...\n")

except socket.timeout:
    f.close()
    s.close()
    print ("File Downloaded")

print("done")
