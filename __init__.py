# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RSGIS
                                 A QGIS plugin
 Tool supports operations on Landsat (1to8) level 1 data, LISS III and LISS IV satellite data products
                             -------------------
        begin                : 2017-04-17
        copyright            : (C) 2017 by Prathamesh B
        email                : prathamesh.barane@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RSGIS class from file RSGIS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .RSGIS_M import RSGIS
    return RSGIS(iface)
