set -a

declare -A USE FEATURES pkg pkg_defphases

a2json() {
  local k i=0

  for k in $(eval echo "\${!${1}[@]}"); do
    eval "local v=\"\${${1}[${k}]}\""
    eval "__KEY${i}=\"\${k}\""
    eval "__VALUE${i}=\"\${v}\""
    i=$((i+1))
  done

  command env2json -a __KEY __VALUE
}

env2json() {
(
  for a in $(alist); do
    eval "unset ${a}; ${a}='JSON:$(a2json ${a})'"
  done
  unset a
  unset -f `declare -F | cut -d' ' -f3`
  command env2json
)
}

alist() {
  declare -A | grep -e '^declare' | sed "s,^declare -[a-zA-Z]\+ \([^_][^=]*\).*$,\1," | sed '/^\(declare\|BASH_\).*/d'
}

# default config API functionality
pre() { :; }
rbsc() { :; }

phase_file() {
  echo "${PHASE_DIR}/.${CATEGORY}.${PF}.${PHASE}.done"
}

phase_touch() {
  touch "$(phase_file)"
}

phase_test() {
  test -d "${PHASE_DIR}" && stat -c %Y "$(phase_file)" 2>/dev/null || echo 0
}

pkg_defphases[stage]=build

