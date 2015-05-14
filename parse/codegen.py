class Indent:
  def __init__(self, f, tabstop=2):
    self.f = f
    self.tabstop = tabstop
    self.level = 0

  def write(self, *b, indent=False):
    if indent:
      self.f.write(' '*self.tabstop*self.level)
    for x in b:
      self.f.write(x)

  def close(self):
    self.f.close()

  def writeln(self, *b):
    if len(b):
      self.write(indent = True)
      for x in b:
        self.write(x)
    self.write('\n')

  def indent(self, pre=''):
    if pre:
      self.writeln(pre)
    self.level += 1

  def unindent(self, post=''):
    if self.level > 0:
      self.level -= 1
    if post:
      self.writeln(post)
