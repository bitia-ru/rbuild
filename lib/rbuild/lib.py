import socket, threading, sys
import json as packer
from rbuild.misc import indir,Path,exec
from rbuild.err import *
from rbuild.ui import err,warn,sysdbg
from traceback import print_exception as print_exc
from sys import exc_info
from rbuild.apicomm import send_pckt, recv_pckt
from rbuild.version import version as rb_version

import datetime



class LibServer(threading.Thread):
  def __init__(self, prj):
    threading.Thread.__init__(self)
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.bind(('127.0.0.1', 0))
    self.sock.listen(1)
    self.prj = prj
    self.pkgstk = [ ]
    self.curpkg = None
    self.phase = ''
    self.busy = False

    def ver(env, pipes):
      pipes[0].append(rb_version['version'] + '\n')
      return 0

    def prj_root(env, pipes):
      pipes[0].append(str(self.prj.root()) + '\n')
      return 0

    def pkg_done(env, pipes, phase=None, pkgname=None):
      pkg = prj.find_pkg(pkgname) if pkgname else prj.pkg(self.curpkg)
      if not phase: phase = str(self.curphase)
      if phase not in self.prj.phases: return 1 
      res = pkg.is_done_cached(self.prj.phases[phase])
      if res is None or res < 128: return 1
      #pipes[0].append(str(int(res)) + '\n')
      return 0

    def pkg_env(env, pipes, varname, pkgname=None):
      pipes[0].append(str(prj.pkg(pkgname if pkgname else self.curpkg).env(varname)) + '\n')
      return 0

    def pkg_dir(env, pipes, phase_name=None, pkgname=None):
      if not pkgname: pkgname = self.curpkg
      pipes[0].append(str(prj.phases[phase_name].dir(pkgname)) + '\n')
      return 0

    def pkg_use(env, pipes, *flags):
      if not self.curphase and env['RB_PHASE'] != 'env': return 1
      uses = self.prj.pkg(self.curpkg).uses(env.get('IUSE', '').strip().split())
      for flag in flags:
        if flag not in uses: return 1
      return 0

    def pkg_feature(env, pipes, *flags):
      features = self.prj.pkg(self.curpkg).features()
      for flag in flags:
        if flag not in features: return 1
      return 0

    def pkg_name(env, pipes, *args):
      attrs = ( 'name', 'fullname', 'fullpath', 'category', 'branch', 'version', 'fullversion', 'tag', 'rc' )
      rargs = list(reversed(args))
      attr = None
      pkgname = None

      while rargs:
        arg = rargs.pop()

        if arg == '-a':
          if not rargs: return 1
          attr = rargs.pop()
          if not attr in attrs: return 1
        elif not pkgname:
          pkgname = arg
        else:
          return 1

      pn = prj.pkg(pkgname if pkgname else self.curpkg).pkgname
      if attr:
        pipes[0].append((getattr(pn, attr) if getattr(pn, attr) else '') + '\n')
      else:
        pipes[0].append(', '.join(((getattr(pn, a) if getattr(pn, a) else '') for a in attrs)) + '\n')
        
      return 0

    def cfg(env, pipes, *args):
      force=False
      a = { 'act': 'get' }
      args = list(args)

      if not args:
        pipes[1].append('Arguments error\n')
        return 1

      if args[0] == '-f':
        force=True
        args.pop(0)

      if args[0] == '-t':
        a['act'] = 'get_type'
        args.pop(0)
      elif args[0] == '-k':
        a['act'] = 'get_keys'
        args.pop(0)

      if a['act'] == 'get' or a['act'] == 'get_type' or a['act'] == 'get_keys':
        if not args:
          pipes[1].append('Arguments error\n')
          return 1
        varpath = args.pop(0)
        a['path'] = [ e for e in varpath.strip().split('/') if e ]

      if a['act'] == 'get':
        if not 'path' in a or not a['path']:
          pipes[1].append('Arguments error\n')
          return 1

        curp = 0
        curc = prj.cfg.__dict__()
        for e in a['path']:
          if curp == len(a['path'])-1:
            def conv(e):
              if type(e) == str: return e
              if type(e) == int: return str(e)
              if type(e) == list or type(e) == tuple: return ' '.join(e)
              return None
            if e in curc:
              s = conv(curc[e])
              if not s:
                pipes[1].append('Undefined e type %s, %s' % (str(type(curc[e])), str(curc[e])))
                return 1
              pipes[0].append(s+'\n')
              return 0
            return (1 if not force else 0)

          if type(curc[e]) != dict or not e in curc:
            return (1 if not force else 0)

          curc = curc[e]
          curp += 1
      elif a['act'] == 'get_type':
        if not 'path' in a or not a['path']:
          return 1
        curp = 0
        curc = prj.cfg.__dict__()
        for e in a['path']:
          if curp == len(a['path'])-1:
            def tp(e):
              if type(e) == str or type(e) == int or type(e) == list: return 'value'
              if type(e) == dict: return 'group'
              return None
            if e in curc:
              s = tp(curc[e])
              if s: pipes[0].append(s+'\n')
              else:
                return 1
              return 0
            return (1 if not force else 0)

          if not e in curc or type(curc[e]) != dict:
            return (1 if not force else 0)

          curc = curc[e]
          curp += 1
      elif a['act'] == 'get_keys':
        if not 'path' in a or not a['path']:
          return 1
        curp = 0
        curc = prj.cfg.__dict__()
        for e in a['path']:
          if curp == len(a['path'])-1:
            def tp(e):
              if type(e) == dict: return ' '.join(e.keys())
              return None
            if e in curc:
              s = tp(curc[e])
              if s: pipes[0].append(s+'\n')
              else:
                return 1
              return 0
            return (1 if not force else 0)

          if not e in curc or type(curc[e]) != dict:
            return (1 if not force else 0)

          curc = curc[e]
          curp += 1
      else:
        return 1

    def pkg_cfg(env, pipes, *args):
      force=False
      pkgname,varname = None,None

      args = list(args)

      if args[0] == '-f':
        force=True
        args.pop(0)

      if len(args) == 2:
        pkgname,varname = args[0],args[1]
      elif len(args) == 1:
        pkgname,varname = str(self.curpkg),args[0]
      else:
        return 1

      pkg_cfg = prj.pkg_cfg(pkgname)
      if varname in pkg_cfg:
        pipes[0].append(str(pkg_cfg[varname])+'\n')
        return 0

      cfg_args = (varname, ) if not force else ('-f', varname)

      return cfg(env, pipes, *cfg_args)

    def warning(env, pipes, msg):
      print(msg, file=warn, flush=True)
      return 0

    def flush(env, pipes):
      ui.flush()
      return 0

    self.lib = {
      'ver': ver,
      'prj_root': prj_root,
      'pkg_done': pkg_done,
      'pkg_env': pkg_env,
      'pkg_dir': pkg_dir,
      'pkg_name': pkg_name,
      'pkg_cfg': pkg_cfg,
      'pkg_use': pkg_use,
      'pkg_feature': pkg_feature,
      'cfg': cfg,
      'warning': warning,
      'flush': flush
    }

    self.addr = self.sock.getsockname()

  def stop(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(self.addr)
    send_pckt(s, packer.dumps('quit'))
    s.close()

  def __enter__(self):
    self.start()
    return self

  def __exit__(self, t, v, bt):
    self.stop()

  def in_pkg(self, pkgname, phase=''):
    if self.busy:
      raise RBuildError('Rbuild lib server is busy')
    self.busy = True
    class InPkg:
      def __init__(self, libsrv):
        self.libsrv = libsrv
      def __enter__(self):
        self.libsrv.pkgstk.append( (self.libsrv.curpkg, phase) )
        self.libsrv.curpkg = pkgname
        self.libsrv.curphase = phase
        return self
      def __exit__(self, t, v, bt):
        self.libsrv.busy = False
        self.libsrv.curpkg,self.libsrv.curphase = self.libsrv.pkgstk.pop()

    return InPkg(self)

  def run(self):
    while True:
      pckt = None
      c,a = self.sock.accept()
      try:
        pckt = recv_pckt(c)
        msg = packer.loads(pckt)
        if msg == 'quit':
          return
        if msg['funcname'] in self.lib:
          with indir(msg['env']['PWD']):
            stdout,stderr = [],[]
            retval = self.lib[msg['funcname']](msg['env'], (stdout, stderr), *(msg['args']))
            retmsg = { 'retval': retval, }
            if stdout: retmsg['stdout'] = ''.join(stdout)
            if stderr: retmsg['stderr'] = ''.join(stderr)
            send_pckt(c, packer.dumps(retmsg))
        else:
          send_pckt(c, packer.dumps({ 'retval': 1, 'stderr': 'API function not found: %s\n' % msg['funcname'] }))
      except socket.timeout:
        pass
      except RBuildSysError as e:
        print_exc(*exc_info(), file=sysdbg)
        print(str(e), file=err)
        print('\nInternal error occured through back call, see log file for details.', file=err)
        send_pckt(c, packer.dumps({ 'retval': 1, 'stderr': 'Unexpected error\n' }))
      except RBuildError as e:
        print(str(e), file=err)
        print_exc(*exc_info(), file=sysdbg)
        send_pckt(c, packer.dumps({ 'retval': 1, 'stderr': 'Unexpected error\n' }))
      except:
        print_exc(*exc_info(), file=sysdbg)
        #print('Unexpected error occured through back call, see log for details. (%s)' % self.prj.syslogfile, file=err)
        send_pckt(c, packer.dumps({ 'retval': 1, 'stderr': 'rbapi: Unexpected error, see log for details.\n' }))

#  def stop_forced(self):
#    self.sock.shutdown(socket.SHUT_RDWR)

