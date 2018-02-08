from rbuild.pkgname import PackageName

# cond_tpl : tpl
#          | cond_ident OP cond_tpl CP
# 
# cond_ident : questioned_useflag
#            | OR
# 
# tpl : pkg_name
#     | restrictions pkg_name
#     | pkg_name required_useflags
#     | restrictions pkg_name required_useflags


class PackageTemplate:
  def __init__(self, tpl):
    self.tpl = tpl

    # check tpl

  def __eq__(self, obj):
    if type(obj) == PackageTemplate:
      return self.tpl == obj.tpl

    if type(obj) == PackageName:
      return self.match_pkg(obj)

    raise Exception('obj has invalid type')

  def match_pkg(self, pkg):
    r"(?P<blockier>\!|\!\!)(?P<cond>\>\=|\>|\~|\=|\<\=|\<)"

