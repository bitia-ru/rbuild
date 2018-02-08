class RBuildError(Exception):
  def __init__(self, msg=None):
    self.msg = msg

  def __str__(self):
    return 'Error' + (': %s' % self.msg if self.msg else '')

class RBuildSysError(Exception):
  pass

class RBuildFileError(RBuildError):
  def __init__(self, pkg, msg=None):
    self.msg = msg
    self.pkg = pkg

  def __str__(self):
    return 'Error in Rbuild file for package %s: %s' % (str(self.pkg), self.msg)

class ConfigError(RBuildError):
  def __init__(self, msg=None):
    self.msg = msg

  def __str__(self):
    return 'Error loading config file' + (' (%s)' % self.msg if self.msg else '')

class NoPackageError(RBuildError):
  def __init__(self, pkgname):
    self.pkgname = pkgname

  def __str__(self):
    return "No such package: '%s'" % str(self.pkgname)

class AmbigousPackageError(RBuildError):
  def __init__(self, pkgname):
    self.pkgname = pkgname

  def __str__(self):
    return "Ambigous package name '%s'" % str(self.pkgname)

class NoApiFuncError(RBuildError):
  def __init__(self, apiname):
    self.apiname = apiname

  def __str__(self):
    return "Undefined API function called '%s'" % self.apiname

class ApiCommError(RBuildError):
  def __init__(self, msg):
    self.msg = msg 

  def __str__(self):
    return "API communication error: %s" % self.msg

class RbExecError(RBuildError):
  def __init__(self, retcode, pkgname, sc):
    self.retcode = retcode
    self.pkgname = pkgname
    self.sc = sc

  def __str__(self):
    return "Rbuild script of package '%s' execution return code is not zero (retcode=%s, '%s')" % (self.pkgname, self.retcode, self.sc)

