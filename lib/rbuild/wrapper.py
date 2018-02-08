from rbuild.err import *
from rbuild.ui import *
from logging import FileHandler, DEBUG

from sys import exc_info
from traceback import print_exception as print_exc


def wrapper(main, **args):
  global ui

  retval = 0

  ui.silent = args.get('silent', False)
  ui.verbose = args.get('verbose', False)
  ui.sysverbose = args.get('sysverbose', False)

  ui.exception = False

  def main_exit(ui, t, v, bt):
    if t:
      try: raise v
      except RBuildSysError as e:
        print_exc(*exc_info(), file=sysdbg)
        print(str(e), file=err)
        print('\nInternal error occured%s.' % ( ', see log file for details (%s)' % args['syslogfile'] if 'syslogfile' in args else '' ), file=err)
      except RBuildError as e:
        print(str(e), file=err)
        print_exc(*exc_info(), file=dbglog)
      except KeyboardInterrupt:
        print('\n\n')
        print_exc(*exc_info(), file=sysdbg)
        print('Stopped (Ctrl-C)', file=err)
        retval = 1
      except:
        print_exc(*exc_info(), file=sysdbg)
        if not ui.sysverbose:
          print('Unexpected error occured%s.' % ( ', see log file for details (%s)' % args['syslogfile'] if 'syslogfile' in args else '' ), file=err)
        retval = 1
      ui.exception = True

  try:
    with ui.streaming(exit_hook=main_exit) as ui:
      args['ui'] = ui
      if 'logfile' in args:
        f = FileHandler(str(args['logfile']))
        f.setLevel(DEBUG)
        ui.log.addHandler(f)

      if 'syslogfile' in args:
        f = FileHandler(str(args['syslogfile']))
        f.setLevel(DEBUG)
        ui.syslog.addHandler(f)
      retval = main(**args)
  except:
    if not ui.exception:
      print('!!!Rbuild PANIC, call the Author!!!\n\n\n\n')
      print_exc(*exc_info())
      ui.stop()

  title(None)
  return retval

