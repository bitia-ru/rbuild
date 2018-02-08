#!/bin/bash

Name=Rbuild
PYTHON=${PYTHON:-python3.3}

DEST_ROOT=/usr
DEST_BIN=${DEST_ROOT}/bin
PYTHON_LIBDIR=$(${PYTHON} -c "import distutils.sysconfig; print(distutils.sysconfig.get_python_lib());")

BINS='rbuild rbapi'
PKGS='rbuild'

die() {
  echo "$@" 2>&1
  exit 1
}

[[ -d "${PYTHON_LIBDIR}" ]] || die "Can find python library directory"
[[ -d "${DEST_BIN}" ]] || die "Binary destination directory is not exist (${DEST_BIN})"

check_prerequisites() {
  # Checking yaml
  ${PYTHON} -c "import yaml" 2>/dev/null || die "Install yaml package for ${PYTHON}"
}

check_installed() {
  for bin in ${BINS}; do
    [[ -f "${DEST_BIN%/}/$(basename ${bin})" ]] && return 0
  done

  for pkg in ${PKGS}; do
    [[ -d "${PYTHON_LIBDIR%/}/${pkg}" ]] && return 0
  done

  return 1
}

do_build() {
  pushd rbapi >/dev/null

  [[ -f Makefile ]] || unimake || return 1

  make

  cp output/rbapi ../bin/

  popd >/dev/null
}

do_install() {
  ${PYTHON} setup.py install
}

do_uninstall() {
  for pkg in ${PKGS}; do
    rm -rvf ${PYTHON_LIBDIR}/${pkg}
  done

  for bin in ${BINS}; do
    rm -vf ${DEST_BIN}/${bin}
  done
}

if [[ "x$1" = "x-u" ]]; then 
  do_uninstall
else
  do_build || die "Can't build platform-dependent code"
  check_installed && die "${Name} already installed, try to uninstall it first."
  check_prerequisites
  do_install
fi

