import subprocess

import scanpdf.lex.register as register

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

  def build(self, last_page, subsequent_pages):
    self.toc = register.ToC(self.name,
                            self.get_text(0, last_page),
                            self.regexes['Section'],
                            self.regexes['Register'])
    for entry in self.toc:
      v = entry.value
      print('register {}, p{}'.format(v.name, v.page))
      if v.name in self.exceptions:
        continue
      tablepgs = self.get_text(v.page,
                               v.page + subsequent_pages)

      try:
        for field in register.BitfieldTree(v.name, tablepgs,
                                           self.regexes['BitfieldHeader'],
                                           self.regexes['BitfieldLine']):
          entry.add_tree(field)
      except register.FilterTree.Empty:
        self.exceptions.append(entry.value)
