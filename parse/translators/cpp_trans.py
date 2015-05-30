from contextlib import contextmanager
import re
import os
from ..translators.translator import BaseTranslator, NodeTemplate
from ..codegen import Indent

join = os.path.join

class Translator(BaseTranslator):
  def __init__(self):
    pass

  @staticmethod
  def unguard(name):
    return ('#endif  /* __{name}_REGS_HPP_GUARD */\n').format(name=name)

  class Device(NodeTemplate):
    def __enter__(self):
      self.oldpwd = os.getcwd()
      os.chdir(self.outdir)
      return self

    def __exit__(self, etype, evalue, tb):
      os.chdir(self.oldpwd)

    def inherit_ctx(self, ctx):
      ctx.device = self
      self.parent_ctx = ctx
      self.outdir = join(ctx.params['OutputDir'], 'auto')
      os.makedirs(self.outdir, exist_ok=True)
      return self

  class Peripheral(NodeTemplate):
    def __init__(self, node):
      self.node = node
      m = re.search(r'(?P<name>[A-Z0-9\s]+)Registers?', node.name)
      if m:
        name = m.group('name')
      else:
        name = node.name
      self.node.name = re.sub(r'\s', '_', name.strip())

    def inherit_ctx(self, ctx):
      self.parent_ctx = ctx
      return self

    def __enter__(self):
      self.header = CppHeader(self.node.name)
      self.header.__enter__()
      self.source = CppSource(self.node.name)
      self.source.__enter__()
      return self

    def __exit__(self, *args, **kwargs):
      self.header.__exit__(*args, **kwargs)
      self.source.__exit__(*args, **kwargs)

  class Register(NodeTemplate):
    def __enter__(self):
      self.hdrf = self.parent_ctx.header.outf
      self.srcf = self.parent_ctx.source.outf
      self.struct  = CppStructUnion(self.node.name, self.hdrf)
      self.struct.__enter__()
      self.members = CppMemberInit(cls=self.parent_ctx.node.name,
                                   name=self.node.name,
                                   addr=self.node.offset,
                                   outf=self.srcf)
      self.members.__enter__()
      return self

    def __exit__(self, *args, **kwargs):
      self.struct.__exit__(*args, **kwargs)
      self.members.__exit__(*args, **kwargs)

  class Bitfield(NodeTemplate):
    @staticmethod
    def bitlen(bits):
      return abs(bits[0] - bits[1]) + 1

    def __enter__(self):
      self.parent_ctx.hdrf.writeln('uint16_t {name} : {width};'.format(name=self.node.name,
                                                                       width=self.bitlen(self.node.physbits)))
      self.parent_ctx.struct.field_ct += 1

class CppFile(NodeTemplate):
  def __init__(self, name, baseclass=None):
    self.name = name
    self.baseclass = baseclass

  def __enter__(self):
    fname = re.sub('/', '_', self.name + self.extension)
    self.outf = Indent(open(fname, 'w'))
    return self

  def __exit__(self, *args, **kwargs):
    self.outf.close()

  def guard(self):
    self.outf.write(('#ifndef __{name}_REGS_HPP_GUARD\n'
                     '#define __{name}_REGS_HPP_GUARD\n').format(name=self.name))
    self.outf.writeln()
    self.outf.writeln('#include <stdint.h>')
    self.outf.writeln()
    self.outf.writeln('#ifndef max')
    self.outf.writeln('#define max(a, b) (((a) > (b)) ? (a) : (b))')
    self.outf.writeln('#endif  /* #ifndef max */')
    self.outf.writeln()

  def unguard(self):
    self.outf.writeln('#endif  /* #ifndef __{name}_REGS_HPP_GUARD */'.format(name=self.name))
    self.outf.writeln()

  def namespace(self):
    self.outf.writeln('namespace periph')
    self.outf.indent('{')

  def unnamespace(self):
    self.outf.unindent('}')

  def startclass(self):
    self.outf.write('class {}_regs'.format(self.name), indent=True)
    if self.baseclass:
      self.outf.write(' : {baseclass}'.format(baseclass=self.baseclass))
    self.outf.write('\n')
    self.outf.indent('{')

  def stopclass(self):
    self.outf.unindent('};')

class CppHeader(CppFile):
  directory = 'include'
  extension = '_regs.hpp'

  def __enter__(self):
    super().__enter__()
    self.guard()
    self.namespace()
    self.startclass()
    self.prot_ctx = self.protected()
    return self.prot_ctx.__enter__()

  def __exit__(self, *args, **kwargs):
    self.prot_ctx.__exit__(*args, **kwargs)
    self.stopclass()
    self.unnamespace()
    self.unguard()
    super().__exit__(self, *args, **kwargs)

  def inherit_ctx(self, ctx):
    self.prot_ctx.parent_ctx = ctx
    return self.prot_ctx

  @contextmanager
  def protected(self):
    self.outf.writeln('protected:')
    self.outf.indent()
    yield self
    self.outf.unindent()

  @contextmanager
  def public(self):
    self.outf.writeln('public:')
    self.outf.indent()
    yield self
    self.outf.unindent()

  def ctor(self):
    self.outf.writeln(' {name}();'.format(name=self.name))

  def dtor(self):
    self.outf.writeln('~{name}();'.format(name=self.name))

class CppSource(CppFile):
  directory = 'src'
  extension = '_regs.cpp'

  def __enter__(self):
    super().__enter__()
    self.include()
    self.namespace()
    return self

  def __exit__(self, *args, **kwargs):
    self.unnamespace()
    return super().__exit__(*args, **kwargs)

  def include(self):
    self.outf.writeln('#include "periph/regs/{name}_regs.hpp"'.format(name=self.name))
    self.outf.writeln()

  def ctor(self):
    self.outf.writeln()
    self.outf.writeln('{name}::{name}()'.format(name=self.name))
    self.outf.writeln('{')
    self.outf.writeln('}')

  def dtor(self):
    self.outf.writeln()
    self.outf.writeln('{name}::~{name}()'.format(name=self.name))
    self.outf.writeln('{')
    self.outf.writeln('}')

class CppStructUnion:
  def __init__(self, name, outf):
    self.name = name
    self.outf = outf

  def __enter__(self):
    self.outf.writeln('static volatile ioport union {name}_t'.format(name=self.name))
    self.outf.indent('{')
    self.outf.writeln('struct {name}_struct_t'.format(name=self.name))
    self.outf.indent('{')
    self.field_ct = 0
    return self

  def __exit__(self, etype, evalue, tb):
    if self.field_ct == 0:
      self.outf.writeln('uint16_t nothing : 16;')
    self.outf.unindent('} bits;')
    self.outf.writeln('uint16_t bytes[max(sizeof(struct {name}_struct_t), 1)];'.format(name=self.name))
    self.outf.unindent('}} * const {name};'.format(name=self.name))

class CppMemberInit:
  def __init__(self, cls, name, addr, outf):
    self.cls  = cls
    self.name = name
    self.addr = addr
    self.outf = outf

  def __enter__(self):
    self.outf.write(('volatile ioport union {cls}::{name}_t * const {cls}::{name} = \n'
                     '  (ioport union {cls}::{name}_t *) '
                     '0x{addr:04x};\n').format(cls=self.cls + '_regs',
                                               name=self.name,
                                               addr=self.addr),
                     indent=True)

  def __exit__(self, etype, evalue, tb):
    pass
