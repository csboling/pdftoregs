import re
import os
import shutil

from pdftoregs.lex import lex
from pdftoregs.parse import parse

module_dir = os.path.dirname(os.path.abspath(__file__))

def lex_manual(name, settings):
  lexer = lex.LexPDF(name      = name,
                     pdftotext = settings['PdfToTextBin'],
                     pdf_fname = settings['PdfManual'],
                     regexes   = { k : settings[k + 'Regex']
                                   for k in ['Section',
                                             'Register',
                                             'BitfieldHeader',
                                             'BitfieldLine',
                                            ] },
                     exceptions = settings['RegisterExceptions'])
  lexer.build(settings['EndOfToC'], settings['SubsequentPages'])
  if lexer.exceptions:
    print('Skipped/could not lex: ' + '\n'.join(map(str, lexer.exceptions)))
  return lexer.toc.t.root

def parse_registers(lang, tree):
  codegen = parse.CodeGenerator(lang, tree)
  return codegen

def main(name, settings):
  pdftotext   = settings['PdfToTextBin']
  infile      = settings['PdfManual']
  lastToCPage = settings['EndOfToC']

  toc = lex_manual(name, settings)
  print(toc)

  source = parse.CodeGenerator(settings['OutputLanguage'], toc,
                               { 'OutputDir' : settings['OutputDir'] })

def get_args():
  import argparse
  argparser = argparse.ArgumentParser(
                description=
                """Extract text-converted pages from a PDF, given
                a regex that locates them in the table of
                contents.
                """)
  argparser.add_argument('--cfgfile', type=str, nargs='?',
                         default=os.path.join(module_dir, 'scanpdf.cfg'))
  argparser.add_argument('--configuration', type=str, nargs='?',
                         help=
                         """Name of the configuration to load from the config file.
                         """,
                         default='TI_TMS320C5517')
  return argparser.parse_args()

def get_cfg(args):
  import configparser
  cfgparser = configparser.ConfigParser()
  cfgparser.read(args.cfgfile)
  configuration = cfgparser[args.configuration]

  config_dir = os.path.dirname(args.cfgfile)
  def path(p):
    if os.path.isabs(p):
      return p
    else:
      return os.path.join(config_dir, p)
  def compileVerbose(p):
    return re.compile(p, re.VERBOSE)

  settings = { k : f(configuration[k])
               for k, f in
               [ ('OutputLanguage',      str),
                 ('OutputDir',           path),

                 ('PdfToTextBin',        shutil.which),
                 ('PdfManual',           path),
                 ('SubsequentPages',     int),
                 ('EndOfToC',            int),
                 ('RegisterExceptions',  str.split),

                 ('SectionRegex',        compileVerbose),
                 ('RegisterRegex',       compileVerbose),
                 ('BitfieldHeaderRegex', compileVerbose),
                 ('BitfieldLineRegex',   compileVerbose),
               ]
             }
  return (args.configuration, settings)

if __name__ == '__main__':
  main(*get_cfg(get_args()))
