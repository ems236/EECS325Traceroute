import sys
import socket
import struct
import select 

#generate list of ip addresses
ips = []
hosts = open("targets.txt", "r")
for line in hosts:
	ips.append(socket.gethostbyname(line))

#generate message bytes (1472B size)
msg = bytearray(b'measurement for class project. questions to student ems236@case.edu or professor mxr136@case.edu ')
while(len(msg) < 1472):
	#append a bunch of 'a's
	msg.append(97)

#set up outbound UDP socket
out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#initial ttl = 30
ttl = 30
out.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

#pick a port to send from and listen on
hostPort = 50001
out.bind(("", hostPort))

#set up inbound raw socket
listen = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
listen.bind(("", hostPort))

#define constansts
#pick weird port
sendport = 33435
#max = 1500 for original datagram + 20 for new IP header + 8 for ICMP header
max = 1528
print(ips[0])

sent = out.sendto(msg, (ips[0], sendport))
print("sent " + str(sent) + " bytes")

#handle timeouts for response (3s timeout)
ready = select.select([listen], [], [], 3)
tried = 0
#returns byte object with length of whatever came to socket, defragments for me I think? 

if ready[0] == []:
	#timeout
	tried += 1
	print("select timeout")
	if tried == 3:
		#give up
		print("failed")

else:
	print("data ready")
	#returns byte object with length of whatever came to socket, defragments for me I think? 
	rsp = listen.recv(max)
	#28 bits of new IP header and ICMP header
	lengthReturned = len(rsp) - 28
	print(lengthReturned)

	#20 bytes of ip header, 8 bytes of icmp header, ttl is the 8th byte of the old ip header
	numHops = ttl - rsp[36]
	print(rsp[36])
	## struct.unpack("!H", rsp[36])
	##i += 1

out.close()
listen.close()
