############
#ems236 project2/distMeasurement.py 
#reads file targets.txt in same directory containing hostnames
#calculates RTT, number of hops, and the number of bytes from the original IP datagram included in the ICMP response for each target and also localhost
#prints results in stdout and in results.csv
#accepts no arguments, run with 'sudo python3 distMeasurement.py'
############
import sys
import socket
import struct
import select
import time

#define a constant for the host ip. Surprisingly difficult to find with python.  
HOST_IP = "10.4.3.100"

#generate list of ip addresses
ips = ["127.0.0.1"]
names = ["localhost"]
hosts = open("targets.txt", "r")
for line in hosts:
	#clean out line breaks
	line = line.replace("\r", "")
	line = line.replace("\n", "")
	ips.append(socket.gethostbyname(line))
	names.append(line)
hosts.close()

#generate message bytes (1472B size)
msg = bytearray(b'measurement for class project. questions to student ems236@case.edu or professor mxr136@case.edu ')
while len(msg) < 1472:
	#append a bunch of 'a's
	msg.append(97)

#set up outbound UDP socket
out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#initial ttl = 60
ttl = 60
out.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

#pick a port to send from
hostPort = 50001
out.bind(("", hostPort))

#set up inbound raw socket
listen = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
## don't need to bind
#listen.bind(("", hostPort))


#define constansts
sendports = 33435
#pick weird port to send to
sendport = 33435
#max = 1500 for original datagram + 20 for new IP header + 8 for ICMP header
max = 1528
shouldSend = True
rttList = []
numHopList = []
icmpSizeList = []

i = 0
while i < len(ips):
	#if a non-matching response is received shouldSend is False.
	if shouldSend:
		#send UDP
		out.sendto(msg, (ips[i], sendport))
		#start timer
		start = int(round(time.time() * 1000000))

	#set up select for timeouts
	ready = select.select([listen], [], [], 3)

	#reset shouldSend 
	shouldSend = True

	#handle timeouts for response (3s timeout)
	if ready[0] == []:
		print(names[i])
		print("timeout\r\n")
		tried += 1
		if tried == 3:
			#give up
			i += 1

			#increment sendport for response matching
			sendport += 1
			tried = 0
	
	else:
		#returns byte object with length of whatever came to socket, defragments for me if it has to I think?
		rsp = listen.recv(max)

		#verify response is from target by matching IP src address and dest port of sent packet included with ICMP message
		#28B offset from new headers, src address is bytes 12-15 of IP header
		srcIp = str(rsp[40]) + "." + str(rsp[41]) + "." + str(rsp[42]) + "." + str(rsp[43])
		#get dest port from UDP header.  28 B offset from IP/ICMP, 20B offset from old IP header, dest port is byte 2-3 of UDP header
		destPort = struct.unpack("!H", rsp[50:52])[0]

		#compare src with host IP + loopback and ports match
		if (srcIp == HOST_IP or srcIp == "127.0.0.1") and destPort == sendport:
			#stop timer
			rtt = (int(round(time.time() * 1000000)) - start) / 1000
			rttList.append(rtt)

			print(names[i])
			print("rtt: " + str(rtt) + "ms")
			#excluded 28 bits of new IP header / ICMP header
			lengthReturned = len(rsp) - 28
			icmpSizeList.append(lengthReturned)
			print("Portion of original datagram included with ICMP message: " + str(lengthReturned) + " Bytes")

			#20 bytes of ip header, 8 bytes of icmp header, ttl is the 8th byte of the old ip header
			numHops = ttl - rsp[36]
			numHopList.append(numHops)
			print("Number of hops: " + str(numHops) + "\r\n")
			i += 1

			#increment sendport for response matching
			sendport += 1
			tried = 0
		
		else:
			print("Received response that didn't match. Ignoring it.\r\n")
			shouldSend = False
out.close()
listen.close()

#write to csv
results = open("results.csv", "w")
data = ""
for i in range(0, len(numHopList)):
	data += str(names[i]) + "," + str(numHopList[i]) + "," + str(rttList[i]) + "," + str(icmpSizeList[i]) + "\r\n"

results.write(data)
results.close()	



