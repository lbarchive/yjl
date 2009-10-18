#!/usr/bin/env python
# This code is put in Public Domain,
# written by Yu-Jie Lin (http://livibetter.mp/)

import os.path
import sys
import urllib2

import matplotlib 
matplotlib.use('GTKAgg') 
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
import matplotlib.mlab as mlab

from numpy import nan

try:
  import pygtk
  pygtk.require("2.0")
except:
  print "You need to install pyGTK or GTKv2 or set your PYTHONPATH correctly"
  sys.exit(1)
  
import gtk
import gtk.glade


DATA_URI = 'http://www.google.org/flutrends/data.txt'
CSV_FILENAME = 'fludata.csv'

class AppFluViewer:

  def __init__(self):

    gladefile = 'fluviewer.glade'
    # This must match the window name in glade
    windowname = 'fluviewer'
    self.wTree = gtk.glade.XML(gladefile, windowname)
    dic = {
        # Also need to set fluviewer's signal tab
        'on_fluviewer_destroy': gtk.main_quit,
        'on_tv_country_button_release_event': self.on_tv_country_changed,
        'on_tv_country_key_release_event': self.on_tv_country_changed,
        'on_btn_update_clicked': self.on_btn_update_clicked,
        }
    self.wTree.signal_autoconnect (dic)
    self.fluviewer = self.wTree.get_widget('fluviewer')

    # Load CSV if it is in current directory
    self.update(False)
    self.reload()

    # Setting up figure
    self.figure = Figure()
    self.axis = self.figure.add_subplot(111)
    self.canvas = FigureCanvas(self.figure)

    vbox = self.wTree.get_widget('vbox2')
    vbox.pack_start(self.canvas, True, True)
    # Setting figure navigation toolbar
    vbox.pack_start(NavigationToolbar(self.canvas, self.fluviewer), False, False)
    vbox.show_all()

  def on_tv_country_changed(self, tv, *args):

    # Clear figure
    self.axis.clear()
    self.axis.hold(True)

    ls_idx = [sel[0] + 1 for sel in tv.get_selection().get_selected_rows()[1]]    
    for idx in xrange(1, len(self.rec.dtype)):
      if idx in ls_idx:
        self.axis.plot(self.rec.date, self.rec.field(idx),
            label=self.tv_data.get_column(idx).get_title())
      self.tv_data.get_column(idx).set_visible(idx in ls_idx)

    self.axis.legend()
    self.canvas.draw()

  def on_btn_update_clicked(self, *args):

    self.update()
    self.reload()

  def update(self, force=True):

    if force or not os.path.exists(CSV_FILENAME):
      csv_started = False
      f = open(CSV_FILENAME, 'w')
      for line in urllib2.urlopen(DATA_URI):
        # Skip the notes before the csv data
        if line.startswith('Date,'):
          csv_started = True
        if csv_started:
          f.write(line)
      f.close()

  def reload(self):

    # Some data is missing, default converter will raise ValueError because of
    # int(''), use missingd or converterd to resolve the problem but we have to
    # load csv first to get field names.
    f = open(CSV_FILENAME, 'r')
    line = f.readline()
    f.close()
    fields = line.replace(' ', '_').lower().split(',')[1:]
    d = dict(zip(fields, [lambda value: int(value) if value != '' else nan]*len(fields)))
    self.rec = mlab.csv2rec(CSV_FILENAME, converterd=d)

    country_names = []
    for name in self.rec.dtype.names:
      if name == 'date':
        continue
      # Prettify the field name, ex. united_states -> United States
      name = ' '.join([_x.capitalize() for _x in name.replace('_', ' ').split(' ')])
      country_names.append(name)

    # Setting up country names
    tv_country = self.wTree.get_widget('tv_country')
    
    # Define the types to ListStore
    types = [str]
    store = gtk.ListStore(*types)
    # Add country names to ListStore
    for name in country_names:
      store.append([name])
    
    tv_country.set_model(store)

    # Clean up columns
    for column in tv_country.get_columns():
      tv_country.remove_column(column)
      
    # Add column to TreeView (Specify what to show)
    column = gtk.TreeViewColumn('Country', gtk.CellRendererText(), text=0)
    tv_country.append_column(column)
    # Set up multiselect
    tv_country.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    # Setting up data
    tv_data = self.wTree.get_widget('tv_data')

    # Let date and number all be str type
    types = [str] * len(self.rec.dtype)
    store = gtk.ListStore(*types)
    for rec in self.rec:
      store.append(rec)

    # Clean up columns
    for column in tv_data.get_columns():
      tv_data.remove_column(column)

    column = gtk.TreeViewColumn('Date', gtk.CellRendererText(), text=0)
    tv_data.append_column(column)

    for i in xrange(len(country_names)):
      name = country_names[i]
      column = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=i+1)
      column.set_visible(False)
      tv_data.append_column(column)
    
    tv_data.set_model(store)
    self.tv_data = tv_data

    # Update last data date
    self.wTree.get_widget('lbl_last_date').set_text(str(self.rec[-1][0]))

app = AppFluViewer()
gtk.main()
