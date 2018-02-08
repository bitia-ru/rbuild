from sys import stdout, stderr
from os import fork,pipe,fdopen,close,environ,chdir,getcwd,O_NONBLOCK,O_CLOEXEC,execvpe,dup2,kill
from os.path import join
from signal import SIGKILL
import select
from fcntl import fcntl,F_SETFL,F_GETFL,F_SETFD


class Sh:
  def __init__(self, **args):
    sh = args.get('shell', '/bin/sh')
    cwd = args.get('cwd', getcwd())

    self.timeout = 0.5 * 1000000
    self._last_cmd = None
    self._log = []

    self.fds = {
      'stdout': pipe(),
      'stderr': pipe(),
      'stdin': pipe(),
      'ctrl': pipe(),
    }

    for fd in ( 'stdout', 'stderr' ):
      fcntl(self.fds[fd][0], F_SETFL, fcntl(self.fds[fd][0], F_GETFL) | O_NONBLOCK)

    fcntl(self.fds['ctrl'][1], F_SETFD, O_CLOEXEC)

    for fd in ( 'stdout', 'stderr' ):
      setattr(self, fd, fdopen(self.fds[fd][0], 'r'))

    self.stdin = fdopen(self.fds['stdin'][1], 'w', buffering=1)
    self.ctrl = fdopen(self.fds['ctrl'][0], 'r', buffering=1)

    env = args.get('env', environ)

    pid = fork()

    if pid == 0:
      chdir(str(cwd))
      dup2(self.fds['stdin'][0], 0)
      dup2(self.fds['stdout'][1], 1)
      dup2(self.fds['stderr'][1], 2)
      execvpe(str(sh), [ str(sh) ], env)

    self.pid = pid
      
    self._clear_pty()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.exit()

  def print_out(self, f=None):
    [ f(d) if callable(f) else ( print(d, end='', file=f) if f is not None else None ) for d in self.stdout.readlines() ]

  def print_out_err(self, f=None):
    [ f(d) if callable(f) else ( print(d, end='', file=f) if f is not None else None ) for d in self.stderr.readlines() ]

  def _wait_stopped(self, f, ferr):
    p = select.poll()
    p.register(self.ctrl.fileno(), select.EPOLLIN)

    events = None 
    while not events:
      events = p.poll(self.timeout)
      self.print_out(f)
      self.print_out_err(ferr)

    self.ctrl.readline()

    p.unregister(self.ctrl.fileno())

  def _sys_feed(self, data):
    self.stdin.write(data)
    self._log.append(data)

  def _clear_pty(self):
    self._sys_feed('\n')
    self.stdout.readlines()
    self.stderr.readlines()

  def require(self, filepath, **args):
    out = args.get('file', stdout)

    self._last_cmd = 'source "%s"' % str(filepath)
    self._sys_feed(self._last_cmd + '\n')
    self._sys_feed('echo "" >&%s\n' % self.fds['ctrl'][1])
    self._wait_stopped(out, stderr)

  def setenv(self, name, value):
    self._last_cmd = '%s="%s"' % ( name, value )
    self._sys_feed(self._last_cmd)
    self._sys_feed('\n')

  def feed(self, cmd, **args):
    subsh = args.get('subsh', False)
    out = args.get('file', stdout)

    self._last_cmd = cmd
    if subsh: self._sys_feed('(\n')
    self._sys_feed(cmd)
    if cmd[-1] != '\n': self._sys_feed('\n')
    if subsh: self._sys_feed(')\n')
    self._sys_feed('__=$?\necho "" >&%s\n' % self.fds['ctrl'][1])
    self._wait_stopped(out, stderr)

    return int(self.eval('echo -n $__').strip())

  def eval(self, cmd, **args):
    res = []
    out = lambda d: res.append(d)
    err = args.get('err', stderr)
    subsh = args.get('subsh', False)

    if '\n' in cmd:
      raise Exception("%s::eval: 'cmd' argument shall not contain newlines" % type(self).__name__)

    self._last_cmd = cmd
    if subsh: self._sys_feed('(\n')
    self._sys_feed(cmd + '\n')
    if subsh: self._sys_feed(')\n')
    self._sys_feed('echo "" >&%s\n' % self.fds['ctrl'][1])
    self._wait_stopped(out, err)

    return ''.join(res)

  def exit(self):
    self._sys_feed("exit\n")
    for name,val in self.fds.items(): close(val[0]), close(val[1])
    kill(self.pid, SIGKILL)

