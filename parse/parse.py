import os.path
from ..parse.translators.translator import BaseTranslator

class CodeGenerator:
  def __init__(self, lang, tree, params):
    self.translator = BaseTranslator.new(lang)
    self.translator.walk(tree, params)

  def write(self, outdir):
    for unit in self.translator:
      print('unit: {}'.format(node.name))
      with os.path.join(outdir,
                        node.name + node.extension + '.auto', 'w') as f:
        f.write(unit)
