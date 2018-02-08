import os

_ROOT = os.path.abspath(os.path.dirname(__file__))

def rb_script(path):
  data = ''
  with open(os.path.join(_ROOT, path)) as f:
    data += f.read()
  return data

def rb_script_fullpath(path):
  return os.path.join(_ROOT, path)

