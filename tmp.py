from scapy.all import sniff, TCP, IP
from utils import convert

interface = "\\Device\\NPF_Loopback"

def packet_callback(packet):
    """Callback function to process each packet."""

    if IP in packet and TCP in packet:
        if packet[TCP].sport == 16713 or packet[TCP].dport == 16713:  # Match destination port

            # Extract and print the payload as hexadecimal
            payload = bytes(packet[TCP].payload)
            if payload:
                if packet[TCP].sport == 16713:
                    print("Received from server:")
                else:
                    print("Received from client:")
                #print(convert(payload.hex()))
                content = convert(payload.hex())
                print(" ".join(content))
                #if "THX" in content:
                    #content = content[4:-4]
                    #power = content[1]
                    
                    #print(" ".join(content))

# Start sniffing for packets
print("Starting to monitor traffic on localhost port 16713...")
sniff(iface=interface, filter="tcp port 16713", prn=packet_callback, store=False)
