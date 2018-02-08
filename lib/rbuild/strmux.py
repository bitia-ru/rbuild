from threading import Thread
from logging import Logger
from select import epoll, EPOLLIN, EPOLLET
from sys import stderr, stdout
from os import pipe, fdopen
from traceback import print_exception as print_exc


class MuxWorker:
  def __init__(self, mux, node):
    self.mux = mux
    self.thread = Thread(target=self.loop)
    self.node = node
    self.stop = False
    r,w = pipe()
    self.wr = fdopen(w, 'w', 1)
    self.rd = fdopen(r, 'r')

  def start(self):
    self.thread.start()

  def loop(self):
    while True:
      try:
        d = self.rd.readline()

        if self.stop and not d: break

        if not d: continue

        for dest in self.node:
          dst,cfg = dest[0],dest[1]
          if type(dst) == Logger:
            if dst.hasHandlers():
              getattr(dst, cfg['level'])(d[:-1])
          else:
            b = True
            for cond in 'if', 'ifnot':
              if cond in cfg:
                if cond == 'if' and not getattr(self.mux, cfg['if']): b = False
                if cond == 'ifnot'  and getattr(self.mux, cfg['ifnot']): b = False
            if b: print(cfg['formatter'](d) if 'formatter' in cfg else d, file=dst, flush=True, end='')
      except ValueError:
        print_exc(*exc_info())
        break

class StreamMux:
  def __init__(self, nodes, **args):
    self.nodes = nodes
    self.silent = False
    self.verbose = False

    self.workers = dict()

    for name in self.nodes:
      self.workers[name] = MuxWorker(self, nodes[name])
      setattr(self, name, self.workers[name].wr)

  def __enter__(self):
    for name in self.nodes:
      self.workers[name].start()
    return self

  def __exit__(self, etype, value, bt):
    if self.exit_hook: self.exit_hook(self, etype, value, bt)
    self.stop()

  def streaming(self, **args):
    self.exit_hook = args['exit_hook'] if 'exit_hook' in args else None
    return self

  def start(self):
    self.__stop_thr = False
    self.thr.start()

  def stop(self):
    for name in self.nodes:
      self.workers[name].wr.flush()
      self.workers[name].wr.close()
      self.workers[name].stop = True

  def flush(self, timeout=0.01):
    for name in self.nodes:
      self.workers[name].wr.flush()
      self.workers[name].thread.join(timeout)

