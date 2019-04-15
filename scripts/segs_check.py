#!/usr/bin/python

# Restart SEGS if auth and/or RPC port becomes unresponsive. -ldilley
# ToDo: Port to Windows and run via Task Scheduler.

import os
import socket

CONNECT_TIMEOUT = 3

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

auth_data = check_connection("blue", 2106)
rpc_query = '{"jsonrpc": "2.0", "method": "ping", "id": 1}'
rpc_data = check_connection("blue", 6001, rpc_query)
if not auth_data or not rpc_data:
  os.system("sudo systemctl restart segs")
#else:
#  print("Auth response: " + repr(auth_data) + "\n")
#  print("RPC response: \n" + str(rpc_data))
