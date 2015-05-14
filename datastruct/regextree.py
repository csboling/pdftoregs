import re
from ..datastruct.tree import Tree

class RegexTree:
  @staticmethod
  def compile_pair(levelpair):
    pattern, other = levelpair
    return (re.compile(pattern), other)

  def __init__(self, name, levels):
    self.levels = list(map(self.compile_pair, levels))
    self.depth = 0
    self.root = Tree([name])
    self._t = self.root

  def __str__(self):
    return str(self.root)

  def feed(self, line):
    for depth, (pattern, factory) in enumerate(self.levels[:self.depth+1]):
      m = pattern.search(line)
      if m:
        if depth < self.depth:
          self._t = self._t.ascend(self.depth - depth)
          self.depth = depth + 1
        else:
          self.depth += 1
        node = factory(m)
        if node != None:
          self._t = self._t.add(node)

  def build(self, text):
    for line in iter(text.splitlines()):
      self.feed(line)
