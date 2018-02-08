from rbuild.ui import *


class BuildTask:
  max_phase_len = None

  def __init__(self, pkg, phase):
    self.pkg = pkg
    self.phase = phase
    self._cache = {}

    if BuildTask.max_phase_len is None:
      BuildTask.max_phase_len = max([ len(t) for t in pkg.prj.phases ])

  def str(self, l=0, spacer=' '):
    uses = self.pkg.uses()
    use_flags_str = grey(' USE="%s"' % ' '.join(uses)) if uses else ''
    features = self.pkg.specific_features()
    features_flags_str = grey(' FEATURES="%s"' % ' '.join(features)) if features else ''
    return '[ %s ] %s%s%s%s' % (grey(self.phase) + ' '*(self.max_phase_len-len(str(self.phase))+1), spacer*l, bold(lgreen(self.pkg.pkgname)) + ('(dummy)' if self.pkg.dummy else ''), use_flags_str, features_flags_str)

  def __eq__(self, a):
    return type(a) == type(self) and self.pkg.pkgname == a.pkg.pkgname and self.phase == a.phase

  def __hash__(self):
    return hash(str(self.pkg.pkgname) + str(self.phase))

  def __repr__(self):
    return str(self.pkg) + '::%s' % str(self.phase)

  def reset_cache(self):
    self._cache = {}

  def deps(self):
    if not 'deps' in self._cache:
      def do():
        res = self.pkg.deps(self.phase)
        if not self.pkg.dummy:
          res += [ self.pkg.prj.task(self.pkg, s) for s in ( self.pkg.prj.phases[s] for s in self.phase.deps ) ]
        return res
      self._cache['deps'] = do()

    return self._cache['deps']

  def reqs(self, wext=True):
    if not 'reqs' in self._cache:
      def do():
        res = self.pkg.reqs(self.phase) if wext else []
        if not self.pkg.dummy:
          res += [ self.pkg.prj.task(self.pkg, s) for s in ( self.pkg.prj.phases[s] for s in self.phase.reqs ) ]
        return res
      self._cache['reqs'] = do()

    return self._cache['reqs']

  def is_outdated(self):
    selfres = self.is_done()
    if not selfres: return False

    deps = []

    def compose(root, deps):
      for d in root.deps():
        if d.pkg.dummy: compose(d, deps)
        else: deps.append(d)

    compose(self, deps)

    for d in deps:
      res = d.is_done()
      if d.is_outdated() or selfres < res:
        return True

    if not self.pkg.dummy and self.phase.outdated_func and self.pkg.is_outdated(self.phase):
      return True

    return False

  def is_done(self):
    if self.pkg.dummy:
      for r in self.reqs():
        if not r.is_done(): return False
      return True
    return self.pkg.is_done(self.phase)

  def do(self, **opts):
    if not opts.get('dryrun', False):
      [ pkg.env(None) for pkg in set(sum( ( [ d.pkg for d in self.pkg.deps(s) + self.pkg.reqs(s) ] for sn,s in self.pkg.prj.phases.items() ), [])) if not pkg.dummy ]

    return self.pkg.do(self.phase, **opts)

