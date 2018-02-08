from sys import stdin,stdout,stderr
from rbuild.strmux import StreamMux
from logging import Logger as logger
import re

__all__ = [
  'title',
  'crst',
  'bold',
  'underlined',
  'striked',
  'bleared',
  'red',
  'green',
  'yellow',
  'blue',
  'purple',
  'cyan',
  'grey',
  'lred',
  'lgreen',
  'lyellow',
  'lblue',
  'lpurple',
  'lcyan',
  'lgrey',
  'bg_red',
  'bg_green',
  'bg_yellow',
  'bg_blue',
  'bg_purple',
  'bg_cyan',
  'bg_grey',
  'bg_lred',
  'bg_lgreen',
  'bg_lyellow',
  'bg_lblue',
  'bg_lpurple',
  'bg_lcyan',
  'bg_lgrey',
  'ui',
  'disp',
  'info',
  'warn',
  'err',
  'dbg',
  'dbglog',
  'syswarn',
  'syserr',
  'sysdbg',
  'ask',
  'msg',
]


def title(s):
  if s:
    print('\x1B]2;rbuild: %s\x07' % str(s), end='', flush=True)
  else:
    print('\x1B]2;\x07', end='', flush=True)
def crst(s):       return '\x1B[0m%s\x1B[0m' % str(s)
def bold(s):       return '\x1B[1m%s\x1B[0m' % str(s)
def underlined(s): return '\x1B[4m%s\x1B[0m' % str(s)
def striked(s):    return '\x1B[9m%s\x1B[0m' % str(s)
def bleared(s):    return '\x1B[2m%s\x1B[0m' % str(s)

def red(s):    return '\x1B[31m%s\x1B[0m' % str(s)
def green(s):  return '\x1B[32m%s\x1B[0m' % str(s)
def yellow(s): return '\x1B[33m%s\x1B[0m' % str(s)
def blue(s):   return '\x1B[34m%s\x1B[0m' % str(s)
def purple(s): return '\x1B[35m%s\x1B[0m' % str(s)
def cyan(s):   return '\x1B[36m%s\x1B[0m' % str(s)
def grey(s):   return '\x1B[37m%s\x1B[0m' % str(s)

def lred(s):    return '\x1B[91m%s\x1B[0m' % str(s)
def lgreen(s):  return '\x1B[92m%s\x1B[0m' % str(s)
def lyellow(s): return '\x1B[93m%s\x1B[0m' % str(s)
def lblue(s):   return '\x1B[94m%s\x1B[0m' % str(s)
def lpurple(s): return '\x1B[95m%s\x1B[0m' % str(s)
def lcyan(s):   return '\x1B[96m%s\x1B[0m' % str(s)
def lgrey(s):   return '\x1B[97m%s\x1B[0m' % str(s)

def bg_red(s):    return '\x1B[41m%s\x1B[0m' % str(s)
def bg_green(s):  return '\x1B[42m%s\x1B[0m' % str(s)
def bg_yellow(s): return '\x1B[43m%s\x1B[0m' % str(s)
def bg_blue(s):   return '\x1B[44m%s\x1B[0m' % str(s)
def bg_purple(s): return '\x1B[45m%s\x1B[0m' % str(s)
def bg_cyan(s):   return '\x1B[46m%s\x1B[0m' % str(s)
def bg_grey(s):   return '\x1B[47m%s\x1B[0m' % str(s)

def bg_lred(s):    return '\x1B[101m%s\x1B[0m' % str(s)
def bg_lgreen(s):  return '\x1B[102m%s\x1B[0m' % str(s)
def bg_lyellow(s): return '\x1B[103m%s\x1B[0m' % str(s)
def bg_lblue(s):   return '\x1B[104m%s\x1B[0m' % str(s)
def bg_lpurple(s): return '\x1B[105m%s\x1B[0m' % str(s)
def bg_lcyan(s):   return '\x1B[106m%s\x1B[0m' % str(s)
def bg_lgrey(s):   return '\x1B[107m%s\x1B[0m' % str(s)


def pkgname2str(name):
  return green(name)


def red_prefix(msgs):
  msglevel = 0
  return lred('%s ' % '*'*(msglevel+1)) + msgs
def yellow_prefix(msgs):
  msglevel = 0
  return lyellow('%s ' % '*'*(msglevel+1)) + msgs
def green_prefix(msgs):
  msglevel = 0
  return green('%s ' % '*'*(msglevel+1)) + msgs
def lgreen_prefix(msgs):
  msglevel = 0
  return lgreen('%s ' % '*'*(msglevel+1)) + msgs


log = logger('main')
syslog = logger('sys')


ui = StreamMux({
  'disp':    (
    ( stdout, {'formatter': lgreen_prefix} ),
  ),

  'info':    (
    ( stdout, {'formatter': lgreen_prefix, 'ifnot': 'silent'} ),
    ( log, {'level': 'info'} )
  ),

  'warn':    (
    ( stdout, {'formatter': yellow_prefix, 'ifnot': 'silent'} ),
    ( log, {'level': 'warning'} )
  ),

  'err':     (
    ( stderr, {'formatter': red_prefix} ),
    ( log, {'level': 'error'} )
  ),

  'dbglog':     (
    ( log, {'level': 'debug'} ),
    ( stderr, {'formatter': yellow_prefix, 'if': 'sysverbose'} ),
  ),

  'dbg':     (
    ( stdout, {'formatter': green_prefix, 'if': 'verbose'} ),
    ( log, {'level': 'debug'} )
  ),

  'syswarn': (
    ( stdout, {'formatter': yellow_prefix, 'if': 'verbose'} ),
    ( syslog, {'level': 'warning'} )
  ),

  'syserr':  (
    ( stderr, {'formatter': red_prefix} ),
    ( syslog, {'level': 'error'} )
  ),

  'sysdbg':  (
    ( stderr, {'formatter': red_prefix, 'if': 'sysverbose'} ),
    ( syslog, {'level': 'debug'} ),
  ),
})

ui.log = log
ui.syslog = syslog

ui.logfile = None
ui.syslogfile = None

ui.silent = False
ui.verbose = False
ui.sysverbose = False

disp    = ui.disp
info    = ui.info
warn    = ui.warn
err     = ui.err
dbg     = ui.dbg
dbglog  = ui.dbglog
syswarn = ui.syswarn
syserr  = ui.syserr
sysdbg  = ui.sysdbg

def ask(prompt, *args):
  color_table = {
    'msg':   lgreen,
    'info':  blue,
    'warn':  yellow,
    'alert': red
  }

  level = tuple(set(args)&set(color_table.keys()))
  level = level[0] if level else 'msg'

  def level_color(text):
    return color_table[level](text)

  yesno = '[%s/%s]' % (lgreen('Yes'), bold(red('No')))

  ui.flush()
  print(green_prefix('%s%s' % (bold(prompt), (' %s ' % yesno) if 'yesno' in args else ': ')), end='', flush=True)

  answer = input()

  if 'yesno' in args:
    return True if re.match(r'[Yy]([Ee][Ss]){0,1}', answer) else False

  return answer

def msg(dest, *args):
  class Msg:
    def __init__(self, args, dest):
      self.args = args
      self.dest = dest
      pass
    def __enter__(self):
      print(*self.args, file=self.dest)
      ui.flush()
      return self
    def __exit__(self, t, v, bt):
      pass

  return Msg(args, dest)

