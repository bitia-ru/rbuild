def dfs(parent, nodes, deps, visited_hook, visited=[], level=0):
  if not visited_hook: visited_hook = lambda n,p,l: True 
  for node in nodes:
    if node in visited: continue
    dfs(node, deps(node), deps, visited_hook, visited, level+1)
    if visited_hook(node, parent, level):
      visited.append(node)

