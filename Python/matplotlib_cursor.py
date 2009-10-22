#!/usr/bin/env python


import datetime

import matplotlib 
matplotlib.use('GTKAgg') 
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
import matplotlib.finance as finance
import matplotlib.mlab as mlab

from numpy import searchsorted, array

try:
  import pygtk
  pygtk.require("2.0")
except:
  print "You need to install pyGTK or GTKv2 or set your PYTHONPATH correctly"
  sys.exit(1)
  
import gtk


# Modified from http://matplotlib.sourceforge.net/examples/pylab_examples/cursor_demo.html
class SnaptoCursor:
    
    def __init__(self, ax, x, y, useblit=True, callback=None):
        
        self.ax = ax
        self.lx = None
        self.ly = None
        self.x = x
        self.y = y
        self.bg = None
        self.useblit = useblit
        # callback just for easy to set cursor on the other figure
        self.callback = callback

    def mouse_move(self, event):

        if not event.inaxes:
          return

        ax = event.inaxes
        minx, maxx = ax.get_xlim()
        miny, maxy = ax.get_ylim()

        if self.useblit and self.bg is None:
          self.bg = ax.figure.canvas.copy_from_bbox(ax.bbox)
        ax.figure.canvas.restore_region(self.bg)

        x, y = event.xdata, event.ydata

        indx = searchsorted(self.x, [x])[0]
        if indx == len(self.x):
          indx = len(self.x) - 1
        x = self.x[indx]
        y = self.y[indx]
        # update the line positions
        if self.lx is not None:
          self.lx.set_data((minx, maxx), (y, y))
          self.ly.set_data((x, x), (miny, maxy))
        else:
          color = 'b-' if self.useblit else 'r-'
          self.lx, = ax.plot((minx, maxx), (y, y), color)  # the horiz line
          self.ly, = ax.plot((x, x), (miny, maxy), color)  # the vert line

        if self.useblit:
          ax.draw_artist(self.lx)
          ax.draw_artist(self.ly)
          ax.figure.canvas.blit(ax.bbox)
        else:
          ax.figure.canvas.draw()


def create_figure(quotes):

  f = Figure(figsize=(5,4), dpi=100)

  a = f.add_subplot(111)
  canvas = FigureCanvas(f)  # a gtk.DrawingArea
  canvas.set_size_request(800,300)

  a.xaxis_date()
  
  finance.candlestick(a, quotes, width=0.5)

  return f


def main():

  win = gtk.Window()
  win.connect('destroy', gtk.main_quit)
  win.set_title('Cursors')

  vbox = gtk.VBox()
  win.add(vbox)

  # Get data from Yahoo Finance
  enddate = datetime.date.today()
  startdate = enddate + datetime.timedelta(days=-72)
  quotes = finance.quotes_historical_yahoo('GOOG', startdate, enddate)

  qa = array(quotes)
 
  f = create_figure(quotes)
  a = f.gca()
  vbox.pack_start(gtk.Label('No Blit'), False, False)
  vbox.pack_start(f.canvas)

  cursor1 = SnaptoCursor(a, qa[:,0], qa[:,2], useblit=False)
  f.canvas.mpl_connect('motion_notify_event', cursor1.mouse_move)
  
  f = create_figure(quotes)
  a = f.gca()
  vbox.pack_start(gtk.Label('Use Blit'), False, False)
  vbox.pack_start(f.canvas)

  cursor2 = SnaptoCursor(a, qa[:,0], qa[:,2], useblit=True)
  f.canvas.mpl_connect('motion_notify_event', cursor2.mouse_move)
  
  win.show_all()
  gtk.main()


if __name__ == '__main__':

  main()
