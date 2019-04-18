#!/usr/bin/python

# Restart SEGS via cron or Task Scheduler if auth and/or RPC port becomes unresponsive. -ldilley

import os
import platform
import socket
import time

HOST_NAME = "blue"
CONNECT_TIMEOUT = 3
WIN_SLEEP_TIME = 3

def check_connection(host, port, payload = None):
  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    sock.connect((host, port))
    if payload:
      sock.send(payload)
    data = sock.recv(1024)
    sock.close()
  except:
    data = None
  return data

auth_data = check_connection(HOST_NAME, 2106)
rpc_query = '{"jsonrpc": "2.0", "method": "ping", "id": 1}'
rpc_data = check_connection(HOST_NAME, 6001, rpc_query)
if not auth_data or not rpc_data:
  if platform.system() == "Windows":
    os.system("sc stop segs")
    time.sleep(WIN_SLEEP_TIME)
    os.system("sc start segs")
  else:
    os.system("sudo systemctl restart segs")
#else:
#  print("Auth response: " + repr(auth_data) + "\n")
#  print("RPC response: \n" + str(rpc_data))
