#!/usr/bin/env python3

# Network UPS Tools の nut-server に接続して，消費電力を収集して，
# JSON で吐き出すスクリプト．Fluentd と組み合わせて使うことを想定しています．

NUT_PORT = 3493

from telnetlib import Telnet
import json
import re
import time
import pprint

def get_ups_status(host, device):
    status = {}
    with Telnet(host, NUT_PORT) as telnet:
        telnet.write("LIST VAR {device}\n".format(device=device).encode('utf-8'))
        time.sleep(0.1)
        var_list = telnet.read_very_eager().decode('utf-8')
               
        telnet.write("LOGOUT".encode('utf-8'))

        for var_line in var_list.split("\n"):
            var = var_line.split(' ', 4)
            if len(var) != 4:
                continue
            
            status[var[2]] = re.search(r'^"?(.+?)"?$' , var[3]).group(1)

    return status

def get_ups_power(ups_status, ups_rated_power):
    power_rate = int(ups_status['ups.load'])

    return power_rate * ups_rated_power[ups_status['VAR']] / 100.0

UPS_RATED_POWER = {
    'bl50t': 450,
    'by50s': 300,
    'bw55t': 340,
}

UPS_LIST = [
    {
        'name': 'network',
        'host': 'localhost',
        'device': 'bl50t',
    },
    {
        'name': 'server',
        'host': 'columbia',
        'device': 'bl50t',
    },
    {
        'name': 'desktop',
        'host': 'rasp-meter-3',
        'device': 'bw55t',
    },
    {
        'name': 'server-2',
        'host': 'rasp-meter-6',
        'device': 'bw55t',
    },
]

for ups in UPS_LIST:
    ups_status = get_ups_status(ups['host'], ups['device'])
    power = get_ups_power(ups_status, UPS_RATED_POWER)

    result = json.dumps({
        'hostname': ups['name'],
        'power': power,
        'temp': ups_status['ups.temperature'],
        'self_time': 0,
    }, ensure_ascii=False)

    print(result)
