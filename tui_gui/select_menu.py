#! /usr/bin/env python
# vim: set ai softtabstop=2 shiftwidth=2 tabstop=80 :

import sys
import os
import signal
import time
import subprocess
import re
from threading import Thread
# a more complete readline library from http://pypi.python.org/pypi/rl
# I only need get_rl_point() as extra
import rl.readline as readline
from tui_gui.exceptions import MenuParseError
from tui_gui.exceptions import MenuNoItemFound
from tui_gui.exceptions import NoDefaultTagInArguments
from tui_gui.exceptions import Timeout

__strip_re = re.compile(r'\\\[.*?\\\]')
def get_string_len(string):
  # use this function to strip the \[ \] sequence from the length calculation.
  # similar to what bash is doing
  stripped_string = strip_string(string)
  return len(stripped_string)
def print_string(string):
  # use this to handle color escape codes
  stripped_string = string.replace(r'\[','').replace(r'\]','').replace(r'\e', '\033')
  sys.stdout.write(stripped_string)
def strip_string(string):
  stripped_string = __strip_re.sub('', string)
  return stripped_string

class Item:
  def __init__(self, tag, label, text):
    self.tag = tag
    self.label = label
    self.text = text
  def get_label_len(self):
    return get_string_len(self.get_label())
  def get_text_len(self):
    return get_string_len(self.get_text())
  def get_label(self):
    return self.label
  def get_tag(self):
    return self.tag
  def get_text(self):
    return self.text

  @staticmethod
  def get_extra_len():
    return 3

  def show(self, max_label_len, max_text_len):
    text_len = get_string_len(self.get_label())
    sys.stdout.write(' '*(max_label_len-text_len))
    sys.stdout.write('[')
    print_string(self.get_label())
    sys.stdout.write('] ')
    text_len = get_string_len(self.get_text())
    print_string(self.get_text())
    sys.stdout.write(' '*(max_text_len-text_len))

  def __str__(self):
    return '{tag:'+self.get_tag()+',label:'+self.get_label()+',text:'+self.get_text()+'}'

class SubMenu:
  def __init__(self, title):
    self.items = []
    self.max_text_len = 0
    self.max_label_len = 0
    self.set_title(title)

  def add_item(self, tag, label, text):
    item = Item(tag, label, text)
    self.items.append(item)
    if item.get_label_len() > self.max_label_len:
      self.max_label_len = item.get_label_len()
    if item.get_text_len() > self.max_text_len:
      self.max_text_len= item.get_text_len()

  def get_items(self):
    return self.items
  def get_max_text_len(self):
    return self.max_text_len
  def get_max_label_len(self):
    return self.max_label_len
  def set_title(self, title):
    self.title = title
  def get_title(self):
    return self.title
  def get_title_len(self):
    return get_text_len(self.get_title())
  
  def find_item_by_label(self, label):
    for item in self.get_items():
      if strip_string(item.get_label()) == label:
        return item
    return None
  def find_item_by_tag(self, tag):
    for item in self.get_items():
      if strip_string(item.get_tag()) == tag:
        return item
    return None

  def show(self, screen_width = None): 
    if screen_width == None:
      screen_width = MenuScreen.get_width()
    if self.get_title():
      # TODO: allow shell escape codes
      sys.stdout.write('*%s*\n' % self.get_title())
    col_width = self.get_max_label_len() + self.get_max_text_len() + Item.get_extra_len() + 1
    nr_cols = max(1, screen_width / col_width)
    s_nr = 0
    for item in self.get_items():
      item.show(self.get_max_label_len(), self.get_max_text_len())
      s_nr += 1 
      if s_nr % nr_cols == 0:
        sys.stdout.write('\n')
      else:
        sys.stdout.write(' ')
    if s_nr % nr_cols != 0:
      sys.stdout.write('\n')
    sys.stdout.write('\n')

  def __str__(self):
    return '['+','.join([str(item) for item in self.get_items()])+']'
    
class Menu:
  CANCELLED = 'cancelled'
  def __init__(self, args, prompt, default_tag=None, timeout=None, item_format='label,text,tag', item_delimiter='|', element_delimiter=','):
    self.clear()
    self.set_prompt(prompt)
    if not isinstance(timeout, float) or timeout <= 0:
      timeout = None
    self.timeout = timeout
    self.default_tag = default_tag
    self.parse_args(args, item_format, item_delimiter, element_delimiter)

  def clear(self):
    self.submenus = []
    self._tags = set()
    self._labels = set()
    self._position_saved = False
    self.answer = ''

  def parse_args(self, args, item_format, item_delimiter, element_delimiter):
    if isinstance(args, str):
      args=(args,)

    self.clear()
    submenu = None
    default_tag_exists = False
    for arg in args:
      if arg.startswith('['):
        submenu = self.new_submenu(arg.lstrip('[').rstrip(']'))
      else:
        if submenu == None:
          submenu = self.new_submenu()
        for item in arg.split(item_delimiter):
          (label, text, tag) = item.split(element_delimiter)
          self.add_item(submenu, tag, label, text)
          if self.default_tag != None and tag == self.default_tag:
            default_tag_exists = True
        submenu = None
    if self.default_tag != None and default_tag_exists == False:
      raise NoDefaultTagInArguments(self.default_tag, arg)

  def new_submenu(self, title = None):
    sm = SubMenu(title)
    self.submenus.append(sm)
    return sm
  def add_item(self, submenu, tag, label, text):
    submenu.add_item(tag, label, text)
    self.check_duplicate_label(label)
    self.check_duplicate_tag(tag)

  def get_submenus(self):
    return self.submenus
  def get_prompt(self):
    return self.prompt
  def set_prompt(self, prompt):
    self.prompt = prompt
  def get_whole_screen(self):
    return self.whole_screen
  def set_whole_screen(self, whole_screen):
    self.whole_screen = whole_screen
    
  def check_duplicate_label(self, label):
    if label in self._labels:
      raise MenuParseError('label', label)
    else:
      self._labels.add(label)
  def check_duplicate_tag(self, tag):
    if tag in self._tags:
      raise MenuParseError('tag', tag)
    else:
      self._tags.add(tag)
  def find_item_by_label(self, label):
    for submenu in self.get_submenus():
      item = submenu.find_item_by_label(label)
      if item != None:
        return item
    raise MenuNoItemFound('label', label)
  def find_item_by_tag(self, tag):
    for submenu in self.get_submenus():
      item = submenu.find_item_by_tag(tag)
      if item != None:
        return item
    raise MenuNoItemFound('tag', tag)

  def show(self):
    MenuScreen.set_cursor_at(0,0)
    MenuScreen.clear_to_end_of_screen()
    for submenu in self.get_submenus():
      submenu.show()
      print
    sys.stdout.write(self.get_prompt())
    sys.stdout.write(readline.get_line_buffer()[:readline.get_rl_point()])
    MenuScreen.save_position()
    sys.stdout.write(readline.get_line_buffer()[readline.get_rl_point():])
    MenuScreen.restore_position()
    sys.stdout.flush()

  def handle(self):
    class __AskThread(Thread):
      def __init__(self, menu):
        Thread.__init__(self)
        self.menu = menu
        self.daemon = True
      def run(self):
        self.menu.answer = raw_input(self.menu.get_prompt())

    MenuScreen.clear()
    item = None
    while not item:
      self.show()
      sys.stdout.write('\r')
      try:
        self.answer = ''
        askThread = __AskThread(self)
        askThread.start()
        askThread.join(self.timeout)
        if self.answer == '':
          # no answer given or we timed out
          if askThread.is_alive():
            # we timed out, cleanup the thread if we can
            # an ugly hack, I know
            Thread._Thread__stop(askThread)
            # go to the next line
            print
            # turn echo'ing characters back on (was set off by readline)
            subprocess.check_output(['stty', 'echo'])
          if self.default_tag != None:
            item = self.find_item_by_tag(self.default_tag)
          else:
            item = Menu.CANCELLED
        else: 
          # an answer was given
          item = self.find_item_by_label(self.answer)
      except EOFError:
        # TODO: find out how to cancel on ESC instead of CTRL-D
        item = Menu.CANCELLED
    return item 

  def __str__(self):
    return '['+','.join([str(submenu) for submenu in self.get_submenus()])+']'

class MenuScreen:
  clear_string = subprocess.check_output(['tput', 'clear'])
  save_position_string = subprocess.check_output(['tput', 'sc'])
  restore_position_string = subprocess.check_output(['tput', 'rc'])
  clear_end_of_screen_string = subprocess.check_output(['tput', 'ed'])
  set_cursor_at_string = subprocess.check_output(['tput', 'cup', '99', '199'])
 
  @staticmethod
  def clear():
    sys.stdout.write(MenuScreen.clear_string)
  @staticmethod
  def save_position():
    sys.stdout.write(MenuScreen.save_position_string)
  @staticmethod
  def restore_position():
    sys.stdout.write(MenuScreen.restore_position_string)
  @staticmethod
  def getmaxyx():
    return MenuScreen.get_terminal_size()
  @staticmethod
  def get_width():
    return MenuScreen.getmaxyx()[1]
  @staticmethod
  def clear_to_end_of_screen():
    sys.stdout.write(MenuScreen.clear_end_of_screen_string)
  @staticmethod
  def set_cursor_at(row, col):
    sys.stdout.write(MenuScreen.set_cursor_at_string.replace('100', str(row)).replace('200', str(col)))
  # adjusted from http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
  @staticmethod
  def get_terminal_size():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
      try:
        import fcntl, termios, struct, os
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
      except:
        return None
      return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
      try:
        fd = os.open(os.ctermid(), os.O_RDONLY)
        cr = ioctl_GWINSZ(fd)
        os.close(fd)
      except:
        pass
    if not cr:
      try:
        cr = (env['COLUMNS'], env['LINES'])
      except:
        cr = (80, 25)
    return int(cr[0]), int(cr[1])
