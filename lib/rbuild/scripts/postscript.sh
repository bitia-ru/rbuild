for hook in ${RB_HOOKS_PRE[${RB_PHASE}]}; do
  [[ "$(type -t $hook)" == function ]] && eval "$hook"
done

for hook in ${RB_HOOKS_PRE}; do
  [[ "$(type -t $hook)" == function ]] && eval "$hook"
done

