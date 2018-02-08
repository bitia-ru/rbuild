import json,yaml,re
from rbuild.misc import Path, parse_env
from rbuild.pkgname import PackageName
from rbuild.scripts import rb_script_fullpath
from rbuild.err import *
from rbuild.sh import Sh


def env2sh(env):
  return ''.join("%s='%s';" % (str(k), str(v)) for k,v in env.items())


class ConfigGroup:
  def __init__(self, cfg, name):
    self.cfg = cfg
    self.name = name

  def __getitem__(self, varname):
    return self.get(varname, '')

  def get(self, varname, default=None):
    if not hasattr(self, '_cache'):
      self._load()

    return self._cache[varname] if varname in self._cache else default

  def __contains__(self, varname):
    return True if varname in self.keys() else False

  def keys(self):
    if not hasattr(self, '_cache'):
      self._load()
    return list(self._cache.keys())

  def values(self):
    if not hasattr(self, '_cache'):
      self._load()
    return list(self._cache.values())

  def __dict__(self):
    res = { }
    for k in self.keys():
      res[k] = self[k]
    return res

  def get_wpkg(self, varname, pkgname):
    self._load(pkgname.env())

    return self.get(varname, '')


class ConfigPhase(ConfigGroup):
  def __init__(self, cfg, name):
    super(type(self), self).__init__(cfg, name)

  def _load(self, addenv={}):
    funcs = self.cfg._phases[self.name]
    self._cache = {}

    for func in funcs:
      e = json.loads(self.cfg._sh.eval('%s ____phase_func_%d; env2json;' % (env2sh(addenv), func), subsh=True).strip())
      self.cfg.remove_zero_env(e)
      e = parse_env(e)
      e_diff = { k:v for k,v in e.items() if k not in self.cfg._cache or self.cfg._cache[k] != v }
      self._cache.update(e_diff)


class ConfigPackage(ConfigGroup):
  def __init__(self, cfg, pkgname):
    super(type(self), self).__init__(cfg, pkgname)

  def _load(self, addenv={}):
    self._cache = {}

    e = json.loads(self.eval('env2json', subsh=True).strip())
    self.cfg.remove_zero_env(e)
    e = parse_env(e)
    self._cache = { k:v for k,v in e.items() if k not in self.cfg._cache or self.cfg._cache[k] != v }

  def eval(self, cmd, **args):
    funcs = self.cfg._pkgs[str(self.name)]

    return self.cfg._sh.eval('%(pkgname_env)s %(dynvars)s %(pkgfuncs)s %(cmd)s' % {
      'pkgname_env': env2sh(self.name.env()),
      'dynvars': ''.join('%s=$(%s);' % (var, var) for var in self.cfg._dynvars),
      'pkgfuncs': ''.join('____package_func_%d;' % func for func in funcs),
      'cmd': cmd
    }, **args)

  def feed(self, cmd, **args):
    funcs = self.cfg._pkgs[str(self.name)]

    return self.cfg._sh.feed('%(pkgname_env)s %(dynvars)s %(pkgfuncs)s %(cmd)s' % {
      'pkgname_env': env2sh(self.name.env()),
      'dynvars': ''.join('%s=$(%s);' % (var, var) for var in self.cfg._dynvars),
      'pkgfuncs': ''.join('____package_func_%d;' % func for func in funcs),
      'cmd': cmd
    }, **args)

  def full_env(self):
    e = dict(self.cfg._cache)
    e.update(self._cache)
    return e

class Config:
  def __init__(self, cfgfile, bindir, workdir=Path.cwd()):
    self._pkgs_max_func = 0
    self._pkgs = {}
    self._phases_max_func = 0
    self._phases = {}
    self._dynvars = []
    self.script = 'cfg.sh'
    self.cfgdir = workdir

    self._sh = Sh(cwd=self.cfgdir,shell=(bindir / 'bash'),env={})

    res = self._sh.require(rb_script_fullpath(self.script))

    self._sh.setenv('PATH', '%s${PATH+:${PATH}}' % str(bindir))

    self._zero_env = json.loads(self._sh.eval('env2json', subsh=True).strip())

    cfg_amalgamated = self.proccess_file(str(cfgfile))

    tmppath = Path(".cfg.sh")
    with open(str(tmppath), "w") as f:
      f.write(cfg_amalgamated)

    self._sh.require(tmppath)

    tmppath.remove()

    self._load()

  def cleanup(self):
    self._sh.exit()

  def proccess_file(self, f):
    content = open(f).read()

    def proccess_line(line):
      m = re.match(r"^\s*pkg\s+%s\s+{\s*" % PackageName.template, line)

      if m:
        n = self._pkgs_max_func
        funcs = self._pkgs.get(m.group('entire'), [])
        funcs.append(n)
        self._pkgs[m.group('entire')] = funcs
        self._pkgs_max_func += 1
        return "____package_func_%d() {" % n

      m = re.match(r"^\s*pkg_phase\s+(?P<phase>%s)\s+{\s*" % __import__('rbuild.phase').phase.Phase.template, line)

      if m:
        n = self._phases_max_func
        funcs = self._phases.get(m.group('phase'), [])
        funcs.append(n)
        self._phases[m.group('phase')] = funcs
        self._phases_max_func += 1
        return "____phase_func_%d() {" % n

      m = re.match(r"^\.\s+(?P<path>[a-zA-Z0-9_\-/\.]+\.rbi)$", line)

      if m:
        return self.proccess_file(m.group('path'))

      m = re.match(r"^\s*(?P<funcname>[a-zA-Z_][a-zA-Z0-9_\-]*)=>(?P<value>.+)$", line)

      if m:
        self._dynvars.append(m.group('funcname'))
        return "%(funcname)s() { echo %(value)s; }" % m.groupdict()

      m = re.match(r"^\s*(?P<varname>[a-zA-Z_][a-zA-Z0-9_\-]*)=\((?P<value>.*)$", line)

      if m:
        return "declare -A %(varname)s=(%(value)s" % m.groupdict()

      return line

    return '\n'.join(proccess_line(line) for line in content.split('\n'))

  def remove_zero_env(self, env):
    for k,v in self._zero_env.items():
      if k in env and env[k] == v: del env[k]

  def _load(self):
    self._cache = json.loads(self._sh.eval('%s env2json' % '; '.join('%s=$(%s)' % (var, var) for var in self._dynvars), subsh=True).strip())
    self.remove_zero_env(self._cache)
    self._cache = parse_env(self._cache)

  def __getitem__(self, varname):
    return self.get(varname, '')

  def get_dynvar(self, varname):
    if self._dynvars[varname] is None:
      self._dynvars[varname] = self._sh.eval(varname, subsh=True).strip()

  def get(self, varname, default=None):
    if varname in self._dynvars:
      return set.get_dynvar(varname)

    return self._cache[varname] if varname in self._cache else default

  def __contains__(self, varname):
    return True if self.__getitem__(varname) else False

  def __dict__(self):
    res = { }
    for k in self._cache.keys():
      res[k] = self._cache[k]
    return res

  def phases(self):
    return self._phases.keys()

  def phase(self, name):
    return ConfigPhase(self, name)

  def packages(self):
    return self._pkgs.keys()

  def package(self, name):
    if str(name) not in self._pkgs: return None
    return ConfigPackage(self, name)

