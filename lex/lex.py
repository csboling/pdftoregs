import subprocess

import pdftoregs.datastruct.tree as tree
import pdftoregs.lex.register as register

class LexPDF:
  def __init__(self, name,
               pdftotext, pdf_fname,
               regexes, exceptions):
    self.name = name
    self.default_args = [pdftotext,
                         '-layout',
                         '-enc', 'UTF-8',
                         pdf_fname, '-']
    self.regexes = regexes
    self.exceptions = exceptions

  def get_text(self, start, end):
    args = self.default_args + ['-f', str(start),
                                '-l', str(end)]
    return subprocess.check_output(args).decode('utf-8')

  def lex_entry(self, entry):
    v = entry.value
    if v.name in self.exceptions:
      return
    tablepgs = self.get_text(v.page,
                             v.page + self.subsequent_pages)

    try:
      for field in register.BitfieldTree(v.name, tablepgs,
                                         self.regexes['BitfieldHeader'],
                                         self.regexes['BitfieldLine']):
        entry.add_tree(field)
    except register.FilterTree.Empty:
      self.exceptions.append(v.name)
    print('register {}, p{}'.format(v.name, v.page))

  def build(self, last_page, subsequent_pages, extras):
    self.toc = register.ToC(self.name,
                            self.get_text(0, last_page),
                            self.regexes['Section'],
                            self.regexes['Register'],
                            extras)
    self.subsequent_pages = subsequent_pages
    for entry in self.toc:
      self.lex_entry(entry)
