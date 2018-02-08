from rbuild.err import *
from struct import pack, unpack


RECV_BUFFER = 1024


def send_pckt(s, pckt):
  d = pckt.encode('utf-8')

  s.sendall(pack('L', len(d)))

  if s.recv(1) != b'Y':
    raise ApiCommError('Packet refused')

  s.sendall(d)


def recvall(s, pckt_len):
  received = 0
  pckt = b''

  while received < pckt_len:
    rest = pckt_len-received
    r = s.recv(RECV_BUFFER if rest > RECV_BUFFER else rest)
    if not r: break
    pckt += r
    received += len(r)

  if len(pckt) != pckt_len:
    raise ApiCommError("Can't receive packet")

  return pckt


def recv_pckt(s):
  pckt = b''
  pckt_len = recvall(s, 4)

  s.sendall(b'Y')

  pckt_len = unpack('L', pckt_len)[0]

  if pckt_len > 1024*1024:
    raise ApiCommError('Msg too long')

  pckt = recvall(s, pckt_len)

  return pckt.decode('utf-8')

