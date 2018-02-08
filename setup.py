from os import system as sh
from setuptools import setup
from setuptools.command.install import install
from lib.rbuild.version import version as app_version

class Install(install):
  def run(self):
    if sh('cd rbapi && make && cp output/rbapi ../bin/'):
      exit('rbapi build failed')
    install.run(self)

setup (
  name = 'Rbuild',
  version = app_version['version'],
  description = 'Rbuild build tool',
  author = 'Levenkov Artem',
  author_email = 'levenkov.artem@globinform.ru',
  url = 'http://www.globinform.ru/',
  packages = [
    'rbuild',
    'rbuild.cmd',
    'rbuild.scripts',
  ],
  package_dir = { 'rbuild': 'lib/rbuild' },
  package_data = { 'rbuild.scripts': [ '*.sh' ] },
  include_package_data = True,
  scripts = [ 'bin/rbuild' ], 
  data_files = [
    ( '/usr/bin', [ 'bin/rbapi' ] ),
  ],
  install_requires = [
    'yaml',
    'ply'
  ],
  cmdclass = {
    'install': Install
  }
)

