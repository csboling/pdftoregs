import logging
from importlib import import_module

from ...common.meta import attach_member_classes
from ...lex import register

class EmptyContext:
  def __init__(self, params):
    self.params = params

  def __enter__(self):
    return self

  def __exit__(self, t, v, tb):
    pass

class NodeTemplate:
  def __init__(self, node):
    self.node = node
    self.name = self.node.name

  def __enter__(self):
    return self

  def __exit__(self, etype, evalue, tb):
    pass

  def inherit_ctx(self, ctx):
    self.parent_ctx = ctx
    return self

@attach_member_classes(NodeTemplate,
                       ['Device',
                        'Peripheral',
                        'Register',
                        'Bitfield'])
class BaseTranslator:
  @staticmethod
  def new(lang):
    try:
      return import_module('..' + lang + '_trans', __name__).Translator()
    except (ImportError, AttributeError):
      logging.error('no translator "{}" found'.format(lang))

  @property
  def node_encoders(self):
    try:
      ret = self._node_encoders
    except AttributeError:
      ret = self._node_encoders = { getattr(register, x + 'Node') : getattr(self, x)
                                    for x in self.ATTACHED_MEMBERS
                                  }
    return ret

  def encode(self, ctx, v):
    emitter = self.node_encoders[type(v)](v)
    return emitter.inherit_ctx(ctx)

  def walk(self, tree, params):
    tree.walk(EmptyContext(params), self.encode)
