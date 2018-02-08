from os import chdir,getcwd,remove
from os.path import relpath,realpath,isabs,join,abspath,normpath,exists,isfile,isdir,dirname,basename
from threading import Thread
from rbuild.err import *
import sys, subprocess, os
import json, yaml
from rbuild.ui import info, err, dbg, warn, ask, lyellow, green, red, msg, ui


def indir(path):
    class InDir:
        def __init__(self, path):
            path = str(path)
            self.path = path
            self.curdir = relpath(getcwd(), path)
        def __enter__(self):
            chdir(self.path)
        def __exit__(self, type, message, bt):
            chdir(self.curdir)

    return InDir(path)

def exec(command, **args):
  stdout = args['stdout'] if 'stdout' in args else sys.stdout
  stderr = args['stderr'] if 'stderr' in args else sys.stderr
  sh = args['sh'] if 'sh' in args else False
  stdin_en = subprocess.PIPE if 'stdin' in args else None
  env = args['env'] if 'env' in args else os.environ
  cwd = args['cwd'] if 'cwd' in args else getcwd()
  close_fds = args['close_fds'] if 'close_fds' in args else False

  p = subprocess.Popen(command, stdin=stdin_en, stdout=stdout, stderr=stderr, bufsize=1, env=env, shell=sh, cwd=cwd, close_fds=True)

  if 'stdin' in args:
    p.stdin.write(args['stdin'].encode())

  res = p.communicate()

  return p.returncode

def sh(cmd, **args):
  stdout_r = None

  r,w = pipe2(O_NONBLOCK)
  stdout,stdout_r = fdopen(w, 'w'),fdopen(r)

  args['stdout'] = stdout
  args['stderr'] = err
  args['sh'] = True

  retcode = exec(cmd, **args)

  stdout.flush()
  if retcode != 0:
    raise RbExecError(retcode, '')
  else:
    return ''.join(stdout_r.readlines())

def while_exec(command, **args):
  class WhileExec:
   def __init__(self, cmd, args):
     self.cmd, self.args = cmd, args

     if 'pipes' in args and args['pipes']:
       ro,wo = os.pipe()
       re,we = os.pipe()
       ro,wo = os.fdopen(ro), os.fdopen(wo, 'w')
       re,we = os.fdopen(re), os.fdopen(we, 'w')
       self.stdout,self.stderr = (ro,re)
       self._stdout,self._stderr = (wo,we)
     else:
       self._stdout = args['stdout'] if 'stdout' in args else sys.stdout
       self._stderr = args['stderr'] if 'stderr' in args else sys.stderr

     self.stdin = str(args['stdin']) if 'stdin' in args and args['stdin'] else None 

   def __enter__(self):
     self.p = subprocess.Popen(self.cmd, stdout=self._stdout, stderr=self._stderr, stdin=subprocess.PIPE)
     if self.stdin:
       self.p.stdin.write(self.stdin.encode())
       self.p.stdin.close()
     return self

   def __exit__(self, type, a, bt):
     res = self.p.communicate()
     if res[0]: self._stdout.write(res[0])
     if res[1]: self._stderr.write(res[1])
     self._stdout.flush()
     self._stderr.flush()

   def is_exited(self):
     return self.p.poll() != None

   def retcode(self):
     self.p.wait()
     return self.p.returncode

  return WhileExec(command, args)

def do_msg(pre, errmsg=None, okmsg=None, **opts):
  class DoMsg:
    def __init__(self, pre):
      self.pre = pre
      self.retval = None

      if not 'out' in opts:
        opts['out'] = info

      if not 'err' in opts:
        opts['err'] = err

    def __enter__(self):
      print(pre, file=opts['out'], flush=True)
      return self

    def __exit__(self, type, a, bt):
      ui.sync()
      if self.retval or type:
        if errmsg:
          print(errmsg, file=opts['err'], flush=True)

        if type:
          raise a
      elif okmsg:
        print(okmsg, file=opts['out'], flush=True)

  return DoMsg(pre)

def parse_env(env):
  res = dict(env)
  for k,v in res.items():
    if type(v) is not str: continue
    if v[:5] == 'YAML:':
      res[k] = yaml.load(v[5:])
    if v[:5] == 'JSON:':
      res[k] = json.loads(v[5:])
  return res

class AttrDict(dict):
 def __init__(self, *args, **kwargs):
   super(AttrDict, self).__init__(*args, **kwargs)
   self.__dict__ = self

class Path:
  def __init__(self, p, **args):
    if type(p) == type(self):
      self.strpath = p.strpath
    elif type(p) == list or type(p) == tuple:
      path = type(self)(p.pop(0))
      for e in p: path = path / e
      self.strpath = path.strpath
    else:
      self.strpath = str(p)

    relfrom = args.get('relfrom', None)
    if relfrom:
      self.strpath = self.relative_from(type(self)(relfrom)).strpath

    resolve = args.get('resolve', False)
    if resolve:
      self.strpath = self.relative_from(type(self)(resolve)).strpath

  def cwd():
    return Path(getcwd())

  def script_wd():
    return Path(sys.argv[0])

  def realpath(self):
    return Path(realpath(self.strpath))

  def basename(self):
    return type(self)(basename(self.strpath))

  def remove(self):
    remove(self.strpath)

  def dirname(self):
    res = dirname(self.strpath)
    return type(self)(res) if res else type(self)('.')

  def is_absolute(self):
    return isabs(self.strpath)

  def absolute(self):
    return type(self)(abspath(self.strpath))

  def resolve(self):
    return type(self)(normpath(self.strpath))

  def relative_from(self, path):
    return type(self)(relpath(str(self), str(path)))

  def is_exists(self):
    return exists(self.strpath)

  def is_file(self):
    return isfile(self.strpath)

  def is_dir(self):
    return isdir(self.strpath)

  def __truediv__(self, p):
    if type(p) == type(self):
      return type(self)(join(self.strpath, p.strpath))
    else:
      return type(self)(join(self.strpath, str(p)))

  def __str__(self):
    return self.strpath

  def __repr__(self):
    return self.strpath

