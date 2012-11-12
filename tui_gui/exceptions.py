#! /usr/bin/env python
# vim: set ai softtabstop=2 shiftwidth=2 tabstop=80 :

class MenuParseError(BaseException):
  def __init__(self, element_type, element_value):
    self.element_type = element_type
    self.element_value = element_value

  def __str__(self):
    return "Duplicate usage of "+self.element_type+" ("+self.element_value+")"
class MenuNoItemFound(BaseException):
  def __init__(self, element_type, element_value):
    self.element_type = element_type
    self.element_value = element_value

  def __str__(self):
    return "Can't find "+self.element_type+" "+self.element_value