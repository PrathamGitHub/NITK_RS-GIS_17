# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RSGISDialog
                                 A QGIS plugin
 Tool supports operations on Landsat (1to8) level 1 data, LISS III and LISS IV satellite data products
                             -------------------
        begin                : 2017-04-17
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Prathamesh B
        email                : prathamesh.barane@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

#from qgis.PyQt import QtGui, uic
from qgis.core import *
from qgis.PyQt import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'RSGIS_M_dialog_base.ui'))


class RSGISDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(RSGISDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
