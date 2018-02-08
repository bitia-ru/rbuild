from rbuild.misc import Path,AttrDict
from os.path import relpath,abspath,dirname,join
from os import makedirs
from rbuild.lib import LibServer
from rbuild.package import Package
from rbuild.pkgname import PackageName
from rbuild.config import Config
from rbuild.pkgdep import PackageDep
from rbuild.buildtask import BuildTask
from rbuild.err import *
from rbuild.uri import URI
from rbuild.version import version as rb_version
from rbuild.graph import dfs
from rbuild.phase import Phase
import sys, yaml, re, types

from time import time


class Project:
  def __init__(self, **args):
    self.args = args
    self.ui = args['ui']
    self._root = self.args.get('root', Path.cwd())

    cfgpath = Path(args.get('config', 'config.rbc'))

    cfgpath_full = (self._root/cfgpath).resolve()

    if not (cfgpath_full).is_file():
      raise ConfigError("Config file '%s' not found" % str(cfgpath_full))

    self.rbbindir = Path(args['rbuild']).realpath().dirname()

    self.cfg = Config(cfgpath, self.rbbindir, self._root)

    self.tasks = {}

    if self.cfg.get('root', None): self._root = Path(self.cfg['root'])

    self._root = self._root.absolute()

    if not self._root.is_dir():
      raise RBuildError('Project directory is not exists: %s' % str(self._root))

    self._root = self._root.resolve()

    self.libsrv = LibServer(self)

  def __enter__(self):
    if not self.args.get('no-libsrv-autostop', False):
      self.libsrv.start()
    return self

  def __exit__(self, *args):
    if self.libsrv.is_alive():
      self.libsrv.stop()
    self.cfg.cleanup()

  def task(self, pkg, phasename):
    phasename = str(phasename)
    if not (pkg, phasename) in self.tasks:
      self.tasks[(pkg, phasename)] = BuildTask(pkg, self.phases[phasename])

    return self.tasks[(pkg, phasename)]

  def root(self):
    return self._root.relative_from(Path.cwd())

  def pkg(self, pkgname):
    if not type(pkgname) == PackageName:
      pkgname = PackageName(pkgname)

    found = None

    if pkgname in self.packages:
      found = pkgname
    else:
      for pkg in self.packages:
        if pkg.name == pkgname.name and pkg.category == pkgname.category and ( pkgname.fullversion == pkg.fullversion if pkgname.fullversion else True ):
          found = pkg

    if not found: raise NoPackageError(pkgname)

    if self.packages[found] == None:
      pkg = Package(found, self)
      pkgcfg = self.cfg.package(found)
      if not pkgcfg:
        pkgcfg = self.cfg['pkg'][str(found)]

      if type(pkgcfg) is str: pkg.dummy = pkgcfg
      else:
        pkg.dummy = False
        pkg._cfg = pkgcfg
        pkgcfg = dict(pkgcfg)

      pkg.pkgcfg = pkgcfg
      self.packages[found] = pkg

    return self.packages[found]

  def pkg_cfg(self, pkgname):
    return self.pkg(pkgname).pkgcfg

  def find_pkg(self, pkgtpl):
    found = []

    for pkg in self.packages:
      if pkg.fullname == pkgtpl or pkg.name == pkgtpl:
        found.append(pkg)

    if not found: return self.pkg(pkgtpl)
    if len(found) > 1: raise AmbigousPackageError(pkgtpl)

    return self.pkg(found[0])

  def phase_list(self, phase):
    l = []
    dfs(None, [ phase, ], lambda s: self.phases[s].deps, None, l)
    return l

  def __tm__(self, msg='', end='\n'):
    if not hasattr(self, '_time_start'):
      self._time_start = time()

    print("T# %s %.3f" % (str(msg), time()-self._time_start), end=end)

  def __intm__(self, msg):
    if not hasattr(self, '_time_start'):
      self._time_start = time()

    prj = self

    class InTm:
      def __enter__(self):
        prj.__tm__('#T ' + str(msg) + ' {')
        return self
      def __exit__(self, t, v, bt):
        prj.__tm__('} ' + str(msg))

    return InTm()

  def load_config(self):
    try:
      self.packages = {}

      version = self.cfg['version']

      if version:
        needed = PackageDep.parse(version)[0]
        current = PackageName('rbuild-'+rb_version['version'])
        if not needed.__eq__(current): raise RBuildError('rbuild version is not compatible (%s)' % version)

      self.name = self.cfg['project_name']

      self.phases = {}
      self.phase_defs = {}

      self.phase_defs['phase'] = self.cfg['pkg_defphases'].get('phase', 'build')
      self.phase_defs['reltype'] = self.cfg['pkg_defphases'].get('reltype', 'spokesman')

      for phname in self.cfg.phases():
        ph = Phase(self, phname)
        ph.cfg = self.cfg.phase(phname)

        if 'dummy' in ph.cfg and ph.cfg['dummy'] == True:
          ph.dummy = True
          ph.reqs = ph.cfg['deps'].split()
        else:
          ph.is_sticky = False
          if 'dir' in ph.cfg:
            ph.dummy = False
            ph._dir = Path(ph.cfg['dir']).absolute()
            if 'dir_type' in ph.cfg:
              if ph.cfg['dir_type'] == 'temporary': ph.dir_type = 'tmp'
              elif ph.cfg['dir_type'] == 'output': ph.dir_type = 'out'
              else: ph.cfg['dir_type'] = 'src'
            else: ph.dir_type = 'src'
            if not 'is_done_func' in ph.cfg:
              ph.is_sticky = True
          else:
            ph.dummy = True
          ph.deps = ph.cfg.get('deps', '')
          ph.reqs = ph.cfg.get('reqs', ph.deps)
          ph.deps = ph.deps.split()
          ph.reqs = ph.reqs.split()
          ph.cleans = ph.cfg.get('cleans', '').split()
          ph.outdated_func = ph.cfg.get('outdated_func', None)
          ph.is_done_func = ph.cfg.get('is_done_func')
          if ph.is_done_func:
            if ph.is_done_func == 'false': ph.is_done_func = False
            elif ph.is_done_func == 'true': ph.is_done_func = True
        self.phases[phname] = ph

      self.phase_defs['phase'] = self.phases[self.phase_defs['phase']]

      for name,s in self.phases.items():
        s.reqsdeps_all = []
        dfs(None, [ s ], lambda s: [ self.phases[d] for d in set(s.reqs+s.deps) ], None, s.reqsdeps_all)
        s.reqsdeps_all = { e for e in set(s.reqsdeps_all) if e != s }

      for name in (tuple(self.cfg.packages()) + tuple(self.cfg['pkg'].keys())):
        pkgname = PackageName(name)
        self.packages[pkgname] = None

      self.use = self.cfg.get('USE', {})
      if type(self.use) is not dict: self.use = { '0': str(self.use) }
      self.use = { k: v.strip().split() for k,v in self.use.items() }

      self.features = self.cfg.get('FEATURES', {})
      if type(self.features) is not dict: self.features = { '0': str(self.features) }
      self.features = { k: v.strip().split() for k,v in self.features.items() }

    except RBuildError as e:
      raise e
    except Exception as e:
      raise ConfigError(str(e))

  def close(self):
    self.libsrv.stop()

