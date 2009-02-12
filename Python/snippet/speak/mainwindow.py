# Copyright (C) 2009  Yu-Jie Lin
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PyQt4 import QtCore, QtGui, uic

import speechd


Ui_MainWindow = uic.loadUiType('mainwindow.ui')[0]


class MainWindow(Ui_MainWindow, QtGui.QMainWindow):

  def __init__(self):
    # UI initialization
    QtGui.QMainWindow.__init__(self)
    self.setupUi(self)

    # Speech Dispatcher initialziation
    client = self._client = speechd.SSIPClient('speak.py')
    output_modules = client.list_output_modules()
    if output_modules:
      self.output_module.addItems(output_modules)
      client.set_output_module(output_modules[0])
      client.set_punctuation(speechd.PunctuationMode.SOME)
      self.language.emit(
          QtCore.SIGNAL('textChanged(int)'), self.language.text())
      self.volume.emit(
          QtCore.SIGNAL('valueChanged(int)'), self.volume.value())
      self.rate.emit(QtCore.SIGNAL('valueChanged(int)'), self.rate.value())

  def closeEvent(self, event):
    if self._client:
      self._client.close()

  @QtCore.pyqtSignature('')
  def on_speak_clicked(self):
    if self._client:
      self._client.speak(str(self.speak_content.toPlainText()))

  @QtCore.pyqtSignature('const QString&')
  def on_output_module_currentIndexChanged(self, module_name):
    if self._client:
      self._client.set_output_module(module_name)

  @QtCore.pyqtSignature('const QString&')
  def on_language_textChanged(self, language):
    if self._client and len(language) == 2:
      self._client.set_language(str(language))

  @QtCore.pyqtSignature('int')
  def on_volume_valueChanged(self, volume):
    if self._client:
      self._client.set_volume(volume)
  
  @QtCore.pyqtSignature('int')
  def on_rate_valueChanged(self, rate):
    if self._client:
      self._client.set_rate(rate)
