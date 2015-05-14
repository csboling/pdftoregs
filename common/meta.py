def attach_member_classes(template, members):
  """Class decorator to programmatically generate 'virtual' member
  classes from a template.

  >>> @attach_member_classes(object, ['Foo', 'Bar'])
  ... class Quux:
  ...   pass
  ...
  >>> Quux.Foo
  <class '__main__.Quux.Foo'>
  >>> Quux.Bar
  <class '__main__.Quux.Bar'>
  """
  def wrapper(cls):
    cls.ATTACHED_MEMBERS = members
    for m in members:
      setattr(cls, m,
              type(cls.__name__ + '.' + m, (template,), {}))
    return cls
  return wrapper

if __name__ == '__main__':
  import doctest
  doctest.testmod()
