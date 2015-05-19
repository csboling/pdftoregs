import re
from ..datastruct.regextree import RegexTree

class ToC:
  """Object for stripping the information we care about
  out of a table of contents, given appropriate regexes.
  """
  def __init__(self, name, text,
               section_re, entry_re,
               extras):
    self.t = RegexTree(DeviceNode(name),
                       [(section_re, PeripheralNode),
                        (entry_re,   RegisterNode)])
    self.t.build(text)
    self.extras = extras

  def __str__(self):
    return str(self.t.root)

  def __len__(self):
    return len(self.t.root)

  def __iter__(self):
    self._nodes = iter(self.t.root)
    return self

  def __next__(self):
    for node in self._nodes:
      if isinstance(node.value, PeripheralNode):
        try:
          extra_reg = self.extras[node.value.name]
        except KeyError:
          extra_reg = []
        for regfields in extra_reg:
          node.add(RegisterNode.create(regfields))
        continue
      if isinstance(node.value, RegisterNode):
        return node
    raise StopIteration

class FilterTree(RegexTree):
  class Finished(Exception):
    pass
  class Empty(Exception):
    pass

  def __init__(self, name,
               filter_re, predicate,
               levels):
    super().__init__(name, [(filter_re, self.factory)] + levels)
    self.predicate = predicate

  def __enter__(self):
    return self

  def __exit__(self, etype, evalue, tb):
    if isinstance(evalue, self.Finished):
      nodes = self.root.children.values()
      if len(nodes) == 0:
        raise self.Empty
      else:
        self.accepted = iter(nodes)
      return True
    else:
      self.accepted = iter([])

  def factory(self, match):
    if self.predicate(match):
      raise self.Finished
    else:
      return None

  def build(self, text):
    with self as ft:
      super().build(text)

class DeviceNode:
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return self.name

class PeripheralNode:
  def __init__(self, match):
    section = match.group('section')
    print(section)
    m = re.search(r'[\w\s]*\((?P<name>\w+)\)[\w\s]*', section)
    if m:
      self.name = m.group('name')
    else:
      self.name = ''.join(section.split())

  def __str__(self):
    return self.name

class RegisterNode:
  def __init__(self, match):
    self.name   = match.group('regname')
    self.offset = int(match.group('offset'), 16)
    try:
      self.reset = int(match.group('reset'), 16)
    except TypeError:
      self.reset = 0
    self.page   = int(match.group('pagenum'))

  @staticmethod
  def create(fields):
    """Alternate constructor, directly from dict of values instead of regex match.
    """
    self = object.__new__(RegisterNode)
    self.__dict__.update(fields)
    return self

  def __str__(self):
    return 'Reg {} p{}'.format(self.name, self.page)

class BitfieldTree:
  def __init__(self, name, text, header_re, line_re):
    self.name = name
    self._t = FilterTree(self.name,
                         header_re, self.predicate,
                         [(line_re, BitfieldNode)])
    self._t.build(text)

  def predicate(self, match):
    candidates = [match.group('regname')]
    try:
      # guess that the name is given by the first capital letters
      candidates += ''.join(re.findall(r'(?<![A-Z])[A-Z]',
                            match.group('fullname')))
    except TypeError:
      pass
    if self.name in candidates:
      return False
    else:
      return True

  def __iter__(self):
    return self

  def __next__(self):
    return next(self._t.accepted)

class BitfieldNode:
  @staticmethod
  def get_slice(hi, lo):
    return (int(hi), int(lo) if lo else int(hi))

  def __init__(self, match):
    self.name = match.group('fieldname')
    self.physbits = self.get_slice(match.group('hibit'),
                                   match.group('lobit'))
    logbits = match.group('hibit_log'), match.group('lobit_log')
    if logbits == (None, None):
      self.logbits = self.physbits
    else:
      self.logbits = self.get_slice(*logbits)
    self.reset    = int(match.group('reset'), 16)
#    print('    bitfield: {} [{}:{}]'.format(self.name, *self.physbits))

  def __str__(self):
    return self.name
