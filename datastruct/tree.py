import collections
import copy
import functools

class Tree:
  class _Leaf:
    def __str__(self):
      return 'nil'
  _leaf = _Leaf()

  def __init__(self, nodes=None):
    self.parent = None
    self.depth = 0
    self.reset()
    if nodes:
      self.value, *children = nodes
      for c in children:
        self.add_tree(Tree(c))
    else:
      self.value = self._leaf

    self.iterator = self.__iter__()

  @property
  def value(self):
    return self._value

  @value.setter
  def value(self, other):
    self._value = other
    self.key = str(self.value)

  ###
  # Display and reformatting
  #
  def show_branch(self, depth=0):
    return ('|   '*depth + '+-- ' + str(self.value) + '\n')
  def __str__(self, depth=0):
    if self.value == self._leaf:
      return ''
    ret = self.show_branch(depth)
    for c in self.children.values():
      ret += c.__str__(depth + 1)
    return ret

  def to_list(self):
    if self.value == self._leaf:
      return []
    return [self.value] + [x.to_list() for x in self.children.values()]

  def map(self, f, inplace=False):
    """Destructively map a function over the values stored by the tree.
    """
    for node in self:
      node.value = f(node.value)
    return self

  def fold(self, f, zero):
    x = f(self.value, zero)
    return functools.reduce(f, (c.fold(f, x) for c in self.children.values()))

  ###
  # Modification
  #
  def add(self, child):
    t = Tree()
    t.value = child
    t.parent = self
    t.depth = self.depth + 1
    self.children[t.key] = t
    return t

  def add_tree(self, child):
    child.parent = self
    child.depth = self.depth + 1
    self.children[child.key] = child

  def prune(self, depth, threshold=1):
    """Prune all subtrees with fewer than 'threshold' children,
    stopping after reaching a depth of 'depth'
    """
    if len(self.children) < threshold:
      del self.parent.children[self.key]
    if self.depth < depth:
      for c in self.children.values():
        c.prune(depth, threshold)

  def reset(self):
    self.children = collections.OrderedDict()

  ###
  # Navigation
  #
  def __iter__(self):
    """Breadth-first traversal.
    """
    if self.value != self._leaf:
      yield self
    for child in self.children.values():
      if child.value != child._leaf:
        for x in iter(child):
          yield x

  def __next__(self):
    try:
      return next(self.iterator)
    except StopIteration:
      self.iterator = iter(self)
      raise

  def walk(self, ctx, operation):
    with operation(ctx, self.value) as new_ctx:
      for child in self.children.values():
        child.walk(new_ctx, operation)

  def ascend(self, k):
    curr = self
    for _ in range(k):
      if not curr.parent:
        break
      curr = curr.parent
    return curr
