import unittest
import collections
import itertools
import pdftoregs.datastruct.tree as uut

class TestTree(unittest.TestCase):
  @classmethod
  def flatten(cls, iterable):
    for i in iterable:
      if isinstance(i, collections.Iterable) and not isinstance(i, (str, bytes)):
        for j in cls.flatten(i):
          yield j
      else:
        yield i

  class Counter:
    count = 0
    def __init__(self, *args, **kwargs):
      self.value = self.count
      self.count += 1

    def __str__(self):
      return str(self.value)

  def test_show_tree(self):
    initializer = ['root',
                   ['left',
                    ['leafA', []],
                    ['leafB', []],
                   ],
                   ['right',
                    ['leafC', []],
                    ['farright',
                     ['leafD', []]
                    ]
                   ],
                  ]
    t = uut.Tree(initializer)
    self.assertEqual(t.to_list(), initializer)
    self.assertEqual(list(node.value for node in t),
                     list(self.flatten(initializer)))
    self.assertEqual(t.__str__(),
                     '\n'.join([
                           '+-- root',
                           '|   +-- left',
                           '|   |   +-- leafA',
                           '|   |   +-- leafB',
                           '|   +-- right',
                           '|   |   +-- leafC',
                           '|   |   +-- farright',
                           '|   |   |   +-- leafD',
                          '']))

if __name__ == '__main__':
  unittest.main()
