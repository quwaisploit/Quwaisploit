import os
from scapy.all import ARP, Ether, srp
from core.promptui import *

class Module:
    def __init__(self):
        self.info = {
            'name': 'Live Host Scanner Wifi',
            'description': 'Scan Active Client on wifi',
            'author': 'Quwais',
            'options': {
                'IP_RANGE': {
                    'default': '192.168.1.0/24',
                    'required': True,
                    'desc': 'Target IP Range / Subnet'
                },
                'INTERFACE': {
                    'default': 'wlan0',
                    'required': True,
                    'desc': 'Network interface to use (e.g., wlan0, eth0)'
                }
            }
        }

    def run(self, options):
        if os.geteuid() != 0:
            print(f"{PromptUi.error} This Modules requires root access")
            return

        ip_range = options.get('IP_RANGE')
        interface = options.get('INTERFACE')

        print(f"{PromptUi.info} Starting Scan on range: {ip_range} using interface {interface}")

        try:
            arp = ARP(pdst=ip_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp

            # Menambahkan parameter iface agar tidak terjadi error Interface 'None' not found
            result = srp(packet, iface=interface, timeout=3, verbose=False)[0]

            clients = []
            for sent, received in result:
                clients.append({'ip': received.psrc, 'mac': received.hwsrc})

            print(f"{'No':<4} | {'IP Address':<18} | {'MAC Address'}")
            for idx, client in enumerate(clients):
                print(f"{idx+1:<4} | {client['ip']:<18} | {client['mac']}")
            print("=" * 55)
            print(f"{PromptUi.result} Found {len(clients)} in the net")

        except Exception as e:
            print(f"{PromptUi.error} Error while scanning: {e}")
