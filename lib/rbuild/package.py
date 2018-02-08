from rbuild.misc import Path
from os import path,makedirs,pipe2,O_NONBLOCK,fdopen,remove
from os.path import relpath
from rbuild.misc import indir,exec,parse_env
from rbuild.pkgname import PackageName
from rbuild.pkgdep import PackageDep
from rbuild.err import *
from rbuild.config import env2sh
from subprocess import Popen, PIPE, STDOUT
from rbuild.scripts import rb_script
from time import time
import json


class Package:
    def __init__(self, pkgname, prj):
      self.prj = prj
      self.pkgname = PackageName(str(pkgname))
      self.scname_env = 'env'
      self.scname_use = 'use'
      self._script = None

      self.reset_cache()

    def reset_cache(self):
      self._cache = {
        'is_done': {},
        'phase_file': {}
      }

    def __repr__(self):
      return '<pkg: %s>' % str(self.pkgname)

    def cfg(self, varname):
      return self.pkgcfg[varname] if varname in self.pkgcfg else (self.prj.cfg[varname] if varname in self.prj.cfg else '')

    def script(self):
      if self.dummy:
        raise RBuildSysError('Attempting to get Rbuild script for dummy package')

      if self._script is None:
        self._script = self._cfg.eval('rbsc', subsh=True)

      return self._script

    def ensure_dir(self, d):
      if not d.is_exists(): makedirs(str(d), exist_ok=True)

    def _do_func(self, phase, **opts):
      silent=opts.get('silent', False)
      dummy=opts.get('dummy', False)
      d = phase.dir(self.pkgname)

      self.ensure_dir(d)

      with indir(d):
        if not dummy:
          retcode = self.exec('rb_do ' + str(phase), scname=str(phase), phase=str(phase))
        else:
          retcode = 0

        self.prj.ui.flush()

        if not silent: print('%s returned %d' % (str(phase), retcode), file=(self.prj.ui.dbg if retcode == 0 else self.prj.ui.err))

      if retcode == 0:
        if phase.is_sticky:
          if not phase.touch(self.pkgname):
            print("Failed touching phase '%s'" % str(phase), file=self.prj.ui.err)
            return False
        return True

      return False

    def do(self, phase, **opts):
      dryrun = opts.get('dryrun', False)

      if phase.dummy or dryrun:
        res = True
      else:
        with self.prj.libsrv.in_pkg(self.pkgname, str(phase)):
          res = self._do_func(phase, dummy=self.ignore_phase(phase))

      if res and phase.cleans:
        fileslist = []
        dirlist = []
        for s in ( self.prj.phases[s] for s in phase.cleans ):
          self._cache['is_done'][s] = False
          if dryrun or not s.is_sticky: continue
          fileslist.append(s.file(self.pkgname))
          if s.dir_type == 'tmp':
            dirlist.append(str(s.dir(self.pkgname)))

        if not dryrun:
          if self.exec('rm -vf %s && rm -rvf %s' % (' '.join(fileslist), ' '.join(dirlist)), clean=True) != 0:
            print("Error occured while cleaning marker files...", file=self.prj.ui.err)
            return False

      if res:
        self._cache['is_done'][phase] = float(time())

      return res

    def ignore_phase(self, phase):
      if type(self.env('RB_PHASES')) is not dict: return False
      return 'ignore' in self.env('RB_PHASES').get(str(phase), '').split(' ')

    def is_done(self, phase):
      if self.dummy:
        raise RBuildSysError('Invocation is_done() function for dummy packages is prohibited (%s).' % str(self.pkg))

      if not phase in self._cache['is_done']:
        def do():
          if phase.dummy:
            return max([ self.is_done(self.prj.phases[s]) for s in phase.deps+phase.reqs])
          elif str(phase) in self.env('RB_PKG_PHASE_STATES'):
            if self.env('RB_PKG_PHASE_STATES')[str(phase)] != '0':
              return float(self.env('RB_PKG_PHASE_STATES')[str(phase)])
            return False
          elif type(phase.is_done_func) is bool: return phase.is_done_func
          else:
            return False
        self._cache['is_done'][phase] = do()

      return self._cache['is_done'][phase]

    def is_done_cached(self, phase):
      if self.dummy:
        raise RBuildSysError('Invocation is_done() function for dummy packages is prohibited (%s).' % str(self.pkg))

      if not 'is_done' in self._cache or not phase in self._cache['is_done']:
        if not phase.dummy and str(phase) in self.env('RB_PKG_PHASE_STATES'):
          if self.env('RB_PKG_PHASE_STATES')[str(phase)] != '0':
            return float(self.env('RB_PKG_PHASE_STATES')[str(phase)])
          return False
        return None

      return self._cache['is_done'][phase]

    def is_outdated(self, phase):
      return self.env('RB_PKG_OUTDATED_STATES')[str(phase)] != '0'

    def iuses(self):
      if not 'env' in self._cache: self.load_env()
      return set(self._cache['env'].get('IUSE', '').strip().split())

    def uses(self, iuses=None):
      if iuses is None:
        iuses = self.iuses()
      else:
        iuses = set(iuses)
      use_set = set()
      for fl in self.prj.use.get('0', []) + self.prj.use.get(str(self.pkgname), []):
        if fl[:1] == '-':
          fl = fl[1:]
          if fl in use_set: use_set.remove(fl)
        else:
          use_set.add(fl)
      if not self.dummy:
        return use_set & iuses

      return use_set

    def specific_features(self):
      return self.prj.features.get(str(self.pkgname), [])

    def features(self):
      fea_set = set()
      for fl in self.prj.features.get('0', []) + self.specific_features():
        if fl[:1] == '-':
          fl = fl[1:]
          if fl in fea_set: fea_set.remove(fl)
        else:
          fea_set.add(fl)
      return fea_set

    def use(self, *flags):
      uses = self.uses()
      for flag in flags:
        if flag not in uses: return False
      return True

    def load_env(self):
      if 'env' in self._cache: return
      print('Loading environment for package', str(self.pkgname), '...', file=self.prj.ui.sysdbg)

      phase_states = { phase_name: phase.test(self.pkgname) for phase_name,phase in self.prj.phases.items() if phase.is_sticky }
      outdated_states = { phase_name: '$( { %s %s; } &>/dev/null; echo $?)' % (phase.outdated_func, phase.file(self.pkgname)) for phase_name,phase in self.prj.phases.items() if phase.outdated_func }
      states_str = '''
declare -A RB_PKG_PHASE_STATES=(
%(phase_states)s
)

declare -A RB_PKG_OUTDATED_STATES=(
%(outdated_states)s
)
      ''' % {
        'phase_states': '\n'.join(('[%s]=%s' % (name,val) for name,val in phase_states.items())),
        'outdated_states': '\n'.join(('[%s]=%s' % (name,val) for name,val in outdated_states.items()))
      }
      with self.prj.libsrv.in_pkg(self.pkgname):
        self._cache['env'] = parse_env(json.loads(self.exec('set -e\n%s\nrb_env' % states_str, retstdout=True,scname=self.scname_env,phase=self.scname_env)))

    def env(self, varname):
      if not 'env' in self._cache:
        self.load_env()

      return self._cache['env'].get(varname, '')

    def deps(self, phase):
      if not hasattr(self, '_deps'): self._deps = {}

      if not phase in self._deps:
        deps_dict = { '0': self.dummy } if self.dummy else self.env('RB_PKG_DEPS')
        try:
          self._deps[phase] = PackageDep.parse2tasks(self.prj, self.uses() if not self.dummy else None, phase, (deps_dict.get(str(phase), '') + deps_dict.get('0', '')).strip())
        except RBuildError as e:
          raise RBuildFileError(self, e.msg)

      return self._deps[phase]

    def reqs(self, phase):
      if not hasattr(self, '_reqs'): self._reqs = {}

      if not phase in self._reqs:
        reqs_dict = { '0': self.dummy } if self.dummy else self.env('RB_PKG_REQS')
        try:
          self._reqs[phase] = PackageDep.parse2tasks(self.prj, self.uses() if not self.dummy else None, phase, (reqs_dict.get(str(phase), '') + reqs_dict.get('0', '')).strip())
        except RBuildError as e:
          raise RBuildFileError(self)

      return self._reqs[phase]

    def exec(self, cmd, **args):
      script = self.script()

      varmap = {
        'RB_BIN_PATH': str(self.prj.rbbindir),
        'RB_LIB_ADDR': '%s:%s' % self.prj.libsrv.addr,
        'RB_PHASE': args.get('phase', ''),
      }
      varmap.update({ k:v for k,v in self._cfg.full_env().items() if type(v) is str})

      retstdout = args.get('retstdout', False)
      clean = args.get('clean', False)
      save_sc = args.get('save_sc', False)

      prescript2 = '\n'.join([
        'declare -A RB_PHASES=(' + ' '.join("[%s]=''" % phase for phase in self.prj.phases.keys()) + ')'
      ])

      if not clean:
        prescript = rb_script('prescript.sh') + (args['prescript'] if set(args)&{'prescript'} else '')
        postscript = rb_script('postscript.sh')

        script_full = '\n'.join((prescript, prescript2, script, postscript, cmd))
      else:
        script_full = cmd

      scname = '.%s.sh' % args.get('scname', 'unnamed')

      script_path = str(scname)
      
      with open(script_path, 'w') as f:
        f.write(script_full)

      stdout_r = None

      if retstdout:
        r,w = pipe2(O_NONBLOCK)
        stdout,stdout_r = fdopen(w, 'w'),fdopen(r)
      else: stdout = self.prj.ui.dbg

      retcode = exec(['bash', script_path], stdout=stdout, stderr=self.prj.ui.err, env=varmap)

      if retcode == 0:
        if not save_sc and Path(scname).is_file(): remove(scname)

      if retstdout:
        stdout.flush()
        if retcode != 0:
          raise RbExecError(retcode, self.pkgname, script_path)
        else:
          return ''.join(stdout_r.readlines())

      return retcode

