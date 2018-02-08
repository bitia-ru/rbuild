rb_do() {
  local funcname=$1

  if [[ "$(type -t $funcname)" != "function" ]]; then
    echo "Function '${funcname}' is not defined" 1>&2
    exit 1
  fi

  eval "$@"
}

rb() {
  ${RB_BIN_PATH}/rbapi ${RB_LIB_ADDR} "$@"
}

rb_env() {
(
  for a in $(rb_alist); do
    eval "unset ${a}; export ${a}='JSON:$(rb_a2json ${a})'"
  done
  unset a
  unset -f `declare -F | cut -d' ' -f3`
  ${RB_BIN_PATH}/env2json
)
}

rb_a2json() {
  local k i=0

  for k in $(eval echo "\${!${1}[@]}"); do
    eval "local v=\"\${${1}[${k}]}\""
    eval "export __KEY${i}=\"\${k}\""
    eval "export __VALUE${i}=\"\${v}\""
    i=$((i+1))
  done

  ${RB_BIN_PATH}/env2json -a __KEY __VALUE
}

rb_alist() {
  declare -A | grep -e '^declare' | sed "s,^declare -[a-zA-Z]\+ \([^_].*\)\='.*$,\1," | sed '/^\(declare\|BASH_\).*/d'
}

declare -A RB_PKG_DEPS RB_PKG_REQS RB_HOOKS_PRE

