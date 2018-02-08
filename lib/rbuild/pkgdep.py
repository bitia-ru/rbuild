from rbuild.pkgname import PackageName
from rbuild.err import *
from copy import deepcopy
import re
import ply.lex as lex
import ply.yacc as yacc


tokens = [
  'USECOND',
  'PKGNAME1',
  'PKGNAME2',
  'PKGNAME3',
  'SPACE',
  'GT',
  'LT',
  'GTE',
  'LTE',
  'EQ',
  'TLD',
  'OB',
  'CB',
  'OBR',
  'CBR',
  'EXCL',
  'DEXCL',
  'DOR',
  'COLON',
  'DCOLON',
  'SLOT',
  'BSLSH',
  'WORD1',
  'WORD2',
  'WORD3',
  'COMMA',
  'AST'
]


t_WORD1    = r'[a-zA-Z][a-zA-Z012-9_]+'
t_WORD2    = r'\-[a-zA-Z][a-zA-Z0-9_]+'
t_WORD3    = r'[a-zA-Z][a-zA-Z012-9_-]+'
t_USECOND  = r'[abcd-zA-Z0123456789_]+\?'
t_PKGNAME1 = r'([a-zA-Z0-9_-]+\/)?[a-zA-Z0-9_\-\+]+\-([0-9]+\.)*[0-9]+([a-zA-Z]|\-[Rr][Cc][0-9]+)?'
t_PKGNAME2 = r'[a-zA-Z0-9_-]+\/[a-zA-Z0-9_\-\+]+'
t_PKGNAME3 = r'[a-zA-Z0-9_-]+'
t_SPACE = r'[\n\t ]+'
t_GT = r'\>'
t_LT = r'\<'
t_GTE = r'\>\='
t_LTE = r'\<\='
t_TLD = r'\~'
t_OB = r'\('
t_CB = r'\)'
t_OBR = r'\['
t_CBR = r'\]'
t_EXCL = r'\!'
t_DEXCL = r'\!\!'
t_DOR = r'\|\|'
t_COLON = r'\:'
t_DCOLON = r'\:\:'
t_BSLSH = r'\/'
t_EQ = r'\='
t_SLOT = r'([0-9]+\.)*[0-9]+'
t_AST = r'\*'
t_COMMA = r'\,'

t_ignore = ''

class PackageDep:
  def __init__(self, deplist):
    self.cond = None
    self.deplist = deplist

  def parse2tasks(prj, uses, phase, s):
    if not s: return []
    lexer = lex.lex()
    parser = yacc.yacc(debug=0, write_tables=0)
    deps = parser.parse(s)

    res = []

    for dep in PackageDep.parse_result(prj, uses, deps):
      pkg = prj.find_pkg(dep['pkgname'])
      ph = None
      if 'phase' in dep: ph = dep['phase']
      else:
        if pkg.dummy:
          ph = str(phase)
        else:
          if 'pkg_defphases' in pkg._cfg and 'depend' in pkg._cfg['pkg_defphases']:
            ph = pkg._cfg['pkg_defphases']['depend']
          elif 'pkg_defphases' in phase.cfg and 'depend' in phase.cfg['pkg_defphases']:
            ph = phase.cfg['pkg_defphases']['depend']
          elif 'depend' in prj.cfg['pkg_defphases']:
            ph = prj.cfg['pkg_defphases']['depend']
          else:
            ph = str(prj.phase_defs['phase'])
      res.append(prj.task(pkg, prj.phases[ph]))

    req_unique = []

    [ req_unique.append(r) for r in res if r not in req_unique ]

    return req_unique

  def parse_result(prj, uses, deps, res=[], context={}):
    res=list(res)
    for dep in deps:
      if type(dep) == dict:
        dep_with_context = dict(dep)
        dep_with_context.update({ 'context': context })
        res.append(dep_with_context)
      elif type(dep) == PackageDep:
        context_new = deepcopy(context)
        if dep.cond:
          if dep.cond == '||':
            raise Exception('Unsupported || in DEPEND')

          m = re.match(r"^(?P<not>\!?)(?P<use>\w+)\?$", dep.cond)

          if not m:
            raise Exception('Bad condition %s in DEPEND' % dep.cond)
          
          use, n = m.group('use'), ( True if m.group('not') == '!' else False )

          use_list = context_new.get('use', set())
          nuse_list = context_new.get('nuse', set())

          if not n: use_list.add(use)
          else: nuse_list.add(use)

          if uses is not None:
            if use_list & uses != use_list: continue
            if nuse_list & uses: continue

        subdeps = dep.deplist

        if type(subdeps) != list: subdeps = [ subdeps ]

        res = PackageDep.parse_result(prj, uses, subdeps, res, context_new)

    return res

  def parse(s):
    if not s: return []
    lexer = lex.lex()
    parser = yacc.yacc(debug=0, write_tables=0)
    return parser.parse(s)

  def __repr__(self):
    return '<cond: %s deplist: %s>' % (self.cond, ', '.join([ str(e) for e in self.deplist ]))

  def __eq__(self, pkgname):
    if type(self.deplist[0]) != dict: return False

    selfpkgname = PackageName(self.deplist[0]['pkgname'])
    op = self.deplist[0]['ver']

    if op == '=': return selfpkgname == pkgname
    elif op == '>=': return selfpkgname >= pkgname
    elif op == '<=': return selfpkgname <= pkgname
    elif op == '<': return selfpkgname < pkgname
    elif op == '>': return selfpkgname > pkgname
    else: return selfpkgname == pkgname

def t_error(t):
    raise RBuildError("Invalid DEPEND: Illegal character '%s'" % t.value[0])

def p_error(t):
    print("Error: " + str(t))

def p_deplist(t):
  '''deplist : dep
             | deplist SPACE dep'''
  if len(t) == 2: t[0] = [ t[1], ]
  else: t[0] = t[1] + [ t[3], ]

def p_dep(t):
  '''dep : pkgname_phased 
         | usecond SPACE OB SPACE deplist SPACE CB
         | DOR SPACE OB SPACE deplist SPACE CB'''
  if len(t) == 2: t[0] = PackageDep([ t[1], ])
  else:
    if len(t[5]) == 1: t[0] = t[5][0]
    else: t[0] = PackageDep(t[5])
    t[0].cond = t[1]

def p_pkgname_phased(t):
  '''pkgname_phased : pkgname
                      | pkgname DCOLON WORD1
                      | pkgname DCOLON WORD3'''
  if len(t) == 2: t[0] = t[1]
  else:
    t[1]['phase'] = t[3]
    t[0] = t[1]

def p_pkgname(t):
  '''pkgname : pkgname_prefixed
             | pkgname_prefixed pkgslot
             | pkgname_prefixed pkguse
             | pkgname_prefixed pkgslot pkguse'''
  if len(t) == 3:
    if type(t[2]) == str:
      t[1]['slot'] = t[2]
      t[0] = t[1]
    else:
      t[1]['use'] = t[2]
      t[0] = t[1]
  elif len(t) == 4:
    t[1]['slot'] = t[2]
    t[1]['use'] = t[3]
    t[0] = t[1]
  else:
    t[0] = t[1]

def p_pkgname_prefixed(t):
  '''pkgname_prefixed : pkgpref PKGNAME1
                      | PKGNAME2
                      | PKGNAME3
                      | WORD1
                      | WORD3'''
  if len(t) == 2:
    t[0] = { 'pkgname': t[1] }
  else:
    t[0] = { 'pkgname': t[2] }
    for e in t[1]:
      if e == '!' or e == '!!': t[0]['blk'] = e
      else: t[0]['ver'] = e

def p_pkgslot(t):
  '''pkgslot : COLON SLOT
             | COLON SLOT EQ
             | COLON EQ
             | COLON AST
             | COLON SLOT BSLSH SLOT'''
  if len(t) == 3:
    t[0] = t[2]
  elif len(t) == 4:
    t[0] = t[2] + t[3]
  else:
    t[0] = t[2] + ';' + t[4]

def p_pkguse(t):
  '''pkguse : OBR uselist CBR'''
  t[0] = t[2]

def p_uselist(t):
  '''uselist : WORD1 
             | WORD2
             | uselist COMMA WORD1
             | uselist COMMA WORD2'''
  if len(t) == 2:
    t[0] = [ t[1], ]
  else:
    t[0] = t[1] + [ t[3], ]

def p_usecond(t):
  '''usecond : USECOND
             | EXCL USECOND'''
  t[0] = ''.join(t[1:])

def p_pkgpref(t):
  '''pkgpref : pkgvercond
             | pkgblk
             | pkgblk pkgvercond'''
  t[0] = t[1:]

def p_pkgblk(t):
  '''pkgblk : EXCL
            | DEXCL'''
  t[0] = t[1]

def p_pkgvercond(t):
  '''pkgvercond : GT
                | GTE
                | LT
                | LTE
                | TLD
                | EQ'''
  t[0] = t[1]

def dep_lex(script):
  lexer = lex.lex()
  lexer.input(script)

  while True:
    tok = lexer.token()
    if not tok: 
      break
    print(tok)

