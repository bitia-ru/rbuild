from argparse import ArgumentParser


def base_parser():
  p = ArgumentParser()

  p.add_argument('-c', '--config', dest='config', metavar='filepath', type=str, default='./config.rbc', help='set path for project config (default: %(default)s)')
  p.add_argument('-a', '--ask', action='store_true', help='ask user confirmation')
  p.add_argument('--pretend', action='store_true', help="don't really build, just test")
  p.add_argument('--debug', action='store_true', help='Run debug console')
 
  p.add_argument('-v', '--verbose', action='store_true', help='Verbose mode', dest='verbose')
  p.add_argument('-f', '--force', action='store_true', dest='force')
  p.add_argument('--vv', action='store_true', help='Super verbose mode (print system errors)', dest='sysverbose')
  p.add_argument('-V', '--version', action='store_true', help='Print version', dest='version')
  p.add_argument('--silent', action='store_true', help='Silent mode', dest='silent')
  p.add_argument('--logfile', dest='logfile', type=str, default=None, help='default log file path (relative from output dir)')
  p.add_argument('--syslogfile', dest='syslogfile', type=str, default=None, help='default log file path for system debug (relative from output dir)')

  return p

