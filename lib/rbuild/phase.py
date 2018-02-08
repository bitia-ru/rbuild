from os.path import relpath,abspath,dirname,join
from rbuild.config import env2sh
from rbuild.misc import Path


class Phase:
  template = r'[a-zA-Z][a-zA-Z0-9_\-]+'

  def __init__(self, prj, name):
    self.prj = prj 
    self.name = name
    self.deps_all = set()
    self._cache = {
      'file': {}
    }

  def __repr__(self):
    return self.name

  def __str__(self):
    return self.name

  def dir(self, pkgname):
    if pkgname not in self._cache:
      self._cache[pkgname] = Path(self.cfg.get_wpkg('dir', pkgname)).absolute()
    return self._cache[pkgname]

  def env(self, pkgname):
    res = {
      'PHASE': str(self),
      'PHASE_DIR': str(self.dir(pkgname)),
    }
    res.update(pkgname.env())
    return res

  def file(self, pkgname):
    if not pkgname in self._cache['file']:
      self._cache['file'][pkgname] = self.prj.cfg._sh.eval('%s phase_file' % env2sh(self.env(pkgname)), subsh=True).strip()
    return self._cache['file'][pkgname]

  def test(self, pkgname):
    res = self.prj.cfg._sh.eval('%s phase_test' % env2sh(self.env(pkgname)), subsh=True).strip()
    return res

  def touch(self, pkgname):
    res = self.prj.cfg._sh.feed('%s phase_touch' % env2sh(self.env(pkgname)), subsh=True)
    return res == 0

  def comparable(a, b):
    return a in b.reqsdeps_all or b in a.reqsdeps_all

  def __gt__(self, b):
    return b in self.reqsdeps_all

