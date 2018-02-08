import re


class PackageName:
  template = r"(?P<entire>((?P<category>[\w\-\+_]+)/|)(?P<fullname>(?P<name>[\w\-\+_]+?)((@(?P<branch>[\w\-_\.]+))|(\-(?P<fullversion>(?P<version>(\d+\.)*\d+)((?P<tag>[a-zA-Z])|(\-[Rr][Cc](?P<rc>\d+))){0,1}))){0,1}))"

  def __init__(self, fullpath):
    self.fullpath = str(fullpath).strip()
    m = re.match(r'^%s$' % PackageName.template, self.fullpath)

    if m is None:
      raise ValueError('Bad package name (%s)' % fullpath)

    for attr in ('fullname', 'category', 'name', 'branch', 'version', 'fullversion', 'tag', 'rc', 'entire'):
      setattr(self, attr, m.group(attr))

  def is_simple(self):
    return self.name == self.fullname

  def __eq__(self, other):
    return self.fullname == other.fullname and self.category == other.category

  def hash(self):
    return hash('%s/%s' % (self.category if self.category else '', self.name))

  def __hash__(self):
    return self.hash()

  def __str__(self):
    return self.fullpath

  def __repr__(self):
    return '<pn: %s>' % self.fullpath

  def env(self):
    return {
      'P': self.fullname,
      'PN': self.name,
      'PF': self.fullname,
      'PV': self.version if self.version else '',
      'PVR': self.fullversion if self.fullversion else '',
      'CATEGORY': self.category if self.category else '',
    }

