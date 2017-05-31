# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RSGIS
                                 A QGIS plugin
 Used to work with satellite raw data
                              -------------------
        begin                : 2017-04-16
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from RSGIS_M_dialog import RSGISDialog
import os.path
from PyQt4 import QtCore, QtGui
import time
# import logging
import datetime
import tarfile
import zipfile
import re
import math
from osgeo import gdal
import numpy as np
import os
from osgeo import ogr, osr
import gdal
from gdalconst import *
import multiprocessing
from io import StringIO
import tokenize
# import threading
import webbrowser as wb
import traceback
from qgis.core import *



# Create a lock for multiprocess
p_lock = multiprocessing.Lock()


ip_toa_ra=[0] * 9
ip_toa_re=[0] * 9
ip_extras=[0] * 6
ip_exclude_following=[0] * 16

class Worker(QtCore.QObject):
    
    def __init__(self, ip_user, custom, custom_names, browse, browse_selected_obj, browse_selected_ext_obj, browse_selected_mode, shape_path, if_clip):
        QtCore.QObject.__init__(self)
        # if isinstance(layer, QgsVectorLayer) is False:
        #     raise TypeError('Worker expected a QgsVectorLayer, got a {} instead'.format(type(layer)))
        self.ip_user = ip_user
        self.custom = custom
        self.custom_names = custom_names
        self.browse = browse
        self.browse_selected_obj = browse_selected_obj
        self.browse_selected_ext_obj = browse_selected_ext_obj
        self.browse_selected_mode = browse_selected_mode
        self.shape_path = shape_path
        self.if_clip = if_clip

    def run(self):
        finish_cond = 0
        try:

            custom = self.custom
            custom_names = self.custom_names

            browse = self.browse

            browse_selected_obj = self.browse_selected_obj
            browse_selected = []
            for item in browse_selected_obj:
                browse_selected.append(str(item))
            del browse_selected_obj

            browse_selected_ext_obj = self.browse_selected_ext_obj
            browse_selected_ext = []
            for item in browse_selected_ext_obj:
                browse_selected_ext.append(str(item))
            del browse_selected_ext_obj

            browse_selected_mode = self.browse_selected_mode
            shape_path = self.shape_path
            if_clip = self.if_clip

            del item
            # ================================================================================================
            # ================================= Start the process ============================================
            self.progress.emit('\n>>>----------------------------------------------------------------------<<<\n'
                         ' ==============  Process Started ==============='
                         '\n>>>----------------------------------------------------------------------<<<')
            # Collecting all the use inputs
            self.progress.emit('\nCollected all the user inputs')
            ip_user = self.ip_user
            # ------------------------------------------------------------------------------------------------------------------------
            # TO measure time for processing
            start_time=time.time()

            # -----------------------------------------------------------------------------------------------------
            # Create a NITK_RSGIS_******* folder i.e. folder_01
            folder_01='NITK_RSGIS_%s' % (time.strftime("%Y%m%d_") + time.strftime("%H%M%S"))
            if not os.path.exists(os.path.join(browse, folder_01)):
                os.makedirs(os.path.join(browse, folder_01))
                # print("%s is created in directory: %s" % (folder_01, browse))
            else:
                folder_create=False
                while not folder_create:
                    folder_01='NITK_RSGIS_%s' % (time.strftime("%Y%m%d_") + time.strftime("%H%M%S"))
                    if not os.path.exists(os.path.join(browse, folder_01)):
                        os.makedirs(os.path.join(browse, folder_01))
                        # print("%s is created in directory: %s" % (folder_01, browse))
                        folder_create=True

                del folder_create
            self.progress.emit('Folder "%s" created in (%s) directory\n' %(folder_01, browse))

            # Open the current working directory
            wb.open(os.path.join(browse, folder_01))

            # ------------------------------------------------------------------------------------------------------
            # In case of selection mode 1 (compressed file/s mode) extracting the compressed files and listing their names
            if browse_selected_mode == 1:
                extract_path = 'Extracted'
                self.progress.emit('Extracting the file/s in the corresponding folder/s ...\n')

                def Extract_files(file,ext):

                    if ext in ["*.tar.gz", "*.tar", "*.tar.zip", '*.gz']:
                        with tarfile.open(os.path.join(browse, file)) as tar:
                            os.makedirs(os.path.join(browse, folder_01, extract_path, os.path.splitext(file)[0]))
                            # with p_lock:
                            self.progress.emit(">>>~~~\nExtracting %s file in ../%s/Extracted/%s folder....." % (file, folder_01, file.split('.')[0]))
                            tar.extractall(path=os.path.join(browse, folder_01, extract_path, os.path.splitext(file)[0]))
                            # with p_lock:
                                #self.progress.emit("Extracted %s file" % (file))
                    elif ext == "*.zip":
                        with zipfile.ZipFile(os.path.join(browse, file)) as zip:
                            os.makedirs(os.path.join(browse, folder_01, extract_path, os.path.splitext(file)[0]))
                            # with p_lock:
                            self.progress.emit(">>>~~~\nExtracting %s file in ../%s/Extracted/%s folder....." % (file, folder_01, file.split('.')[0]))
                            zip.extractall(path=os.path.join(browse, folder_01, extract_path, os.path.splitext(file)[0]))
                            #with p_lock:
                                #self.progress.emit("Extracted %s file" % (file))
                    else:
                        #with p_lock:
                        self.progress.emit('%s is not a supported compressed file format!' % file)

                for file, ext in zip(browse_selected, browse_selected_ext):
                    Extract_files(file, ext)
                del file, ext

                # processes = []
                # for file, ext in zip(browse_selected, browse_selected_ext):
                #     process = multiprocessing.Process(target=Extract_files, args=(file, ext,))
                #     process.daemon = True
                #     process.start()
                #     processes.append(process)
                # del file, ext
                #
                # for process in processes:
                #     process.join()
                # del process, processes

                # Print time taken for extraction
                if int((time.time() - start_time) / 60) == 0 and int((time.time() - start_time) % 60) == 0:
                    self.progress.emit('\nTime taken for extraction: Less than 1 sec.')
                else:
                    self.progress.emit('\nTime taken for extraction: %i min. %i sec.' % (
                        ((time.time() - start_time) / 60), (time.time() - start_time) % 60))

                # Listing names of all the extracted folders
                browse_selected=[d for d in os.listdir(os.path.join(browse, folder_01, extract_path)) if
                                 os.path.isdir(os.path.join(browse, folder_01, extract_path, d))]
            # -------------------------------------------------------------------------------------------------
            # Listing the names of individual files and their extensions in each folder
            if browse_selected_mode == 1 or browse_selected_mode == 3:
                # Create empty variable lists
                num = len(browse_selected) + 1

                folder_files=[[] for x in xrange(num)]
                folder_files_ext=[[] for x in xrange(num)]
                raw_metadata_del=[[] for x in xrange(num)]
                raw_metadata_del = [[] for x in xrange(num)]
                sensor_type=[[] for x in xrange(num)]
                metadata_required=[[] for x in xrange(num)]
                spatial_ref=[[] for x in xrange(num)]
                spatial_ref_pan=[[] for x in xrange(num)]
                spatial_ref_pan = [[] for x in xrange(num)]
                clip_state = [[None] for x in xrange(num)]
                exclude_following_list = [[] for x in xrange(num)]
                quality_band = [[] for x in xrange(num)]

                del num

                # Collecting folder files and their extensions

                for ref_num, file in enumerate(browse_selected):
                    if browse_selected_mode == 1:
                        folder_files[ref_num]=os.listdir(os.path.join(browse, folder_01, extract_path, file))
                    if browse_selected_mode == 3:
                        req_files = [f for f in os.listdir(os.path.join(browse, file)) if f.endswith('.txt') or f.endswith('.tif') or f.endswith('.TIF')]
                        folder_files[ref_num]=req_files
                        del req_files, f
                    for ext in folder_files[ref_num]:
                        folder_files_ext[ref_num].append('+'+os.path.splitext(ext)[-1])


                del ref_num, file, ext

            if browse_selected_mode == 2:
                # one empty list is added as python indexing starts with zero.
                folder_files=[browse_selected, []]
                folder_files_ext=[browse_selected_ext, []]
                raw_metadata_del=[[], []]
                sensor_type=[[], []]
                metadata_required=[[], []]
                spatial_ref=[[], []]
                spatial_ref_pan=[[], []]
                clip_state = [[None], []]
                exclude_following_list = [[], []]
                quality_band = [[], []]

            # ==================================================================================================
            ''' Write functions for raster input output using gdal'''

            def gdali(filename, ref='array'):
                dataset=gdal.Open(filename, GA_ReadOnly)
                band=dataset.GetRasterBand(1)

                if ref == 'array':
                    data=band.ReadAsArray(0, 0, dataset.RasterXSize, dataset.RasterYSize).astype(np.float32)
                    return (data)
                else:
                    cols=dataset.RasterXSize
                    rows=dataset.RasterYSize
                    geoTransform=dataset.GetGeoTransform()
                    proj=dataset.GetProjection()
                    return ([cols, rows, geoTransform, proj])

            def gdalo(outfilename, spatial_ref, array, bands, datatype):
                driver = gdal.GetDriverByName('GTiff')
                outDataset=driver.Create(outfilename, spatial_ref[0], spatial_ref[1], bands,
                                         datatype)  # datatype: 2: UInt16, 6:Float32
                outDataset.SetGeoTransform(spatial_ref[2])
                outDataset.SetProjection(spatial_ref[3])

                if bands == 1:
                    outBand=outDataset.GetRasterBand(1)
                    outBand.WriteArray(array, 0, 0)
                elif bands == 3:
                    outBand=outDataset.GetRasterBand(1)
                    outBand.WriteArray(array[0], 0, 0)

                    outBand=outDataset.GetRasterBand(2)
                    outBand.WriteArray(array[1], 0, 0)

                    outBand=outDataset.GetRasterBand(3)
                    outBand.WriteArray(array[2], 0, 0)

            # ------------------------------------------------------------------------------------------------------
            # Reading the metadata files
            self.progress.emit('\n>>> Please make sure:\n'
                         '        1. Selected input file/s contain/s metadata file/s\n\n'
                         '            Read metadata file/s and extracted the details')

            # Create function to read metadata file
            def get_meta(meta_text, dir_list, list_num=0):
                m_name_compile=re.compile(meta_text)
                m_name="".join(filter(lambda x: m_name_compile.search(x), dir_list))
                if len(m_name) != 0:
                    if browse_selected_mode == 1:
                        m_handle=open(os.path.join(browse, folder_01, extract_path, browse_selected[list_num], m_name))
                    elif browse_selected_mode == 2:
                        m_handle=open(os.path.join(browse, m_name))
                    elif browse_selected_mode == 3:
                        m_handle=open(os.path.join(browse, browse_selected[list_num], m_name))
                    raw_metadata=m_handle.read().splitlines()
                    m_handle.close()
                    raw_metadata_del[list_num].append(raw_metadata)

            # Reading and storing metadata file/s
            if browse_selected_mode in [1, 3]:
                for list_num in xrange(len(browse_selected)):
                    get_meta('MTL.txt', folder_files[list_num], list_num)
                    get_meta('BAND_META.txt', folder_files[list_num], list_num)
                del list_num
            elif browse_selected_mode == 2:
                get_meta('MTL.txt', folder_files[0])
                get_meta('BAND_META.txt', folder_files[0])

            # Function to identify the sensor from sensor_string
            def identify_sensor(sensor_string):
                if 'LANDSAT_8' in sensor_string and 'OLI_TIRS' in sensor_string:
                    return ('LC8')
                elif 'IRS-R2' in sensor_string:
                    if 'L3' in sensor_string:
                        return ('L3')
                    elif 'L4FX' in sensor_string:
                        return ('L4')
                elif 'LANDSAT_7' in sensor_string and 'ETM' in sensor_string:
                    return ('LE7')
                elif 'LANDSAT_5' in sensor_string:
                    if 'TM' in sensor_string:
                        return ('LT5')
                    elif 'MSS' in sensor_string:
                        return ('LM5')
                elif 'LANDSAT_4' in sensor_string:
                    if 'TM' in sensor_string:
                        return ('LT4')
                    elif 'MSS' in sensor_string:
                        return ('LM4')
                elif 'LANDSAT_3' in sensor_string and 'MSS' in sensor_string:
                    return ('LM3')
                elif 'LANDSAT_2' in sensor_string and 'MSS' in sensor_string:
                    return ('LM2')
                elif 'LANDSAT_1' in sensor_string and 'MSS' in sensor_string:
                    return ('LM1')
                else:
                    return (None)

            # Function to get and put sensor type
            def sensor_type_find(num):
                if raw_metadata_del[num]:
                    sat = None
                    sensor = None
                    i = 0
                    while i < len(raw_metadata_del[num][0]) and sensor == None:
                        if 'SPACECRAFT_ID' in raw_metadata_del[num][0][i] or 'SatID' in raw_metadata_del[num][0][i]:
                            sat = raw_metadata_del[num][0][i].split(' ')[-1]
                        if 'SENSOR_ID' in raw_metadata_del[num][0][i] or 'Sensor' in raw_metadata_del[num][0][i]:
                            sensor = raw_metadata_del[num][0][i].split(' ')[-1]
                            sensor_type[num] = identify_sensor(sat + sensor)
                            sat = 'identified'
                        i += 1
                    del i
                else:
                    sensor_type[num] = None

            # Identify and put the sensor type
            for num in xrange(len(raw_metadata_del)):
                sensor_type_find(num)

            # Creating empty lists for metadata_required list according to sensor type
            for num in xrange(len(sensor_type)):
                if sensor_type[num]:
                    metadata_required[num] = [[] for y in xrange(11)]
                    # if sensor_type[num] == 'LC8':
                    #     metadata_required[num] = [[] for y in xrange(11)]
                    # elif sensor_type[num] == 'LE7':
                    #     metadata_required[num] = [[] for y in xrange(11)]
                    # elif sensor_type[num] in ['L3', 'L4']:
                    #     metadata_required[num] = [[] for y in xrange(11)]
                    # elif sensor_type[num] in ['LM1', 'LM2', 'LM3']:
                    #     metadata_required[num] = [[] for y in xrange(11)]
                    # elif sensor_type[num] in ['LM4', 'LM5']:
                    #     metadata_required[num] = [[] for y in xrange(11)]
                    # elif sensor_type[num] in ['LT4', 'LT5']:
                    #     metadata_required[num] = [[] for y in xrange(11)]
            del num

            # earth2sun distance table
            e2s_dist = [0, 0.98331, 0.9833, 0.9833, 0.9833, 0.9833, 0.98332, 0.98333, 0.98335, 0.98338, 0.98341,
                        0.98345,
                        0.98349,
                        0.98354, 0.98359, 0.98365, 0.98371, 0.98378, 0.98385, 0.98393, 0.98401, 0.9841, 0.98419,
                        0.98428,
                        0.98439,
                        0.98449, 0.9846, 0.98472, 0.98484, 0.98496, 0.98509, 0.98523, 0.98536, 0.98551, 0.98565, 0.9858,
                        0.98596,
                        0.98612, 0.98628, 0.98645, 0.98662, 0.9868, 0.98698, 0.98717, 0.98735, 0.98755, 0.98774,
                        0.98794,
                        0.98814,
                        0.98835, 0.98856, 0.98877, 0.98899, 0.98921, 0.98944, 0.98966, 0.98989, 0.99012, 0.99036,
                        0.9906,
                        0.99084,
                        0.99108, 0.99133, 0.99158, 0.99183, 0.99208, 0.99234, 0.9926, 0.99286, 0.99312, 0.99339,
                        0.99365,
                        0.99392,
                        0.99419, 0.99446, 0.99474, 0.99501, 0.99529, 0.99556, 0.99584, 0.99612, 0.9964, 0.99669,
                        0.99697,
                        0.99725,
                        0.99754, 0.99782, 0.99811, 0.9984, 0.99868, 0.99897, 0.99926, 0.99954, 0.99983, 1.00012,
                        1.00041,
                        1.00069,
                        1.00098, 1.00127, 1.00155, 1.00184, 1.00212, 1.0024, 1.00269, 1.00297, 1.00325, 1.00353,
                        1.00381,
                        1.00409,
                        1.00437, 1.00464, 1.00492, 1.00519, 1.00546, 1.00573, 1.006, 1.00626, 1.00653, 1.00679, 1.00705,
                        1.00731,
                        1.00756, 1.00781, 1.00806, 1.00831, 1.00856, 1.0088, 1.00904, 1.00928, 1.00952, 1.00975,
                        1.00998,
                        1.0102,
                        1.01043, 1.01065, 1.01087, 1.01108, 1.01129, 1.0115, 1.0117, 1.01191, 1.0121, 1.0123, 1.01249,
                        1.01267,
                        1.01286, 1.01304, 1.01321, 1.01338, 1.01355, 1.01371, 1.01387, 1.01403, 1.01418, 1.01433,
                        1.01447,
                        1.01461,
                        1.01475, 1.01488, 1.015, 1.01513, 1.01524, 1.01536, 1.01547, 1.01557, 1.01567, 1.01577, 1.01586,
                        1.01595,
                        1.01603, 1.0161, 1.01618, 1.01625, 1.01631, 1.01637, 1.01642, 1.01647, 1.01652, 1.01656,
                        1.01659,
                        1.01662,
                        1.01665, 1.01667, 1.01668, 1.0167, 1.0167, 1.0167, 1.0167, 1.01669, 1.01668, 1.01666, 1.01664,
                        1.01661,
                        1.01658, 1.01655, 1.0165, 1.01646, 1.01641, 1.01635, 1.01629, 1.01623, 1.01616, 1.01609,
                        1.01601,
                        1.01592,
                        1.01584, 1.01575, 1.01565, 1.01555, 1.01544, 1.01533, 1.01522, 1.0151, 1.01497, 1.01485,
                        1.01471,
                        1.01458,
                        1.01444, 1.01429, 1.01414, 1.01399, 1.01383, 1.01367, 1.01351, 1.01334, 1.01317, 1.01299,
                        1.01281,
                        1.01263,
                        1.01244, 1.01225, 1.01205, 1.01186, 1.01165, 1.01145, 1.01124, 1.01103, 1.01081, 1.0106,
                        1.01037,
                        1.01015,
                        1.00992, 1.00969, 1.00946, 1.00922, 1.00898, 1.00874, 1.0085, 1.00825, 1.008, 1.00775, 1.0075,
                        1.00724,
                        1.00698, 1.00672, 1.00646, 1.0062, 1.00593, 1.00566, 1.00539, 1.00512, 1.00485, 1.00457, 1.0043,
                        1.00402,
                        1.00374, 1.00346, 1.00318, 1.0029, 1.00262, 1.00234, 1.00205, 1.00177, 1.00148, 1.00119,
                        1.00091,
                        1.00062,
                        1.00033, 1.00005, 0.99976, 0.99947, 0.99918, 0.9989, 0.99861, 0.99832, 0.99804, 0.99775,
                        0.99747,
                        0.99718,
                        0.9969, 0.99662, 0.99634, 0.99605, 0.99577, 0.9955, 0.99522, 0.99494, 0.99467, 0.9944, 0.99412,
                        0.99385,
                        0.99359, 0.99332, 0.99306, 0.99279, 0.99253, 0.99228, 0.99202, 0.99177, 0.99152, 0.99127,
                        0.99102,
                        0.99078,
                        0.99054, 0.9903, 0.99007, 0.98983, 0.98961, 0.98938, 0.98916, 0.98894, 0.98872, 0.98851, 0.9883,
                        0.98809,
                        0.98789, 0.98769, 0.9875, 0.98731, 0.98712, 0.98694, 0.98676, 0.98658, 0.98641, 0.98624,
                        0.98608,
                        0.98592,
                        0.98577, 0.98562, 0.98547, 0.98533, 0.98519, 0.98506, 0.98493, 0.98481, 0.98469, 0.98457,
                        0.98446,
                        0.98436,
                        0.98426, 0.98416, 0.98407, 0.98399, 0.98391, 0.98383, 0.98376, 0.9837, 0.98363, 0.98358,
                        0.98353,
                        0.98348,
                        0.98344, 0.9834, 0.98337, 0.98335, 0.98333, 0.98331]

            # Getting metadata_required
            for num in xrange(len(raw_metadata_del)):
                if sensor_type[num]:
                    success, path, row, date, pass_time = 0, [], [], [], []
                    # def Meta_reqd_l2(i):
                    i = 0
                    while success < 11 and i < len(raw_metadata_del[num][0]):
                        # for i in xrange(len(raw_metadata_del[num][0])):
                        # For Julian Day
                        if not (metadata_required[num][0]):
                            # if sensor_type[num] in ["LC8", "LE7", "LM5", "LM4", "LM3", "LM2", "LM1", "LT5", "LT4"]:
                            if 'DATE_ACQUIRED' in raw_metadata_del[num][0][i]:
                                metadata_required[num][0] = datetime.datetime.strptime(
                                    raw_metadata_del[num][0][i].split(' ')[-1], '%Y-%m-%d').timetuple().tm_yday
                                success += 1
                                if sensor_type[num] != 'LC8':
                                    metadata_required[num][1] = e2s_dist[metadata_required[num][0]]
                                    success += 1
                            # elif sensor_type[num] in ["L3", 'L4']:
                            elif 'DateOfPass' in raw_metadata_del[num][0][i]:
                                metadata_required[num][0] = datetime.datetime.strptime(
                                    raw_metadata_del[num][0][i].split(' ')[-1], '%d-%b-%Y').timetuple().tm_yday
                                success += 1
                                metadata_required[num][1] = e2s_dist[metadata_required[num][0]]
                                success += 1

                        # For earth2sun distance
                        if sensor_type[num] == 'LC8' and not (metadata_required[num][1]) and metadata_required[num][0]:
                            if 'EARTH_SUN_DISTANCE' in raw_metadata_del[num][0][i]:
                                metadata_required[num][1] = float(raw_metadata_del[num][0][i].split(' ')[-1])
                                metadata_required[num][2] = e2s_dist[metadata_required[num][0]]
                                success += 1
                                # For esun values except for Landsat 8
                        # Here bands are
                        #   band 0:   Deep Blue(d)
                        #   band 1:   Blue (b)
                        #   band 2:   Green (g)
                        #   band 3:   Red (r)
                        #   band 4:   NIR (n)
                        #   band 5,6: SWIR (s)
                        #   band 7,8: TIR (t)
                        #   band 9:   PAN (p)
                        #   band 10:  Cirus (c)
                        if not (metadata_required[num][2]):
                            if sensor_type[num] == "LE7":
                                metadata_required[num][2] = [None, 1997, 1812, 1533, 1039, 230.8, None, None, 84.9, 1362]
                            elif sensor_type[num] == "LT5":
                                metadata_required[num][2] = [None, 1957, 1826, 1554, 1036, 215, None, 80.69, None]
                            elif sensor_type[num] == "LT4":
                                metadata_required[num][2] = [None, 1957, 1825, 1557, 1033, 214.9, None, 80.72, None]
                            elif sensor_type[num] == "L3":
                                metadata_required[num][2] = [None, None, 1849.5, 1553, 1092, 239.52, None, None, None, None]
                            elif sensor_type[num] == "L4":
                                metadata_required[num][2] = [None, None, 1853.6, 1581.6, 1114.6, None, None, None, None,
                                                             None]
                            else:
                                metadata_required[num][2] = [None]
                            success += 1

                        # For k1 and k2 coef
                        # Here bands are
                        #   K1:   0
                        #   K2:   1
                        if not (metadata_required[num][3]):
                            if sensor_type[num] == "LC8":
                                metadata_required[num][3] = [[777.8853, 480.8883], [1321.0789, 1201.1442]]
                            elif sensor_type[num] == "LE7":
                                metadata_required[num][3] = [[666.09, 666.09], [1282.71, 1282.71]]
                            elif sensor_type[num] == "LT5":
                                metadata_required[num][3] = [607.76, 1260.56]
                            elif sensor_type[num] == "LT4":
                                metadata_required[num][3] = [671.62, 1284.30]
                            else:
                                metadata_required[num][3] = [None]
                            success += 1

                        # For sun's elevation
                        if not (metadata_required[num][4]):
                            # if sensor_type[num] in ["LC8", "LE7", "LM5", "LM4", "LM3", "LM2", "LM1", "LT5", "LT4"]:
                            if 'SUN_ELEVATION' in raw_metadata_del[num][0][i]:
                                metadata_required[num][4] = float(raw_metadata_del[num][0][i].split(' ')[-1])
                                success += 1
                                # elif sensor_type[num] in ["L3", "L4"]:
                            elif 'SunElevationAtCenter' in raw_metadata_del[num][0][i]:
                                metadata_required[num][4] = float(raw_metadata_del[num][0][i].split(' ')[-1])
                                success += 1

                        # For different coefs
                        if not (metadata_required[num][5]):
                            if 'RADIANCE_MULT_BAND_10' in raw_metadata_del[num][0][i]:
                                if sensor_type[num] in ['LC8']:
                                    # for Rad Mul Const
                                    raw_list = [None]
                                    for item in xrange(i - 9, i + 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    metadata_required[num][5] = raw_list
                                    # for Rad Add Const
                                    raw_list = [None]
                                    for item in xrange(i + 2, i + 13):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    metadata_required[num][6] = raw_list
                                    # for Ref Mul Const
                                    raw_list = [None]
                                    for item in xrange(i + 13, i + 22):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    metadata_required[num][7] = raw_list
                                    # for Ref Add Const
                                    raw_list = [None]
                                    for item in xrange(i + 22, i + 31):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    metadata_required[num][8] = raw_list
                                    success += 1

                            elif 'RADIANCE_MAXIMUM_BAND_1' in raw_metadata_del[num][0][i]:
                                if sensor_type[num] in ['LE7']:
                                    # for Lmax
                                    raw_list = [None]
                                    for item in xrange(i, i + 17, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None])
                                    metadata_required[num][5] = raw_list
                                    # for Lmin
                                    raw_list = [None]
                                    for item in xrange(i + 1, i + 18, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None])
                                    metadata_required[num][6] = raw_list
                                    # for QcalMax and Qcalmin
                                    metadata_required[num][7] = 255
                                    metadata_required[num][8] = 1
                                    success += 1

                                elif sensor_type[num] in ['LT5', 'LT4']:
                                    # for Lmax
                                    raw_list = [None]
                                    for item in xrange(i, i + 13, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None])
                                    metadata_required[num][5] = raw_list
                                    # for Lmin
                                    raw_list = [None]
                                    for item in xrange(i + 1, i + 14, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None])
                                    metadata_required[num][6] = raw_list
                                    # for QcalMax and Qcalmin
                                    metadata_required[num][7] = 255
                                    metadata_required[num][8] = 1
                                    success += 1

                                elif sensor_type[num] in ['LM5', 'LM4']:
                                    # for Lmax
                                    raw_list = [None]
                                    for item in xrange(i, i + 7, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None, None])
                                    metadata_required[num][5] = raw_list
                                    # for Lmin
                                    raw_list = [None]
                                    for item in xrange(i + 1, i + 8, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None, None])
                                    metadata_required[num][6] = raw_list
                                    # for QcalMax and Qcalmin
                                    metadata_required[num][7] = 255
                                    metadata_required[num][8] = 1
                                    success += 1

                            elif 'B2_Lmin' in raw_metadata_del[num][0][i]:
                                if sensor_type[num] in ['L3']:
                                    # for Lmax
                                    raw_list = [None, None]
                                    for item in xrange(i + 4, i + 8):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None, None])
                                    metadata_required[num][5] = raw_list
                                    # for Lmin
                                    raw_list = [None, None]
                                    for item in xrange(i, i + 4):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None, None])
                                    metadata_required[num][6] = raw_list
                                    # for QcalMax and Qcalmin
                                    metadata_required[num][7] = 255
                                    metadata_required[num][8] = 1
                                    success += 1

                                elif sensor_type[num] in ['L4']:
                                    # for Lmax
                                    raw_list = [None, None]
                                    for item in xrange(i + 3, i + 6):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None, None, None])
                                    metadata_required[num][5] = raw_list
                                    # for Lmin
                                    raw_list = [None, None]
                                    for item in xrange(i, i + 3):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None, None, None])
                                    metadata_required[num][6] = raw_list
                                    # for QcalMax and Qcalmin
                                    metadata_required[num][7] = 255
                                    metadata_required[num][8] = 1
                                    success += 1

                            elif 'RADIANCE_MAXIMUM_BAND_4' in raw_metadata_del[num][0][i]:
                                if sensor_type[num] in ['LM3', 'LM2', 'LM1']:
                                    # for Lmax
                                    raw_list = [None, None, None, None]
                                    for item in xrange(i, i + 7, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None])
                                    metadata_required[num][5] = raw_list
                                    # for Lmin
                                    raw_list = [None, None, None, None]
                                    for item in xrange(i + 1, i + 8, 2):
                                        raw_list.append(float(raw_metadata_del[num][0][item].split(' ')[-1]))
                                    raw_list.extend([None, None])
                                    metadata_required[num][6] = raw_list
                                    # for QcalMax and Qcalmin
                                    metadata_required[num][7] = 255
                                    metadata_required[num][8] = 1
                                    success += 1

                        # For Thermal Wavelengths
                        if not (metadata_required[num][9]):
                            if sensor_type[num] == "LC8":
                                metadata_required[num][9] = [10.9, 12]
                            elif sensor_type[num] == "LE7":
                                metadata_required[num][9] = [11.45, 11.45]
                            elif sensor_type[num] in ["LT5", "LT4"]:
                                metadata_required[num][9] = [11.45]
                            else:
                                metadata_required[num][9] = [None]
                            success += 1

                        # For write string for every dataset folder
                        if not (metadata_required[num][10]):
                            if sensor_type[num] in ['LC8', 'LE7', 'LT5', 'LT4', 'LM5', 'LM4', 'LM3', 'LM2', 'LM1']:
                                if ' WRS_PATH' in raw_metadata_del[num][0][i]:
                                    path = raw_metadata_del[num][0][i].split(' ')[-1]
                                    row = raw_metadata_del[num][0][i + 1].split(' ')[-1]
                                    success += 1
                                if 'DATE_ACQUIRED' in raw_metadata_del[num][0][i]:
                                    date = raw_metadata_del[num][0][i].split(' ')[-1]
                                    success += 1
                                if 'SCENE_CENTER_TIME' in raw_metadata_del[num][0][i]:
                                    pass_time = '-'.join((raw_metadata_del[num][0][i].split(' ')[-1][1:]).split(':')[:2])
                                    success += 1
                                if path and row and date and pass_time:
                                    metadata_required[num][10] = '%s[%s_%s](%s_%s)' % (
                                    sensor_type[num], path, row, date, pass_time)
                                    success += 1

                            elif sensor_type[num] in ['L3', 'L4']:
                                if 'Path' in raw_metadata_del[num][0][i]:
                                    path = raw_metadata_del[num][0][i].split(' ')[-1]
                                    row = raw_metadata_del[num][0][i + 1].split(' ')[-1]
                                    success += 1
                                if 'DateOfPass' in raw_metadata_del[num][0][i]:
                                    date = raw_metadata_del[num][0][i].split(' ')[-1]
                                    success += 1
                                if 'SceneCenterTime' in raw_metadata_del[num][0][i]:
                                    pass_time = '-'.join((raw_metadata_del[num][0][i].split(' ')[-1]).split(':')[:2])
                                    success += 1
                                if path and row and date and pass_time:
                                    metadata_required[num][10] = '%s[%s_%s](%s_%s)' % (
                                    sensor_type[num], path, row, date, pass_time)
                                    success += 1
                        i += 1

            del num, i, date, pass_time, path, row, success, raw_list   # Can't delete raw_metadata_del as it has nested ref


            # ----------------------------------------------------------------------------------------------------

            # -----------------------------------------------------------------------------------------------------
            ''' Define function to collect the band information required'''
            # Create the empty lists to store all the band information (input and output)
            num = len(sensor_type)

            bands=[[] for x in xrange(num)]
            output_ra=[[] for x in xrange(num)]
            output_re=[[] for x in xrange(num)]
            output_extras=[[] for x in xrange(num)]

            for num in xrange(len(bands)):
                output_extras[num]=[[] for y in xrange(3)]
                if sensor_type[num] == 'LC8':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(12)]
                elif sensor_type[num] == 'LE7':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(10)]
                elif sensor_type[num] == 'LT4' or sensor_type[num] == 'LT5':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(8)]
                elif sensor_type[num] == 'LM4' or sensor_type[num] == 'LM5':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(5)]
                elif sensor_type[num] == 'LM1' or sensor_type[num] == 'LM2' or sensor_type[num] == 'LM3':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(8)]
                elif sensor_type[num] == 'L4':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(5)]
                elif sensor_type[num] == 'L3':
                    for list_name in [bands, output_ra, output_re]:
                        list_name[num]=[[] for y in xrange(6)]
            del list_name

            # function which returns extent_status where, 0: no tile, 1: tile extent, 2: shape extent
            def Shape_extent(feature_path):
                shape_extents = [[], [], [], []]
                # Create an OGR layer from a boundary shapefile
                driver_shape = ogr.GetDriverByName('ESRI Shapefile')
                inDataSet = driver_shape.Open(feature_path)

                # from Layer
                inLayer = inDataSet.GetLayer()
                spatialRef_source = inLayer.GetSpatialRef()

                minmax = 0
                for feature_number in xrange(inLayer.GetFeatureCount()):
                    inFeature = inLayer.GetFeature(feature_number)
                    geom = inFeature.GetGeometryRef()

                    # Convert the layer extent to image pixel coordinates
                    if minmax == 0:
                        (minX, maxX, minY, maxY) = geom.GetEnvelope()
                        minmax = 1
                    shape_extents[0] = min(minX, geom.GetEnvelope()[0])
                    shape_extents[1] = max(maxX, geom.GetEnvelope()[1])
                    shape_extents[2] = min(minY, geom.GetEnvelope()[2])
                    shape_extents[3] = max(maxY, geom.GetEnvelope()[3])
                return [spatialRef_source, shape_extents]

            def Clip_status(raster_path, spatialRef_source, extent):
                def world_to_pixel(geo_matrix, x, y):
                    '''
                    Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
                    the pixel location of a geospatial coordinate; from:
                    http://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#clip-a-geotiff-with-shapefile
                    '''
                    ulX = geo_matrix[0]
                    ulY = geo_matrix[3]
                    xDist = geo_matrix[1]
                    yDist = geo_matrix[5]
                    rtnX = geo_matrix[2]
                    rtnY = geo_matrix[4]
                    pixel = int((x - ulX) / xDist)
                    line = int((ulY - y) / xDist)
                    return (pixel, line)

                # Can accept either a gdal.Dataset or numpy.array instance
                rast_obj = gdal.Open(raster_path)
                gt = rast_obj.GetGeoTransform()
                proj_wktstring = rast_obj.GetProjection()

                spatialRef_target = osr.SpatialReference()
                spatialRef_target.ImportFromWkt(proj_wktstring)
                # ===================================================================

                point1 = (extent[0], extent[2])
                point2 = (extent[1], extent[3])

                if spatialRef_source.IsSame(spatialRef_target) == 0:
                    transform = osr.CoordinateTransformation(spatialRef_source, spatialRef_target)
                    point_geo1 = ogr.CreateGeometryFromWkt("POINT (%s %s)" % (point1[0], point1[1]))
                    point_geo1.Transform(transform)
                    point1 = (point_geo1.GetX(), point_geo1.GetY())
                    point_geo2 = ogr.CreateGeometryFromWkt("POINT (%s %s)" % (point2[0], point2[1]))
                    point_geo2.Transform(transform)
                    point2 = (point_geo2.GetX(), point_geo2.GetY())

                # Carefull *************
                [shp_minX, shp_maxY] = list(world_to_pixel(gt, point1[0], point1[1]))
                [shp_maxX, shp_minY] = list(world_to_pixel(gt, point2[0], point2[1]))

                shp_col = shp_maxX - shp_minX
                shp_row = shp_maxY - shp_minY

                shp_pix = shp_col * shp_row

                [im_maxX, im_maxY] = [rast_obj.RasterXSize, rast_obj.RasterYSize]

                im_pix = im_maxX * im_maxY

                if shp_minX < im_maxX and shp_minY < im_maxY and shp_maxX > 0 and shp_maxY > 0:
                    extent_status = 1 if shp_pix > im_pix else 2
                else:
                    extent_status = 0

                return (extent_status)

            if if_clip == 1:
                [spatialRef_source, extent] = Shape_extent(shape_path)
                for num in xrange(len(clip_state)):
                    if sensor_type[num]:
                        b_name = None
                        file = 0
                        while b_name == None:
                            if '.TIF' in folder_files[num][file] or '.tif' in folder_files[num][file]:
                                b_name = folder_files[num][file]
                            file += 1
                        del file

                        if browse_selected_mode == 1:
                            filename = os.path.join(browse, folder_01, extract_path, browse_selected[num], b_name)
                        elif browse_selected_mode == 2:
                            filename = os.path.join(browse, b_name)
                        elif browse_selected_mode == 3:
                            filename = os.path.join(browse, browse_selected[num], b_name)
                        clip_state[num] = Clip_status(filename, spatialRef_source, extent)
                del num, b_name, filename
            # ==============================================================================================================
            '''Creating folders for outputs'''
            output_path = 'Outputs'
            if not os.path.exists(os.path.join(browse, folder_01, output_path)):
                os.makedirs(os.path.join(browse, folder_01, output_path))

            # # logger.append('>>>-----------------------------------------------------<<<\n'
            # 'Creating a folder "%s" to store all the outputs .....\n'
            # 'Created %s folder in directory %s' % (output_path, output_path, folder_01))
                self.progress.emit('>>>----------------------------------------------------------------------<<<\n'
                         'Created "%s" folder to store all the outputs in the directory (%s)' % (output_path, folder_01))

            if browse_selected_mode in [1, 3]:
                self.progress.emit('\nFolders created in ../%s/%s directory:' % (folder_01, output_path))
                num = 0
                for file in browse_selected:
                    if sensor_type[num] and clip_state[num] != 0:
                        os.makedirs(os.path.join(browse, folder_01, output_path, file))
                        self.progress.emit('    %s' % file)
                    num += 1
                del file, num
            # -----------------------------------------------------------------------------------------------------
            if if_clip == 1:
                '''Creating folders for clipped images'''
                clipped_path = 'Clipped'
                if not os.path.exists(os.path.join(browse, folder_01, clipped_path)):
                    os.makedirs(os.path.join(browse, folder_01, clipped_path))

                #logger.append('>>>-----------------------------------------------------<<<\n'
                 #            'Creating a folder "%s" to store all the raw clipped raster images .....\n'
                  #           'Created %s folder in directory %s' % (clipped_path, clipped_path, folder_01))
                    self.progress.emit('>>>----------------------------------------------------------------------<<<\n'
                             'Created "%s" folder to store all the raw clipped raster images in the directory (%s)' % (clipped_path, folder_01))

                if browse_selected_mode in [1, 3]:
                    self.progress.emit('\nFolders created in ../%s/%s directory:' % (folder_01, clipped_path))
                    num = 0
                    for file in browse_selected:
                        if sensor_type[num] and clip_state[num] != 0:
                            os.makedirs(os.path.join(browse, folder_01, clipped_path, file))
                            self.progress.emit('    %s' % file)
                        num += 1
                    del file, num

            # ==============================================================================================================
            # Function for exclude_following_list
            def Exclude_following_list(num):
                # For Landsat8 removing the "exclude following features"
                if not len(exclude_following_list[num]) and sensor_type[num] == 'LC8':
                    # Create a list of all the quality band values to remove
                    exclude_following_list[num].append(61440) if ip_user[4][0] == 1 else exclude_following_list
                    exclude_following_list[num].append(56320) if ip_user[4][1] == 1 else exclude_following_list
                    exclude_following_list[num].append(53248) if ip_user[4][2] == 1 else exclude_following_list
                    exclude_following_list[num].append(48128) if ip_user[4][3] == 1 else exclude_following_list
                    exclude_following_list[num].append(45056) if ip_user[4][4] == 1 else exclude_following_list
                    exclude_following_list[num].append(39936) if ip_user[4][5] == 1 else exclude_following_list
                    exclude_following_list[num].append(36896) if ip_user[4][6] == 1 else exclude_following_list
                    exclude_following_list[num].append(36864) if ip_user[4][7] == 1 else exclude_following_list
                    exclude_following_list[num].append(31744) if ip_user[4][8] == 1 else exclude_following_list
                    exclude_following_list[num].append(28672) if ip_user[4][9] == 1 else exclude_following_list
                    exclude_following_list[num].append(23552) if ip_user[4][10] == 1 else exclude_following_list
                    exclude_following_list[num].append(20516) if ip_user[4][11] == 1 else exclude_following_list
                    exclude_following_list[num].append(20512) if ip_user[4][12] == 1 else exclude_following_list
                    exclude_following_list[num].append(20482) if ip_user[4][13] == 1 else exclude_following_list
                    exclude_following_list[num].append(20480) if ip_user[4][14] == 1 else exclude_following_list
                    exclude_following_list[num].append(1) if ip_user[4][15] == 1 else exclude_following_list

            def Quality_band(num):
                # For Landsat8 read the quality band for removing the "exclude following features"
                if not len(quality_band[num]) and sensor_type[num] == 'LC8':
                    # Reading the BQA band to extract the exclude following values
                    bq_name_compile = re.compile('BQA.TIF')
                    bq_name = "".join(filter(lambda x: bq_name_compile.search(x),
                                             folder_files[num]))  # "".join(x for x in dir_list b_name_compile.search(x))
                    if bq_name:
                        if browse_selected_mode == 1:
                            bq_filename = os.path.join(browse, folder_01, extract_path, browse_selected[num], bq_name)
                        elif browse_selected_mode == 2:
                            bq_filename = os.path.join(browse, bq_name)
                        elif browse_selected_mode == 3:
                            bq_filename = os.path.join(browse, browse_selected[num], bq_name)

                    if if_clip == 1:
                        # Get the band filename to store
                        if browse_selected_mode == 1:
                            clipped_name = os.path.join(browse, folder_01, clipped_path, browse_selected[num], 'clip_'+bq_name)
                        elif browse_selected_mode == 2:
                            clipped_name = os.path.join(browse, folder_01, clipped_path, 'clip_'+bq_name)
                        elif browse_selected_mode == 3:
                            clipped_name = os.path.join(browse, folder_01, clipped_path, browse_selected[num], 'clip_'+bq_name)

                        if clip_state[num] == 1:
                            warp = 'gdalwarp -q -cutline %s %s %s' %(shape_path, bq_filename, clipped_name)
                        else:
                            warp = 'gdalwarp -q -cutline %s -crop_to_cutline %s %s' %(shape_path, bq_filename, clipped_name)
                        os.system(warp)
                        # logger.append('Clipping file \n    "%s"\n' % (os.path.split(bq_filename)[1]))-----------------
                        if os.path.exists(clipped_name):
                            bq_filename = clipped_name
                        else:
                            self.progress.emit(':-( Clipping operation not performed on file \n"%s"\n' % bq_filename)
                    dataset = gdal.Open(bq_filename, GA_ReadOnly)
                    band = dataset.GetRasterBand(1)
                    quality_band[num] = band.ReadAsArray(0, 0, dataset.RasterXSize, dataset.RasterYSize)
                    #logger.append('Reading the quality band .......')

            # Define a function for getting raw bnad information
            def get_band_data(num, band_string, band_num, pan='no_pan'):
                if not len(bands[num][band_num]):
                    # Finding the full name of the perticular band file in the perticular folder
                    b_name_compile=re.compile(band_string)
                    b_name="".join(filter(lambda x: b_name_compile.search(x),
                                          folder_files[num]))  # "".join(x for x in dir_list b_name_compile.search(x))

                    # If a perticular band file exists in the given folder then
                    if b_name:
                        # Get the band filename to read
                        if browse_selected_mode == 1:
                            filename=os.path.join(browse, folder_01, extract_path, browse_selected[num], b_name)
                        elif browse_selected_mode == 2:
                            filename=os.path.join(browse, b_name)
                        elif browse_selected_mode == 3:
                            filename=os.path.join(browse, browse_selected[num], b_name)

                        if if_clip == 1:
                            # Get the band filename to store
                            if browse_selected_mode == 1:
                                clipped_name = os.path.join(browse, folder_01, clipped_path, browse_selected[num], 'clip_'+b_name)
                            elif browse_selected_mode == 2:
                                clipped_name = os.path.join(browse, folder_01, clipped_path, 'clip_'+b_name)
                            elif browse_selected_mode == 3:
                                clipped_name = os.path.join(browse, folder_01, clipped_path, browse_selected[num], 'clip_'+b_name)

                            if not os.path.exists(clipped_name):
                                if clip_state[num] == 1:
                                    warp = 'gdalwarp -q -cutline %s %s %s' % (shape_path, filename, clipped_name)
                                else:
                                    warp = 'gdalwarp -q -cutline %s -crop_to_cutline %s %s' % (
                                    shape_path, filename, clipped_name)
                                os.system(warp)
                                # logger.append('Clipping file\n    "%s"\n' % (os.path.split(filename)[1]))-----------------

                            if os.path.exists(clipped_name):
                                filename = clipped_name
                            else:
                                self.progress.emit(':-( Clipping operation not performed on file\n"%s"\n' %filename)

                        # Get the spatial reference info of the band
                        if pan == 'no_pan':
                            if not spatial_ref[num]:
                                spatial_ref[num]=gdali(filename, 1)
                        else:
                            if not spatial_ref_pan[num]:
                                spatial_ref_pan[num]=gdali(filename, 1)

                        # Read the band and store it as variable
                        bands[num][band_num]=gdali(filename)
                        #logger.append('Storing data in bands[%s][%s]'%(str(num), str(band_num)))

                        # Assign all the nodata pixels to NaN
                        if ip_user[0] == 'y':
                            bands[num][band_num][bands[num][band_num] == 0]=np.nan

                        # For Landsat8 removing the "exclude following features"
                        if sensor_type[num] == 'LC8' and sum(ip_user[4]) > 0 and pan == 'no_pan':
                            if not len(exclude_following_list[num]):
                                Exclude_following_list(num)
                            if not len(quality_band[num]):
                                Quality_band(num)

                            # Assign all the pixels NaN if it has the values which is in the exclude following list
                            for pix_value in exclude_following_list[num]:
                                bands[num][band_num][quality_band[num] == pix_value] = np.nan

            # --------------------------------------------------------------------------------------------------------
            ''' Define functions for various operations to perform'''

            # Define a function for extracting the band string and band info
            def band_string_info(sensor, band_string):
                if band_string == 'd':
                    if sensor == 'LC8':
                        return ([1, 1, 'B1.TIF', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 'b':
                    if sensor == 'LC8':
                        return ([1, 2, 'B2.TIF', 'no_pan'])
                    elif sensor in ['LE7', 'LT4', 'LT5']:
                        return ([1, 1, 'B1.TIF', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 'g':
                    if sensor == 'LC8':
                        return ([1, 3, 'B3.TIF', 'no_pan'])
                    elif sensor in ['LE7', 'LT4', 'LT5']:
                        return ([1, 2, 'B2.TIF', 'no_pan'])
                    elif sensor in ['LM1', 'LM2', 'LM3']:
                        return ([1, 4, 'B4.TIF', 'no_pan'])
                    elif sensor in ['LM4', 'LM5']:
                        return ([1, 1, 'B1.TIF', 'no_pan'])
                    elif sensor == 'L3':
                        return ([1, 2, 'BAND2.tif', 'no_pan'])
                    elif sensor == 'L4':
                        return ([1, 2, 'BAND2_RPC.tif', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 'r':
                    if sensor == 'LC8':
                        return ([1, 4, 'B4.TIF', 'no_pan'])
                    elif sensor in ['LE7', 'LT4', 'LT5']:
                        return ([1, 3, 'B3.TIF', 'no_pan'])
                    elif sensor in ['LM1', 'LM2', 'LM3']:
                        return ([1, 5, 'B5.TIF', 'no_pan'])
                    elif sensor in ['LM4', 'LM5']:
                        return ([1, 2, 'B2.TIF', 'no_pan'])
                    elif sensor == 'L3':
                        return ([1, 3, 'BAND3.tif', 'no_pan'])
                    elif sensor == 'L4':
                        return ([1, 3, 'BAND3_RPC.tif', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 'n':
                    if sensor == 'LC8':
                        return ([1, 5, 'B5.TIF', 'no_pan'])
                    elif sensor in ['LE7', 'LT4', 'LT5']:
                        return ([1, 4, 'B4.TIF', 'no_pan'])
                    elif sensor in ['LM1', 'LM2', 'LM3']:
                        return ([1, 6, 'B6.TIF', 'no_pan'])
                    elif sensor in ['LM4', 'LM5']:
                        return ([1, 3, 'B3.TIF', 'no_pan'])
                    elif sensor == 'L3':
                        return ([1, 4, 'BAND4.tif', 'no_pan'])
                    elif sensor == 'L4':
                        return ([1, 4, 'BAND4_RPC.tif', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 's':
                    if sensor == 'LC8':
                        return ([2, [6, 7], ['B6.TIF', 'B7.TIF'], 'no_pan'])
                    elif sensor == 'LE7':
                        return ([2, [5, 8], ['B5.TIF', 'B7.TIF'], 'no_pan'])
                    elif sensor in ['LT4', 'LT5']:
                        return ([2, [5, 7], ['B5.TIF', 'B7.TIF'], 'no_pan'])
                    elif sensor in ['LM1', 'LM2', 'LM3']:
                        return ([1, 7, 'B7.TIF', 'no_pan'])
                    elif sensor in ['LM4', 'LM5']:
                        return ([1, 4, 'B4.TIF', 'no_pan'])
                    elif sensor == 'L3':
                        return ([1, 5, 'BAND5.tif', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 't':
                    if sensor == 'LC8':
                        return ([2, [10, 11], ['B10.TIF', 'B11.TIF'], 'no_pan'])
                    elif sensor == 'LE7':
                        return ([2, [6, 7], ['B6_VCID_1.TIF', 'B6_VCID_2.TIF'], 'no_pan'])
                    elif sensor in ['LT4', 'LT5']:
                        return ([1, 6, 'B6.TIF', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 'p':
                    if sensor == 'LC8':
                        return ([1, 8, 'B8.TIF', 'pan'])
                    elif sensor == 'LE7':
                        return ([1, 9, 'B8.TIF', 'pan'])
                    else:
                        return ([None, None, None, None])
                elif band_string == 'c':
                    if sensor == 'LC8':
                        return ([1, 9, 'B9.TIF', 'no_pan'])
                    else:
                        return ([None, None, None, None])
                else:
                    return ([None, None, None, None])           # return (#bands, band#, band_name, if_PAN)

            # Define a function to add text of the band to the write info
            def band_text_add(band_symbol):
                if band_symbol == 'd':
                    return ('deep_blue')
                elif band_symbol == 'b':
                    return ('blue')
                elif band_symbol == 'g':
                    return ('green')
                elif band_symbol == 'r':
                    return ('red')
                elif band_symbol == 'n':
                    return ('nir')
                elif band_symbol == 's':
                    return ('swir')
                elif band_symbol == 't':
                    return ('tir')
                elif band_symbol == 'p':
                    return ('pan')
                elif band_symbol == 'c':
                    return ('cirus')

            # Define a function to get band_del_write_string information
            def band_del_w_string_info(num, band_w_del_string):
                del_list_info=list(band_w_del_string)
                if len(del_list_info) == 2:
                    band_text=band_text_add(del_list_info[1])
                    del_w_band_info=band_string_info(sensor_type[num], del_list_info[1])
                    del_list_info[1]=del_w_band_info[0]
                    if del_list_info[1] == 1:
                        del_list_info.extend(
                            [del_w_band_info[1], metadata_required[num][10] + del_w_band_info[2][:-4] +'_'+ band_text + '.TIF',
                             del_w_band_info[3]])
                    elif del_list_info[1] == 2:
                        del_list_info.extend([del_w_band_info[1],
                                              [metadata_required[num][10] + del_w_band_info[2][0][:-4] +'_'+ band_text + '.TIF',
                                               metadata_required[num][10] + del_w_band_info[2][1][:-4] +'_'+ band_text + '.TIF'],
                                              del_w_band_info[3]])
                    else:
                        del_list_info.extend([None, None, None])
                if len(del_list_info) == 1:
                    if sensor_type[num] != None:
                        if del_list_info[0] == 'V':
                            del_list_info.extend([1, 0, metadata_required[num][10] + 'NDVI.TIF', 'no_pan'])

                        del_w_band_info=band_string_info(sensor_type[num], 't')
                        if del_w_band_info[0] == 1:
                            if del_list_info[0] == 'A':
                                del_list_info.extend([1, 1, metadata_required[num][10] + 'Brightness_Temp.TIF', 'no_pan'])
                        elif del_w_band_info[0] == 2:
                            if del_list_info[0] == 'A':
                                del_list_info.extend([2, [1, 2],
                                                      [metadata_required[num][10] + 'Brightness_Temp_' + del_w_band_info[2][0],
                                                       metadata_required[num][10] + 'Brightness_Temp_' + del_w_band_info[2][1]],
                                                      'no_pan'])
                        else:
                            del_list_info.extend([None, None, None, None])
                    else:
                        del_list_info.extend([None, None, None, None])
                return (del_list_info)

            # Define a function to del the stored band data
            def band_data_del(num, band_del_string):
                del_list_info=band_del_w_string_info(num, band_del_string)
                if del_list_info[1] == 1:
                    if del_list_info[0] == 'b':
                        if len(bands[num][del_list_info[2]]):
                            bands[num][del_list_info[2]]=[]
                            #logger.append('Removed data from bands[%s][%s]'%(str(num),str(del_list_info[2])))
                    elif del_list_info[0] == 'a':
                        if len(output_ra[num][del_list_info[2]]):
                            output_ra[num][del_list_info[2]]=[]
                            #logger.append('Removed data from output_ra[%s][%s]' % (str(num), str(del_list_info[2])))
                    elif del_list_info[0] == 'e':
                        if len(output_re[num][del_list_info[2]]):
                            output_re[num][del_list_info[2]]=[]
                            #logger.append('Removed data from output_re[%s][%s]' % (str(num), str(del_list_info[2])))
                    elif del_list_info[0] in ['V', 'A', 'L']:
                        if len(output_extras[num][del_list_info[2]]):
                            output_extras[num][del_list_info[2]]=[]
                            #logger.append('Removed data from output_extras[%s][%s]' % (str(num), str(del_list_info[2])))
                if del_list_info[1] == 2:
                    # for 1st band
                    if del_list_info[0] == 'b':
                        if len(bands[num][del_list_info[2][0]]):
                            bands[num][del_list_info[2][0]]=[]
                            #logger.append('Removed data from bands[%s][%s]' % (str(num), str(del_list_info[2][0])))
                    elif del_list_info[0] == 'a':
                        if len(output_ra[num][del_list_info[2][0]]):
                            output_ra[num][del_list_info[2][0]]=[]
                            #logger.append('Removed data from output_ra[%s][%s]' % (str(num), str(del_list_info[2][0])))
                    elif del_list_info[0] == 'e':
                        if len(output_re[num][del_list_info[2][0]]):
                            output_re[num][del_list_info[2][0]]=[]
                            #logger.append('Removed data from output_re[%s][%s]' % (str(num), str(del_list_info[2][0])))
                    elif del_list_info[0] in ['A']:
                        if len(output_extras[num][del_list_info[2][0]]):
                            output_extras[num][del_list_info[2][0]]=[]
                            #logger.append('Removed data from output_extras[%s][%s]' % (str(num), str(del_list_info[2][0])))
                    # for 2nd band
                    if del_list_info[0] == 'b':
                        if len(bands[num][del_list_info[2][1]]):
                            bands[num][del_list_info[2][1]]=[]
                            #logger.append('Removed data from bands[%s][%s]' % (str(num), str(del_list_info[2][1])))
                    elif del_list_info[0] == 'a':
                        if len(output_ra[num][del_list_info[2][1]]):
                            output_ra[num][del_list_info[2][1]]=[]
                            #logger.append('Removed data from output_ra[%s][%s]' % (str(num), str(del_list_info[2][1])))
                    elif del_list_info[0] == 'e':
                        if len(output_re[num][del_list_info[2][1]]):
                            output_re[num][del_list_info[2][1]]=[]
                            #logger.append('Removed data from output_re[%s][%s]' % (str(num), str(del_list_info[2][1])))
                    elif del_list_info[0] in ['A']:
                        if len(output_extras[num][del_list_info[2][1]]):
                            output_extras[num][del_list_info[2][1]]=[]
                            #logger.append('Removed data from output_extras[%s][%s]' % (str(num), str(del_list_info[2][1])))

            # Define a function to write the band data
            def band_data_write(num, band_write_string):
                band_write_info=band_del_w_string_info(num, band_write_string)
                if band_write_info[4] == 'no_pan':
                    meta=spatial_ref[num]
                else:
                    meta=spatial_ref_pan[num]

                write_text=[None, None]
                if band_write_info[1] == 1:
                    if browse_selected_mode in [1, 3]:
                        if band_write_info[0] == 'a':
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       'radiance_' + band_write_info[3])
                        elif band_write_info[0] == 'e':
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       'reflectance_' + band_write_info[3])
                        else:
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num], band_write_info[3])
                    elif browse_selected_mode == 2:
                        if band_write_info[0] == 'a':
                            write_text[0]=os.path.join(browse, folder_01, output_path, 'radiance_' + band_write_info[3])
                        elif band_write_info[0] == 'e':
                            write_text[0]=os.path.join(browse, folder_01, output_path, 'reflectance_' + band_write_info[3])
                        else:
                            write_text[0]=os.path.join(browse, folder_01, output_path, band_write_info[3])
                if band_write_info[1] == 2:
                    # for 1st band
                    if browse_selected_mode in [1, 3]:
                        if band_write_info[0] == 'a':
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       'radiance_' + band_write_info[3][0])
                        elif band_write_info[0] == 'e':
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       'reflectance_' + band_write_info[3][0])
                        else:
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       band_write_info[3][0])
                    elif browse_selected_mode == 2:
                        if band_write_info[0] == 'a':
                            write_text[0]=os.path.join(browse, folder_01, output_path, 'radiance_' + band_write_info[3][0])
                        elif band_write_info[0] == 'e':
                            write_text[0]=os.path.join(browse, folder_01, output_path, 'reflectance_' + band_write_info[3][0])
                        else:
                            write_text[0]=os.path.join(browse, folder_01, output_path, band_write_info[3][0])
                    # for 2nd band
                    if browse_selected_mode in [1, 3]:
                        if band_write_info[0] == 'a':
                            write_text[1]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       'radiance_' + band_write_info[3][1])
                        elif band_write_info[0] == 'e':
                            write_text[1]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       'reflectance_' + band_write_info[3][1])
                        else:
                            write_text[1]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       band_write_info[3][1])
                    elif browse_selected_mode == 2:
                        if band_write_info[0] == 'a':
                            write_text[1]=os.path.join(browse, folder_01, output_path, 'radiance_' + band_write_info[3][1])
                        elif band_write_info[0] == 'e':
                            write_text[1]=os.path.join(browse, folder_01, output_path, 'reflectance_' + band_write_info[3][1])
                        else:
                            write_text[1]=os.path.join(browse, folder_01, output_path, band_write_info[3][1])

                # Writing the bands
                if band_write_info[1] == 1:
                    if band_write_info[0] in ['b', 'a', 'V', 'A', 'L']:
                        # with rasterio.open(write_text[0], 'w', count=1, dtype='float64', **meta) as bh:
                        if band_write_info[0] == 'b':
                            # bh.write(bands[num][band_write_info[2]], 1)
                            gdalo(write_text[0], meta, bands[num][band_write_info[2]], 1, 2)

                        elif band_write_info[0] == 'a':
                            # bh.write(output_ra[num][band_write_info[2]], 1)
                            gdalo(write_text[0], meta, output_ra[num][band_write_info[2]], 1, 6)

                        elif band_write_info[0] in ['V']:
                            # bh.write(output_extras[num][band_write_info[2]], 1)
                            gdalo(write_text[0], meta, output_extras[num][band_write_info[2]], 1, 6)

                        elif band_write_info[0] in ['A', 'L']:
                            # bh.write(output_extras[num][band_write_info[2]], 1)
                            gdalo(write_text[0], meta, output_extras[num][band_write_info[2]], 1, 6)

                    if band_write_info[0] == 'e':
                        if len(output_re[num][band_write_info[2]]):
                            # with rasterio.open(write_text[0], 'w', count=1, dtype='float64', **meta) as bh:
                            # bh.write(output_re[num][band_write_info[2]], 1)
                            gdalo(write_text[0], meta, output_re[num][band_write_info[2]], 1, 6)

                if band_write_info[1] == 2:
                    # for 1st file
                    # with rasterio.open(write_text[0], 'w', count=1, dtype='float64', **meta) as bh:
                    if band_write_info[0] == 'b':
                        # bh.write(bands[num][band_write_info[2][0]], 1)
                        gdalo(write_text[0], meta, bands[num][band_write_info[2][0]], 1, 2)
                    elif band_write_info[0] == 'a':
                        # bh.write(output_ra[num][band_write_info[2][0]], 1)
                        gdalo(write_text[0], meta, output_ra[num][band_write_info[2][0]], 1, 6)
                    elif band_write_info[0] == 'e':
                        # bh.write(output_re[num][band_write_info[2][0]], 1)
                        gdalo(write_text[0], meta, output_re[num][band_write_info[2][0]], 1, 6)
                    elif band_write_info[0] in ['A', 'L']:
                        # bh.write(output_extras[num][band_write_info[2][0]], 1)
                        gdalo(write_text[0], meta, output_extras[num][band_write_info[2][0]], 1, 6)
                    # for 2nd file
                    # with rasterio.open(write_text[1], 'w', count=1, dtype='float64', **meta) as bh:
                    if band_write_info[0] == 'b':
                        # bh.write(bands[num][band_write_info[2][1]], 1)
                        gdalo(write_text[1], meta, bands[num][band_write_info[2][1]], 1, 2)
                    elif band_write_info[0] == 'a':
                        # bh.write(output_ra[num][band_write_info[2][1]], 1)
                        gdalo(write_text[1], meta, output_ra[num][band_write_info[2][1]], 1, 6)
                    elif band_write_info[0] == 'e':
                        # bh.write(output_re[num][band_write_info[2][1]], 1)
                        gdalo(write_text[1], meta, output_re[num][band_write_info[2][1]], 1, 6)
                    elif band_write_info[0] in ['A', 'L']:
                        # bh.write(output_extras[num][band_write_info[2][1]], 1)
                        gdalo(write_text[1], meta, output_extras[num][band_write_info[2][1]], 1, 6)

                # Output to logger
                if write_text[0] != None:
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text[0])[1]))
                    if band_write_info[1] == 2:
                        self.progress.emit('    "%s"' % (os.path.split(write_text[1])[1]))
                else:
                    self.progress.emit(':-( Unavailable')

            # Define a function for calculating at sensor radiance
            def radiance_cal(num, band_string):
                band_info=band_string_info(sensor_type[num], band_string)
                if band_info[0] == 1:
                    if not len(output_ra[num][band_info[1]]):
                        if not len(bands[num][band_info[1]]):
                            get_band_data(num, band_info[2], band_info[1], band_info[3])
                        if len(bands[num][band_info[1]]):
                            if sensor_type[num] == 'LC8':
                                output_ra[num][band_info[1]]=(
                                                                 metadata_required[num][5][band_info[1]] * bands[num][
                                                                     band_info[1]]) + \
                                                             metadata_required[num][6][band_info[1]]
                                #logger.append('Stored data in output_ra[%s][%s]' % (str(num), str(band_info[1])))
                            if sensor_type[num] in ['LE7', 'LT4', 'LT5', 'LM1', 'LM2', 'LM3', 'LM4', 'LM5', 'L3', 'L4']:
                                output_ra[num][band_info[1]]=((
                                                                  metadata_required[num][5][band_info[1]] -
                                                                  metadata_required[num][6][
                                                                      band_info[1]]) *
                                                              (bands[num][band_info[1]] - metadata_required[num][8]) /
                                                              (metadata_required[num][7] - metadata_required[num][8])) + \
                                                             metadata_required[num][6][band_info[1]]
                                #logger.append('Stored data in output_ra[%s][%s]' % (str(num), str(band_info[1])))
                elif band_info[0] == 2:
                    # for 1st band
                    if not len(output_ra[num][band_info[1][0]]):
                        if not len(bands[num][band_info[1][0]]):
                            get_band_data(num, band_info[2][0], band_info[1][0], band_info[3])
                        if len(bands[num][band_info[1][0]]):
                            if sensor_type[num] == 'LC8':
                                output_ra[num][band_info[1][0]]=(metadata_required[num][5][band_info[1][0]] * bands[num][
                                    band_info[1][0]]) + \
                                                                metadata_required[num][6][band_info[1][0]]
                                #logger.append('Stored data in output_ra[%s][%s]' % (str(num), str(band_info[1][0])))
                            if sensor_type[num] in ['LE7', 'LT4', 'LT5', 'LM1', 'LM2', 'LM3', 'LM4', 'LM5', 'L3', 'L4']:
                                output_ra[num][band_info[1][0]]=((metadata_required[num][5][band_info[1][0]] -
                                                                  metadata_required[num][6][band_info[1][0]]) *
                                                                 (bands[num][band_info[1][0]] - metadata_required[num][8]) /
                                                                 (metadata_required[num][7] - metadata_required[num][
                                                                     8])) + \
                                                                metadata_required[num][6][band_info[1][0]]
                                #logger.append('Stored data in output_ra[%s][%s]' % (str(num), str(band_info[1][0])))
                    # for 2nd band
                    if not len(output_ra[num][band_info[1][1]]):
                        if not len(bands[num][band_info[1][1]]):
                            get_band_data(num, band_info[2][1], band_info[1][1], band_info[3])
                        if len(bands[num][band_info[1][1]]):
                            if sensor_type[num] == 'LC8':
                                output_ra[num][band_info[1][1]]=(metadata_required[num][5][band_info[1][1]] * bands[num][
                                    band_info[1][1]]) + \
                                                                metadata_required[num][6][band_info[1][1]]
                                #logger.append('Stored data in output_ra[%s][%s]' % (str(num), str(band_info[1][1])))
                            if sensor_type[num] in ['LE7', 'LT4', 'LT5', 'LM1', 'LM2', 'LM3', 'LM4', 'LM5', 'L3', 'L4']:
                                output_ra[num][band_info[1][1]]=((metadata_required[num][5][band_info[1][1]] -
                                                                  metadata_required[num][6][band_info[1][1]]) *
                                                                 (bands[num][band_info[1][1]] - metadata_required[num][8]) /
                                                                 (metadata_required[num][7] - metadata_required[num][
                                                                     8])) + \
                                                                metadata_required[num][6][band_info[1][1]]
                                #logger.append('Stored data in output_ra[%s][%s]' % (str(num), str(band_info[1][1])))

            # Define a function for calculating at satellite reflectance
            def reflectance_cal(num, band_string):
                if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                    band_info = band_string_info(sensor_type[num], band_string)
                    if band_info[0] == 1:
                        if not len(output_re[num][band_info[1]]):
                            if sensor_type[num] in ['LC8']:
                                if not len(bands[num][band_info[1]]):
                                    get_band_data(num, band_info[2], band_info[1], band_info[3])
                            elif sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                if not len(output_ra[num][band_info[1]]):
                                    radiance_cal(num, band_string)
                                    band_data_del(num, 'b' + band_string)

                            if len(bands[num][band_info[1]]) and sensor_type[num] == 'LC8':
                                output_re[num][band_info[1]] = ((metadata_required[num][7][band_info[1]] * bands[num][
                                    band_info[1]]) + \
                                                                metadata_required[num][8][band_info[1]]) / math.sin(
                                    math.radians(metadata_required[num][4]))
                                # logger.append('Stored data in output_re[%s][%s]' % (str(num), str(band_info[1])))
                            elif len(output_ra[num][band_info[1]]) and sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3',
                                                                                            'L4']:
                                radiance_cal(num, band_string)
                                output_re[num][band_info[1]] = (math.pi * output_ra[num][band_info[1]] * (
                                    metadata_required[num][1]) ** 2) / \
                                                               (metadata_required[num][2][band_info[1]] * math.sin(
                                                                   math.radians(metadata_required[num][4])))
                                # logger.append('Stored data in output_re[%s][%s]' % (str(num), str(band_info[1])))

                    if band_info[0] == 2:
                        # for 1st band
                        if not len(output_re[num][band_info[1][0]]):
                            if sensor_type[num] in ['LC8']:
                                if not len(bands[num][band_info[1][0]]):
                                    get_band_data(num, band_info[2][0], band_info[1][0], band_info[3])
                            elif sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                if not len(output_ra[num][band_info[1][0]]):
                                    radiance_cal(num, band_string)
                                    band_data_del(num, 'b' + band_string)

                            if len(bands[num][band_info[1][0]]) and sensor_type[num] == 'LC8':
                                output_re[num][band_info[1][0]] = ((metadata_required[num][7][band_info[1][0]] *
                                                                    bands[num][
                                                                        band_info[1][0]]) + \
                                                                   metadata_required[num][8][
                                                                       band_info[1][0]]) / math.sin(
                                    math.radians(metadata_required[num][4]))
                                # logger.append('Stored data in output_re[%s][%s]' % (str(num), str(band_info[1][0])))
                            elif len(output_ra[num][band_info[1][0]]) and sensor_type[num] in ['LE7', 'LT4', 'LT5',
                                                                                               'L3', 'L4']:
                                output_re[num][band_info[1][0]] = (math.pi * output_ra[num][band_info[1][0]] *
                                                                   metadata_required[num][1] ** 2) / \
                                                                  (
                                                                  metadata_required[num][2][band_info[1][0]] * math.sin(
                                                                      math.radians(metadata_required[num][4])))
                                # logger.append('Stored data in output_re[%s][%s]' % (str(num), str(band_info[1][0])))

                        # for 2nd band
                        if not len(output_re[num][band_info[1][1]]):
                            if sensor_type[num] in ['LC8']:
                                if not len(bands[num][band_info[1][1]]):
                                    get_band_data(num, band_info[2][1], band_info[1][1], band_info[3])

                            if len(bands[num][band_info[1][1]]) and sensor_type[num] == 'LC8':
                                output_re[num][band_info[1][1]] = ((metadata_required[num][7][band_info[1][1]] *
                                                                    bands[num][
                                                                        band_info[1][1]]) + \
                                                                   metadata_required[num][8][
                                                                       band_info[1][1]]) / math.sin(
                                    math.radians(metadata_required[num][4]))
                                # logger.append('Stored data in output_re[%s][%s]' % (str(num), str(band_info[1][1])))
                            if len(output_ra[num][band_info[1][1]]) and sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3',
                                                                                             'L4']:
                                output_re[num][band_info[1][1]] = (math.pi * output_ra[num][band_info[1][1]] *
                                                                   metadata_required[num][1] ** 2) / \
                                                                  (
                                                                      metadata_required[num][2][
                                                                          band_info[1][1]] * math.sin(
                                                                          math.radians(metadata_required[num][4])))
                                # logger.append('Stored data in output_re[%s][%s]' % (str(num), str(band_info[1][1])))

            # Define a fuction for tcc
            def tcc_w_del(num):
                if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5']:
                    radiance_cal(num, 'r')
                    band_info = band_string_info(sensor_type[num], 'r')
                    if sensor_type[num] in ['LC8']:
                        if not len(output_re[num][band_info[1]]):
                            if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                band_data_del(num, 'br')
                        else:
                            band_data_del(num, 'br')
                    elif sensor_type[num] in ['LE7', 'LT4', 'LT5']:
                        band_data_del(num, 'br')

                    radiance_cal(num, 'g')
                    band_data_del(num, 'bg')
                    radiance_cal(num, 'b')
                    band_data_del(num, 'bb')
                    r_info = band_string_info(sensor_type[num], 'r')
                    g_info = band_string_info(sensor_type[num], 'g')
                    b_info = band_string_info(sensor_type[num], 'b')

                    if browse_selected_mode in [1, 3]:
                        write_text = os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                  metadata_required[num][10] + 'TCC.TIF')
                    elif browse_selected_mode == 2:
                        write_text = os.path.join(browse, folder_01, output_path,
                                                  metadata_required[num][10] + 'TCC.TIF')

                    '''
                    with rasterio.open(write_text, 'w', count=3, dtype='float64', **spatial_ref[num]) as bh:
                        bh.write(output_re[num][r_info[1]], 1)
                        bh.write(output_re[num][g_info[1]], 2)
                        bh.write(output_re[num][b_info[1]], 3)
                    '''

                    gdalo(write_text, spatial_ref[num],
                          [output_ra[num][r_info[1]], output_ra[num][g_info[1]], output_ra[num][b_info[1]]], 3, 2)

                    # Output to logger
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                else:
                    # Output to logger
                    self.progress.emit(':-( Unavailable')

            # Define a function for fcc
            def fcc_w_del(num):
                if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                    radiance_cal(num, 'g')
                    band_data_del(num, 'bg')
                    radiance_cal(num, 'r')
                    band_info = band_string_info(sensor_type[num], 'r')
                    if sensor_type[num] in ['LC8']:
                        if not len(output_re[num][band_info[1]]):
                            if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                band_data_del(num, 'br')
                        else:
                            band_data_del(num, 'br')
                    elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                        band_data_del(num, 'br')

                    radiance_cal(num, 'n')
                    band_info = band_string_info(sensor_type[num], 'n')

                    if sensor_type[num] in ['LC8']:
                        if not len(output_re[num][band_info[1]]):
                            if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                band_data_del(num, 'bn')
                        else:
                            band_data_del(num, 'bn')
                    elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                        band_data_del(num, 'bn')
                        # if not len(output_re[num][band_info[1]]):
                        #     if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                        #         band_data_del(num, 'an')
                        # else:
                        #     band_data_del(num, 'an')

                    g_info = band_string_info(sensor_type[num], 'g')
                    r_info = band_string_info(sensor_type[num], 'r')
                    n_info = band_string_info(sensor_type[num], 'n')

                    if browse_selected_mode in [1, 3]:
                        write_text = os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                  metadata_required[num][10] + 'FCC.TIF')
                    elif browse_selected_mode == 2:
                        write_text = os.path.join(browse, folder_01, output_path,
                                                  metadata_required[num][10] + 'FCC.TIF')

                    '''
                    with rasterio.open(write_text, 'w', count=3, dtype='float64', **spatial_ref[num]) as bh:
                        bh.write(output_re[num][n_info[1]], 1)
                        bh.write(output_re[num][r_info[1]], 2)
                        bh.write(output_re[num][g_info[1]], 3)
                    '''

                    gdalo(write_text, spatial_ref[num],
                          [output_ra[num][n_info[1]], output_ra[num][r_info[1]], output_ra[num][g_info[1]]], 3, 2)
                    # Output to logger
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))

                elif sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                    radiance_cal(num, 'g')
                    band_data_del(num, 'bg')
                    radiance_cal(num, 'r')
                    band_data_del(num, 'br')
                    radiance_cal(num, 'n')
                    band_data_del(num, 'bn')
                    g_info=band_string_info(sensor_type[num], 'g')
                    r_info=band_string_info(sensor_type[num], 'r')
                    n_info=band_string_info(sensor_type[num], 'n')

                    if browse_selected_mode in [1, 3]:
                        write_text=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                metadata_required[num][10] + 'FCC.TIF')
                    elif browse_selected_mode == 2:
                        write_text=os.path.join(browse, folder_01, output_path, metadata_required[num][10] + 'FCC.TIF')

                    '''
                    with rasterio.open(write_text, 'w', count=3, dtype='float64', **spatial_ref[num]) as bh:
                        bh.write(output_ra[num][g_info[1]], 1)
                        bh.write(output_ra[num][r_info[1]], 2)
                        bh.write(output_ra[num][n_info[1]], 3)
                    '''

                    gdalo(write_text, spatial_ref[num],
                          [output_ra[num][n_info[1]], output_ra[num][r_info[1]], output_ra[num][g_info[1]]], 3, 2)
                    # Output to logger
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                else:
                    # Output to logger
                    self.progress.emit(':-( Unavailable')

            # Define a function for NDWI
            def ndwi_cal_w_del(num):
                if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                    reflectance_cal(num, 'g')
                    if sensor_type[num] == 'LC8' and ip_user[3][0] == 0 and ip_user[3][1] == 0:
                        band_data_del(num, 'bg')
                    elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                        band_data_del(num, 'bg')
                        if ip_user[3][0] == 0 and ip_user[3][1] == 0:
                            band_data_del(num, 'ag')

                    reflectance_cal(num, 'n')
                    if sensor_type[num] == 'LC8' and ip_user[3][1] == 0:
                        band_data_del(num, 'bn')
                    elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                        band_data_del(num, 'bn')
                        if ip_user[3][1] == 0:
                            band_data_del(num, 'an')

                    g_info = band_string_info(sensor_type[num], 'g')
                    n_info = band_string_info(sensor_type[num], 'n')

                    ndwi = (output_re[num][g_info[1]] - output_re[num][n_info[1]]) / (
                        output_re[num][g_info[1]] + output_re[num][n_info[1]])
                    if browse_selected_mode in [1, 3]:
                        write_text = os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                  metadata_required[num][10] + 'NDWI.TIF')
                    elif browse_selected_mode == 2:
                        write_text = os.path.join(browse, folder_01, output_path,
                                                  metadata_required[num][10] + 'NDWI.TIF')
                    gdalo(write_text, spatial_ref[num], ndwi, 1, 6)
                    # Output to logger
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                    '''
                    with rasterio.open(write_text, 'w', count=1, dtype='float64', **spatial_ref[num]) as bh:
                        bh.write(ndwi, 1)
                    '''

                elif sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                    radiance_cal(num, 'g')
                    band_data_del(num, 'bg')
                    radiance_cal(num, 'n')
                    band_data_del(num, 'bn')
                    g_info=band_string_info(sensor_type[num], 'g')
                    n_info=band_string_info(sensor_type[num], 'n')

                    ndwi=(output_ra[num][g_info[1]] - output_ra[num][n_info[1]]) / (
                        output_ra[num][g_info[1]] + output_ra[num][n_info[1]])
                    if browse_selected_mode in [1, 3]:
                        write_text=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                metadata_required[num][10] + 'NDWI.TIF')
                    elif browse_selected_mode == 2:
                        write_text=os.path.join(browse, folder_01, output_path, metadata_required[num][10] + 'NDWI.TIF')

                    # Writing the output
                    gdalo(write_text, spatial_ref[num], ndwi, 1, 6)
                    # Output to logger
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                    '''
                    with rasterio.open(write_text, 'w', count=1, dtype='float64', **spatial_ref[num]) as bh:
                        bh.write(ndwi, 1)
                    '''
                else:
                    self.progress.emit(':-( Unavailable')

            # Define a function for NDVI cal
            def ndvi_cal(num):
                if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                    if not len(output_extras[num][0]):
                        reflectance_cal(num, 'r')
                        band_data_del(num, 'br')
                        if sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                            band_data_del(num, 'ar')

                        reflectance_cal(num, 'n')
                        band_data_del(num, 'bn')
                        if sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                            band_data_del(num, 'an')

                        r_info = band_string_info(sensor_type[num], 'r')
                        n_info = band_string_info(sensor_type[num], 'n')
                        output_extras[num][0] = (output_re[num][n_info[1]] - output_re[num][r_info[1]]) / (
                            output_re[num][n_info[1]] + output_re[num][r_info[1]])
                        # logger.error('Stored data for NDVI in output_extras[%s][%s]' % (str(num), str(0)))
                        band_data_del(num, 'er')
                        band_data_del(num, 'en')

                elif sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                    if not len(output_extras[num][0]):
                        radiance_cal(num, 'r')
                        band_data_del(num, 'br')
                        radiance_cal(num, 'n')
                        band_data_del(num, 'bn')
                        r_info = band_string_info(sensor_type[num], 'r')
                        n_info = band_string_info(sensor_type[num], 'n')
                        output_extras[num][0] = (output_ra[num][n_info[1]] - output_ra[num][r_info[1]]) / (
                            output_ra[num][n_info[1]] + output_ra[num][r_info[1]])
                        # logger.error('Stored data for NDVI in output_extras[%s][%s]' % (str(num), str(0)))
                        band_data_del(num, 'ar')
                        band_data_del(num, 'an')

            # Define a function for At Satellite brightness Temperature Calculation
            def temp_cal(num):
                if not len(output_extras[num][1]) and sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5']:
                    radiance_cal(num, 't')
                    band_data_del(num, 'bt')
                    t_info = band_string_info(sensor_type[num], 't')  # [#bands, [numbers], [strings], pan]

                    if t_info[0] == 1:
                        output_extras[num][1] = (metadata_required[num][3][1] / np.log(
                            (metadata_required[num][3][0] / output_ra[num][t_info[1]]) + 1)) - 273.15
                        # logger.error('Stored data for temp in output_extras[%s][%s]' % (str(num), str(1)))
                    if t_info[0] == 2:
                        output_extras[num][1] = (metadata_required[num][3][1][0] / np.log(
                            (metadata_required[num][3][0][0] / output_ra[num][t_info[1][0]]) + 1)) - 273.15
                        # logger.error('Stored data for temp in output_extras[%s][%s]' % (str(num), str(1)))
                        output_extras[num][2] = (metadata_required[num][3][1][1] / np.log(
                            (metadata_required[num][3][0][1] / output_ra[num][t_info[1][1]]) + 1)) - 273.15
                        # logger.error('Stored data for temp in output_extras[%s][%s]' % (str(num), str(2)))

            # Define a function for LST calculation
            def lst_cal_w_del(num):
                if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5']:
                    t_info=band_string_info(sensor_type[num], 't')  # [#bands, [numbers], [strings], pan]
                    write_text=[None, None]
                    if t_info[0] == 1:
                        if browse_selected_mode in [1, 3]:
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       metadata_required[num][10] + 'LST.TIF')
                        elif browse_selected_mode == 2:
                            write_text[0]=os.path.join(browse, folder_01, output_path, metadata_required[num][10] + 'LST.TIF')
                    if t_info[0] == 2:
                        # for  1st band
                        if browse_selected_mode in [1, 3]:
                            write_text[0]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       metadata_required[num][10] + 'LST_' + t_info[2][0])
                        elif browse_selected_mode == 2:
                            write_text[0]=os.path.join(browse, folder_01, output_path,
                                                       metadata_required[num][10] + 'LST_' + t_info[2][0])
                        # for  2nd band
                        if browse_selected_mode in [1, 3]:
                            write_text[1]=os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                       metadata_required[num][10] + 'LST_' + t_info[2][1])
                        elif browse_selected_mode == 2:
                            write_text[1]=os.path.join(browse, folder_01, output_path,
                                                      metadata_required[num][10] + 'LST_' + t_info[2][1])

                    ndvi_cal(num)
                    if sensor_type[num] in ['LC8']:
                        band_data_del(num, 'er')
                        band_data_del(num, 'en')
                    elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                        band_data_del(num, 'er')
                        band_data_del(num, 'en')
                        band_data_del(num, 'ar')
                        band_data_del(num, 'an')
                    # Calculate Proportion of vegitation
                    pv=((output_extras[num][0] - np.nanmin(output_extras[num][0])) / (
                        np.nanmax(output_extras[num][0]) - np.nanmin(output_extras[num][0]))) ** 2
                    band_data_del(num, 'V')
                    # Calculation of emissivity
                    emissivity=0.004 * pv + 0.986

                    temp_cal(num)
                    band_data_del(num, 'at')
                    # Calculation of LST
                    if t_info[0] == 1:
                        lst=output_extras[num][1] / (
                            1 + metadata_required[num][9] * (output_extras[num][1] / 14380) * np.log(emissivity))
                        '''
                        with rasterio.open(write_text[0], 'w', count= 1, dtype='float64', **spatial_ref[num]) as bh:
                            bh.write(lst, 1)
                        '''
                        gdalo(write_text[0], spatial_ref[num], lst, 1, 6)

                    if t_info[0] == 2:
                        lst=output_extras[num][1] / (
                            1 + metadata_required[num][9][0] * (output_extras[num][1] / 14380) * np.log(emissivity))
                        '''
                        with rasterio.open(write_text[0], 'w', count=1, dtype='float64', **spatial_ref[num]) as bh:
                            bh.write(lst, 1)
                        '''
                        gdalo(write_text[0], spatial_ref[num], lst, 1, 6)

                        lst=output_extras[num][2] / (
                            1 + metadata_required[num][9][1] * (output_extras[num][2] / 14380) * np.log(emissivity))
                        '''
                        with rasterio.open(write_text[1], 'w', count=1, dtype='float64', **spatial_ref[num]) as bh:
                            bh.write(lst, 1)
                        '''
                        gdalo(write_text[1], spatial_ref[num], lst, 1, 6)
                    band_data_del(num, 'A')

                    # Output to logger
                    self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text[0])[1]))
                    if t_info[0] == 2:
                        self.progress.emit('    "%s"' % (os.path.split(write_text[1])[1]))
                else:
                    self.progress.emit(':-( Unavailable')

            def Expression(expression):
                expression = expression.replace(' ', '').lower()
                expression = ' N'.join(expression.split('min'))
                expression = ' X'.join(expression.split('max'))

                expression = expression.decode()
                expression = [token[1] for token in tokenize.generate_tokens(StringIO(expression).readline) if token[1]]
                return ([c[0].encode() if c.encode().isalpha() else c.encode() for c in expression])

            # ======================================================================================
            # ============== Outputs ===================
            # Using the function created and storing the data to variables as array
            self.progress.emit('>>>----------------------------------------------------------------------<<<\n')
            for num in xrange(len(bands)):
                if sensor_type[num] and clip_state[num] != 0:
                    self.progress.emit('\n>>>~~~~~\n')
                    if browse_selected_mode in [1,3]:
                        self.progress.emit('Processing on the data of %s' %browse_selected[num])
                    # for deep blue band
                    if ip_user[1][0] == 1 or ip_user[2][0] == 1:
                        self.progress.emit('\n>>> For Deep Blue band:\n')
                    if ip_user[1][0] == 1:
                        radiance_cal(num, 'd')
                        if ip_user[2][0] == 0:
                            band_data_del(num, 'bd')
                        band_data_write(num, 'ad')
                        band_data_del(num, 'ad')
                    if ip_user[2][0] == 1:
                        reflectance_cal(num, 'd')
                        band_data_del(num, 'bd')
                        band_data_write(num, 'ed')
                        band_data_del(num, 'ed')

                    # for SWIR band
                    if ip_user[1][5] == 1 or ip_user[2][5] == 1:
                        self.progress.emit('\n>>> For Short Wave IR band:\n')
                    if ip_user[1][5] == 1:
                        radiance_cal(num, 's')
                        if sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L3']:
                            band_data_del(num, 'bs')
                        else:
                            if ip_user[2][5] == 0:
                                band_data_del(num, 'bs')
                        band_data_write(num, 'as')
                        if not sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L3'] or ip_user[2][5] == 0:
                            band_data_del(num, 'as')
                    if ip_user[2][5] == 1:
                        reflectance_cal(num, 's')
                        band_data_del(num, 'as')
                        band_data_del(num, 'bs')
                        band_data_write(num, 'es')
                        band_data_del(num, 'es')

                    # for Cirrus band
                    if ip_user[1][8] == 1 or ip_user[2][8] == 1:
                        self.progress.emit('\n>>> For Cirrus band:\n')
                    if ip_user[1][8] == 1:
                        radiance_cal(num, 'c')
                        if ip_user[2][8] == 0:
                            band_data_del(num, 'bc')
                        band_data_write(num, 'ac')
                        band_data_del(num, 'ac')
                    if ip_user[2][8] == 1:
                        reflectance_cal(num, 'c')
                        band_data_del(num, 'bc')
                        band_data_write(num, 'ec')
                        band_data_del(num, 'ec')

                    # for thermal band
                    if ip_user[1][6] == 1:
                        self.progress.emit('\n>>> For Thermal IR band:\n')
                        radiance_cal(num, 't')
                        band_data_del(num, 'bt')
                        band_data_write(num, 'at')
                        if ip_user[3][4] == 0 and ip_user[3][5] == 0:
                            band_data_del(num, 'at')

                    # for at satellite brightness temp
                    if ip_user[3][4] == 1:
                        self.progress.emit('\n>>> For At Satellite Temperature:\n')
                        temp_cal(num)
                        band_data_del(num, 'at')
                        band_data_write(num, 'A')
                        if ip_user[3][5] == 0:
                            band_data_del(num, 'A')

                    # for blue band
                    if ip_user[1][1] == 1 or ip_user[2][1] == 1:
                        self.progress.emit('\n>>> For Blue band:\n')
                    if ip_user[1][1] == 1:
                        radiance_cal(num, 'b')
                        if sensor_type[num] in ['LE7', 'LT5', 'LT4']:
                            band_data_del(num, 'bb')
                        else:
                            if ip_user[2][1] == 0:
                                band_data_del(num, 'bb')
                        band_data_write(num, 'ab')
                        if ip_user[3][0] == 0 and (not sensor_type[num] in ['LE7', 'LT5', 'LT4'] or ip_user[2][1] == 0):
                            band_data_del(num, 'ab')
                    if ip_user[2][1] == 1:
                        reflectance_cal(num, 'b')
                        if ip_user[3][0] == 0:
                            band_data_del(num, 'ab')
                        band_data_del(num, 'bb')
                        band_data_write(num, 'eb')
                        band_data_del(num, 'eb')

                    # for green band
                    if ip_user[1][2] == 1 or ip_user[2][2] == 1:
                        self.progress.emit('\n>>> For Green band:\n')
                    if ip_user[1][2] == 1:
                        radiance_cal(num, 'g')
                        if sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L4', 'L3']:
                            band_data_del(num, 'bg')
                        else:
                            if ip_user[2][2] == 0 and ip_user[3][3] == 0:
                                band_data_del(num, 'bg')
                        band_data_write(num, 'ag')
                        if ip_user[3][0] == 0 and ip_user[3][1] == 0 and (
                            not sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L4', 'L3'] or (
                                ip_user[2][2] == 0 and ip_user[3][3] == 0)):
                            band_data_del(num, 'ag')
                    if ip_user[2][2] == 1:
                        reflectance_cal(num, 'g')
                        if ip_user[3][0] == 0 and ip_user[3][1] == 0:
                            band_data_del(num, 'ag')
                        band_data_del(num, 'bg')
                        band_data_write(num, 'eg')
                        if ip_user[3][3] == 0:
                            band_data_del(num, 'eg')

                    # for red band
                    if ip_user[1][3] == 1 or ip_user[2][3] == 1:
                        self.progress.emit('\n>>> For Red band:\n')
                    if ip_user[1][3] == 1:
                        radiance_cal(num, 'r')
                        if sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L4', 'L3']:
                            band_data_del(num, 'br')
                        else:
                            if ip_user[2][3] == 0 and ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                band_data_del(num, 'br')
                        band_data_write(num, 'ar')
                        if ip_user[3][0] == 0 and ip_user[3][1] == 0 and (
                            not sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L4', 'L3'] or (
                                    ip_user[2][3] == 0 and ip_user[3][2] == 0 and ip_user[3][5] == 0)):
                            band_data_del(num, 'ar')
                    if ip_user[2][3] == 1:
                        reflectance_cal(num, 'r')
                        if ip_user[3][0] == 0 and ip_user[3][1] == 0:
                            band_data_del(num, 'ar')
                        band_data_del(num, 'br')
                        band_data_write(num, 'er')
                        if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                            band_data_del(num, 'er')

                    # for NIR band
                    if ip_user[1][4] == 1 or ip_user[2][4] == 1:
                        self.progress.emit('\n>>> For Near IR band:\n')
                    if ip_user[1][4] == 1:
                        radiance_cal(num, 'n')
                        if sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L4', 'L3']:
                            band_data_del(num, 'bn')
                        else:
                            if ip_user[2][4] == 0 and ip_user[3][2] == 0 and ip_user[3][5] == 0 and ip_user[3][3] == 0:
                                band_data_del(num, 'bn')
                        band_data_write(num, 'an')
                        if ip_user[3][1] == 0 and (not sensor_type[num] in ['LE7', 'LT5', 'LT4', 'L4', 'L3'] or (
                                        ip_user[2][4] == 0 and ip_user[3][2] == 0 and ip_user[3][5] == 0 and ip_user[3][
                            3] == 0)):
                            band_data_del(num, 'an')
                    if ip_user[2][4] == 1:
                        reflectance_cal(num, 'n')
                        if ip_user[3][1] == 0:
                            band_data_del(num, 'an')
                        band_data_del(num, 'bn')
                        band_data_write(num, 'en')
                        if ip_user[3][2] == 0 and ip_user[3][5] == 0 and ip_user[3][3] == 0:
                            band_data_del(num, 'en')

                    # for NDWI
                    if ip_user[3][3] == 1:
                        self.progress.emit('\n>>> For Normalized Difference Water Index:\n')
                        ndwi_cal_w_del(num)
                        if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                            band_data_del(num, 'eg')
                            if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                band_data_del(num, 'en')
                        elif sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                            if ip_user[3][1] == 0:
                                band_data_del(num, 'ag')
                            if ip_user[3][2] == 0:
                                band_data_del(num, 'an')

                    # for FCC
                    if ip_user[3][1] == 1:
                        self.progress.emit('\n>>> For False Color Composite:\n')
                        fcc_w_del(num)
                        if sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                            if ip_user[3][2] == 0:
                                band_data_del(num, 'an')
                        elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                            band_info = band_string_info(sensor_type[num], 'n')
                            if not len(output_re[num][band_info[1]]):
                                if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                    band_data_del(num, 'an')
                            else:
                                band_data_del(num, 'an')
                        elif sensor_type[num] in ['LC8']:
                            band_data_del(num, 'an')

                        if ip_user[3][0] == 0:
                            band_data_del(num, 'ag')
                            if sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                                if ip_user[3][2] == 0:
                                    band_data_del(num, 'ar')
                            elif sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                band_info = band_string_info(sensor_type[num], 'r')
                                if not len(output_re[num][band_info[1]]):
                                    if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                        band_data_del(num, 'ar')
                                else:
                                    band_data_del(num, 'ar')
                            elif sensor_type[num] in ['LC8']:
                                band_data_del(num, 'ar')

                    # for TCC
                    if ip_user[3][0] == 1:
                        self.progress.emit('\n>>> For True Color Composite:\n')
                        tcc_w_del(num)
                        band_data_del(num, 'ab')
                        band_data_del(num, 'ag')
                        if sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                            if ip_user[3][2] == 0:
                                band_data_del(num, 'ar')
                        elif sensor_type[num] in ['LE7', 'LT4', 'LT5']:
                            band_info = band_string_info(sensor_type[num], 'r')
                            if not len(output_re[num][band_info[1]]):
                                if ip_user[3][2] == 0 and ip_user[3][5] == 0:
                                    band_data_del(num, 'ar')
                            else:
                                band_data_del(num, 'ar')
                        elif sensor_type[num] in ['LC8']:
                            band_data_del(num, 'ar')

                    # for NDVI
                    if ip_user[3][2] == 1:
                        self.progress.emit('\n>>> For Normalized Difference Vegetation Index:\n')
                        ndvi_cal(num)
                        if sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                            band_data_write(num, 'V')
                            if ip_user[3][5] == 0:
                                band_data_del(num, 'V')
                        elif sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                            band_data_write(num, 'V')
                            band_data_del(num, 'V')

                    # for LST
                    if ip_user[3][5] == 1:
                        self.progress.emit('\n>>> For Land Surface Temperature:\n')
                        lst_cal_w_del(num)

                    # for PAN band
                    if ip_user[1][7] == 1 or ip_user[2][7] == 1:
                        self.progress.emit('\n>>> For PAN band:\n')
                    if ip_user[1][7] == 1:
                        radiance_cal(num, 'p')
                        if sensor_type[num] in ['LE7']:
                            band_data_del(num, 'bp')
                        else:
                            if ip_user[2][7] == 0:
                                band_data_del(num, 'bp')
                        band_data_write(num, 'ap')
                        if not sensor_type[num] in ['LE7'] or ip_user[2][7] == 0:
                            band_data_del(num, 'ap')
                    if ip_user[2][7] == 1:
                        reflectance_cal(num, 'p')
                        band_data_del(num, 'ap')
                        band_data_del(num, 'bp')
                        band_data_write(num, 'ep')
                        band_data_del(num, 'ep')

                    # For custom outputs
                    for out,text in enumerate(custom_names):
                        if custom[out]:
                            self.progress.emit('\n>>> For custom output %s:\n'%text)
                            expression = Expression(custom[out])
                            custom[out] = ''.join(expression)

                            min_index = [m.start() for m in re.finditer('N', custom[out])]

                            for n, i in enumerate(min_index):
                                a = custom[out].__getslice__(0, i - 1 + n)
                                b = custom[out].__getslice__(i - 1 + n, i + n)
                                c = custom[out].__getslice__(i + 1 + n, len(custom[out]) + n)
                                custom[out] = '%sA%sB%s' % (a, b, c)

                            max_index = [m.start() for m in re.finditer('X', custom[out])]

                            for n, i in enumerate(max_index):
                                a = custom[out].__getslice__(0, i - 1 + n)
                                b = custom[out].__getslice__(i - 1 + n, i + n)
                                c = custom[out].__getslice__(i + 1 + n, len(custom[out]) + n)
                                custom[out] = '%sY%sZ%s' % (a, b, c)


                            custom_bands_name = []
                            [custom_bands_name.append(i) for i in expression if i.isalpha() and i.islower()]
                            custom_bands_name = list(set(custom_bands_name))

                            # band_info=[]
                            custom_bands_one = []
                            custom_bands_two = []

                            band_number = 0
                            for band in custom_bands_name:
                                if 't' not in custom_bands_name and sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                    reflectance_cal(num, band)
                                elif 't' in custom_bands_name or sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                                    radiance_cal(num, band)
                                band_data_del(num, 'b' + band)

                                if 't' not in custom_bands_name and sensor_type[num] in ['LE7', 'LT4', 'LT5', 'L4', 'L3']:
                                    band_data_del(num, 'a' + band)

                                info = band_string_info(sensor_type[num], band)
                                if info[0] == None:
                                    self.progress.emit(':-( Band/s unavailable !')
                                    break
                                else:
                                    band_number = 1 if band_number == 0 else band_number
                                band_number = 2 if info[0]==2 else band_number
                                #band_info.append(info)

                                if 't' not in custom_bands_name and sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                    if info[0] == 1:
                                        custom_bands_one.append('output_re[num][%d]' % (info[1]))
                                        custom_bands_two.append('output_re[num][%d]' % (info[1]))
                                    elif info[0] == 2:
                                        custom_bands_one.append('output_re[num][%d]' % (info[1][0]))
                                        custom_bands_two.append('output_re[num][%d]' % (info[1][1]))
                                elif 't' in custom_bands_name or sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                                    if info[0] == 1:
                                        custom_bands_one.append('output_ra[num][%d]' % (info[1]))
                                        custom_bands_two.append('output_ra[num][%d]' % (info[1]))
                                    elif info[0] == 2:
                                        custom_bands_one.append('output_ra[num][%d]' % (info[1][0]))
                                        custom_bands_two.append('output_ra[num][%d]' % (info[1][1]))

                            # For single band expression
                            if band_number == 1:
                                eval_exp = []
                                for word in custom[out]:
                                    eval_exp.append(word+'!@#$') if word.isalpha() else eval_exp.append(word)
                                custom_bands_name_new = [a+'!@#$' for a in custom_bands_name if a.isalpha()]

                                for i,j in zip(custom_bands_name_new, custom_bands_one):
                                    eval_exp = [w.replace(i, j) for w in eval_exp]
                                eval_exp = ''.join(eval_exp)

                                eval_exp = eval_exp.replace('A!@#$', 'np.nanmin(')
                                eval_exp = eval_exp.replace('B!@#$', ')')
                                eval_exp = eval_exp.replace('Y!@#$', 'np.nanmax(')
                                eval_exp = eval_exp.replace('Z!@#$', ')')

                                try:
                                    output = eval(eval_exp)
                                except:
                                    self.progress.emit(':-( Expression error !')
                                    continue

                                for band in custom_bands_name:
                                    if 't' not in custom_bands_name and sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                        band_data_del(num, 'e' + band)
                                    elif 't' in custom_bands_name or sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                                        band_data_del(num, 'a'+band)
                                if browse_selected_mode in [1, 3]:
                                    write_text = os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                              metadata_required[num][10] + '%s.TIF'%text)
                                elif browse_selected_mode == 2:
                                    write_text = os.path.join(browse, folder_01, output_path,
                                                              metadata_required[num][10] + '%s.TIF'%text)

                                self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                                gdalo(write_text, spatial_ref[num], output, 1, 6)
                                output = []

                            if band_number == 2:

                                custom_bands_name_new = [a + '!@#$' for a in custom_bands_name if a.isalpha()]

                                # For first band
                                eval_exp = []
                                for word in custom[out]:
                                    eval_exp.append(word + '!@#$') if word.isalpha() else eval_exp.append(word)

                                for i,j in zip(custom_bands_name_new, custom_bands_one):
                                    eval_exp = [w.replace(i, j) for w in eval_exp]
                                eval_exp = ''.join(eval_exp)

                                eval_exp = eval_exp.replace('A!@#$', 'np.nanmin(')
                                eval_exp = eval_exp.replace('B!@#$', ')')
                                eval_exp = eval_exp.replace('Y!@#$', 'np.nanmax(')
                                eval_exp = eval_exp.replace('Z!@#$', ')')

                                try:
                                    output = eval(eval_exp)
                                except:
                                    self.progress.emit(':-( Expression error !')
                                    continue

                                if browse_selected_mode in [1, 3]:
                                    write_text = os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                              metadata_required[num][10] + '%s_01.TIF'%text)
                                elif browse_selected_mode == 2:
                                    write_text = os.path.join(browse, folder_01, output_path,
                                                              metadata_required[num][10] + '%s_01.TIF'%text)

                                self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                                gdalo(write_text, spatial_ref[num], output, 1, 6)
                                output=[]

                                # For second band
                                eval_exp = []
                                for word in custom[out]:
                                    eval_exp.append(word + '!@#$') if word.isalpha() else eval_exp.append(word)

                                for i,j in zip(custom_bands_name_new, custom_bands_two):
                                    eval_exp = [w.replace(i, j) for w in eval_exp]
                                eval_exp = ''.join(eval_exp)

                                eval_exp = eval_exp.replace('A!@#$', 'np.nanmin(')
                                eval_exp = eval_exp.replace('B!@#$', ')')
                                eval_exp = eval_exp.replace('Y!@#$', 'np.nanmax(')
                                eval_exp = eval_exp.replace('Z!@#$', ')')

                                try:
                                    output = eval(eval_exp)
                                except:
                                    self.progress.emit(':-( Expression error !')
                                    continue

                                for band in custom_bands_name:
                                    if 't' not in custom_bands_name and sensor_type[num] in ['LC8', 'LE7', 'LT4', 'LT5', 'L3', 'L4']:
                                        band_data_del(num, 'e' + band)
                                    elif 't' in custom_bands_name or sensor_type[num] in ['LM1', 'LM2', 'LM3', 'LM4', 'LM5']:
                                        band_data_del(num, 'a'+band)

                                if browse_selected_mode in [1, 3]:
                                    write_text = os.path.join(browse, folder_01, output_path, browse_selected[num],
                                                              metadata_required[num][10] + '%s_02.TIF'%text)
                                elif browse_selected_mode == 2:
                                    write_text = os.path.join(browse, folder_01, output_path,
                                                              metadata_required[num][10] + '%s_02.TIF'%text)

                                self.progress.emit('Wrote file\n    "%s"' % (os.path.split(write_text)[1]))
                                gdalo(write_text, spatial_ref[num], output, 1, 6)
                                output = []


                    # Remove the quality band data
                    if sensor_type[num] == 'LC8' and sum(ip_user[4]) > 0:
                        quality_band[num] = []
                        #logger.append('quality band removed!')
            del num

            # ---------------------------------------------------------------------------------------------------------


            # ----------------------------------------------------------------------------------------------------------------------------------------------
            # Output the time required for the total process
            self.progress.emit('\n>>>----------------------------------------------------------------------<<<\n'
                         '=============  Process Completed =============='
                         '\n>>>----------------------------------------------------------------------<<<\n')
            if int((time.time() - start_time) / 60) == 0 and  int((time.time() - start_time) % 60) == 0:
                self.progress.emit('Time required for the complete process: Less than 1 sec.')
            else:
                self.progress.emit('Time required for the complete process: %i min. %i sec.' % (
                ((time.time() - start_time) / 60), (time.time() - start_time) % 60))

            self.progress.emit('\n>>>----------------------------------------------------------------------<<<\n'
                         '=============  Ready to Go Again! =============='
                         '\n>>>----------------------------------------------------------------------<<<\n\n')

            # On successful completion of all the porcesses
            finish_cond = 1

        except Exception, e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())

        self.finished.emit(finish_cond)

    # def kill(self):
    #     self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring)
    progress = QtCore.pyqtSignal(str)

class RSGIS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RSGIS_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&RS&GIS')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'RSGIS')
        self.toolbar.setObjectName(u'RSGIS')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('RSGIS', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = RSGISDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        self.Startup()

        self.dlg.cb_re0.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re0, 0, 1))
        self.dlg.cb_re1.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re1, 1, 1))
        self.dlg.cb_re2.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re2, 2, 1))
        self.dlg.cb_re3.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re3, 3, 1))
        self.dlg.cb_re4.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re4, 4, 1))
        self.dlg.cb_re5.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re5, 5, 1))
        self.dlg.cb_re7.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re7, 7, 1))
        self.dlg.cb_re8.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_re8, 8, 1))

        self.dlg.cb_ra0.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra0, 0, 2))
        self.dlg.cb_ra1.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra1, 1, 2))
        self.dlg.cb_ra2.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra2, 2, 2))
        self.dlg.cb_ra3.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra3, 3, 2))
        self.dlg.cb_ra4.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra4, 4, 2))
        self.dlg.cb_ra5.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra5, 5, 2))
        self.dlg.cb_ra6.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra6, 6, 2))
        self.dlg.cb_ra7.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra7, 7, 2))
        self.dlg.cb_ra8.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ra8, 8, 2))

        self.dlg.cb_ex0.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ex0, 0, 3))
        self.dlg.cb_ex1.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ex1, 1, 3))
        self.dlg.cb_ex2.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ex2, 2, 3))
        self.dlg.cb_ex3.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ex3, 3, 3))
        self.dlg.cb_ex4.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ex4, 4, 3))
        self.dlg.cb_ex5.stateChanged.connect(lambda: self.CheckB_status(self.dlg.cb_ex5, 5, 3))

        self.dlg.cb_cirrus.stateChanged.connect(self.CB_Status)
        self.dlg.cb_clouds.stateChanged.connect(self.CB_Status)

        self.dlg.cb_nodata.stateChanged.connect(self.Cb_nodata)

        self.dlg.cb_clip.stateChanged.connect(self.Cb_clip)

        self.dlg.pb_cancel.clicked.connect(self.Pb_cancel)

        # for browsing
        # self.dlg.cob_mode.currentIndexChanged.connect(self.Cob_mode)
        self.dlg.cob_mode.currentIndexChanged.connect(self.Cob_mode)

        self.dlg.pb_browse.clicked.connect(lambda: self.Pb_browse(browse_selected_mode))
        self.dlg.pb_shape.clicked.connect(self.Pb_shape)
        # self.dlg.pb_processing.clicked.connect(self.Pb_processing)
        self.dlg.pb_processing.clicked.connect(self.startWorker)

        # self.dlg.pb_exclude.clicked.connect(self.Pb_exclude)

        # ----------------------------------------------------------------------------------------------
        # Create dummy buttons for exporting data
        self.dlg.label_browse = QtGui.QLabel()
        self.dlg.label_browse_selected = QtGui.QLabel()
        self.dlg.label_browse_selected_ext = QtGui.QLabel()
        self.dlg.label_browse_selected_mode = QtGui.QLabel()
        self.dlg.label_no_data = QtGui.QLabel()
        self.dlg.label_no_data.setText('y')
        self.dlg.label_ip_toa_ra = QtGui.QLabel()
        self.dlg.label_ip_toa_ra.setText('0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0')
        self.dlg.label_ip_toa_re = QtGui.QLabel()
        self.dlg.label_ip_toa_re.setText('0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0')
        self.dlg.label_ip_extras = QtGui.QLabel()
        self.dlg.label_ip_extras.setText('0!@#$0!@#$0!@#$0!@#$0!@#$0')
        self.dlg.label_exclude_window_state = QtGui.QLabel()
        self.dlg.label_exclude_window_state.setText('not_clicked')
        self.dlg.label_shape_path = QtGui.QLabel()
        self.dlg.label_shape_path.setText('not_selected')
        self.dlg.label_clip_status = QtGui.QLabel()
        self.dlg.label_clip_status.setText('0')
        self.dlg.label_ip_exclude_following = QtGui.QLabel()
        self.dlg.label_ip_exclude_following.setText(
            '0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0!@#$0')

        return action

    def workerFinished(self, finish_cond):
        logger = self.dlg.tb_terminal

        # clean up the worker and thread
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        if finish_cond == 0:
            logger.append('Process stopped in between ! You are good to go again.')

    def workerError(self, e, exception_string):
        logger = self.dlg.tb_terminal
        logger.append(':-( Error:\n\n %s' %str(exception_string))

    def startWorker(self):

        no_data = str(self.dlg.label_no_data.text())
        ip_toa_ra = [int(x) for x in ((self.dlg.label_ip_toa_ra.text()).split('!@#$'))]
        ip_toa_re = [int(x) for x in ((self.dlg.label_ip_toa_re.text()).split('!@#$'))]
        ip_extras = [int(x) for x in ((self.dlg.label_ip_extras.text()).split('!@#$'))]

        custom, custom_names = [[] for i in xrange(4)], [[] for i in xrange(4)]
        custom[0], custom[1], custom[2], custom[3] = str(self.dlg.le_ex_01.text()), str(self.dlg.le_ex_02.text()), str(
            self.dlg.le_ex_03.text()), str(self.dlg.le_ex_04.text())
        custom_names[0], custom_names[1], custom_names[2], custom_names[3] = str(self.dlg.le_output_01.text()), str(
            self.dlg.le_output_02.text()), str(
            self.dlg.le_output_03.text()), str(self.dlg.le_output_04.text())

        custom_names[0] = custom_names[0].replace(' ', '_') if custom_names[0] else 'Custom01'
        custom_names[1] = custom_names[1].replace(' ', '_') if custom_names[1] else 'Custom02'
        custom_names[2] = custom_names[2].replace(' ', '_') if custom_names[2] else 'Custom03'
        custom_names[3] = custom_names[3].replace(' ', '_') if custom_names[3] else 'Custom04'

        ip_exclude_following = [int(x) for x in ((self.dlg.label_ip_exclude_following.text()).split('!@#$'))]

        browse = str(self.dlg.label_browse.text())

        browse_selected_obj = (self.dlg.label_browse_selected.text()).split('!@#$')

        browse_selected_ext_obj = (self.dlg.label_browse_selected_ext.text()).split('!@#$')
        browse_selected_mode = int(self.dlg.label_browse_selected_mode.text())
        shape_path = str(self.dlg.label_shape_path.text())
        if_clip = int(self.dlg.label_clip_status.text())

        ip_user = []
        for list_add in [no_data, ip_toa_ra, ip_toa_re, ip_extras, ip_exclude_following]:
            ip_user.append(list_add)
        del list_add, no_data, ip_toa_ra, ip_toa_re, ip_extras, ip_exclude_following


        worker = Worker(ip_user, custom, custom_names, browse, browse_selected_obj, browse_selected_ext_obj, browse_selected_mode, shape_path, if_clip)

        # start the worker in a new thread
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)

        worker.progress.connect(self.showmsg)

        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker

    def showmsg(self, signal):
        logger = self.dlg.tb_terminal
        logger.append(str(signal))

    def Startup(self):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        logger.append('Welcome to RS&GIS_V17.0 !\n\n'
                     'Start deriving the outputs with 6 simple steps:\n'
                     '    1. Select the mode of selection\n'
                     '    2. Browse the files to process\n'
                     '    3. Select the area of interest shape file\n'
                     '    4. Select all the desired outputs\n'
                     '    5. Give some extra details required\n'
                     '    6. Start Processing!\n\n'
                     'Supports:\n'
                     '    > LISS IV, LISS III data\n'
                     # '    > LISS III data\n'
                     '    > Landsat 8 OLI/TIRS sensor level 1 data\n'
                     '    > Landsat 7 ETM+ sensor level 1 data\n'
                     '    > Landsat 5, Landsat 4 TM sensor level 1 data\n'
                     # '    > Landsat 4 TM sensor level 1 data\n'
                     '    > Landsat 4 and Landsat 5 MSS sensor level 1 data\n'
                     # '    > Landsat 4 MSS sensor level 1 data\n'
                     # '    > Landsat 3 MSS sensor level 1 data\n'
                     # '    > Landsat 2 MSS sensor level 1 data\n'
                     '    > Landsat 1 to 3 MSS sensor level 1 data\n\n'

                     'Note:\n'
                     '    > Select all the required bands along with the metadata file.\n'
                     '    > All the outputs are stored in the directory where raw data is stored\n'
                     '    > All the listed outputs are available for Landsat 8 data but some features are not available '
                      'for other data products due to unavailability of required band/s.\n\n'
                     'Please Wait !\n'
                     '    > Process once started takes some time to complete.\n'
                     '      When all the processes are complete you are good to go again.\n\n'
                     'Suggestions? Feedback? \n'
                     'Contact:\n'
                     'Prathamesh B\n'
                     'NITK, Surathkal, India.\n'
                     'email: prathamesh.barane@gmail.com\n')

        logger.append('>>>----------------------------------------------------------------------<<<\n'
                     ' ================  User Inputs ================'
                     '\n>>>----------------------------------------------------------------------<<<\n\n'
                      'Let\'s get started > Start with specifying the mode of selection\n')

    def Cb_nodata(self):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global no_data
        if self.dlg.cb_nodata.checkState() == 0:
            no_data = 'n'
            logger.append('Consider No Data Value pixels for calculation')
        else:
            no_data='y'
            logger.append("Don't consider No Data Value pixels for calculation")

        # Exporting the data
        self.dlg.label_no_data.setText(no_data)

    def CB_Status(self):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global ip_exclude_following

        if self.dlg.cb_clouds.checkState() == 0 and self.dlg.cb_cirrus.checkState() == 0 :
            logger.append('Deselected: Clouds and cirrus removal for Landsat8 data.')
            ip_exclude_following[0], ip_exclude_following[2] = 0, 0
        elif self.dlg.cb_clouds.checkState() == 2 and self.dlg.cb_cirrus.checkState() == 2 :
            logger.append('Selected: Clouds and cirrus removal for Landsat8 data.')
            ip_exclude_following[0], ip_exclude_following[2] = 1, 1
        elif self.dlg.cb_clouds.checkState() == 2 and self.dlg.cb_cirrus.checkState() == 0 :
            logger.append('Selected: Clouds removal for Landsat8 data.')
            ip_exclude_following[0], ip_exclude_following[2] = 0, 1
        elif self.dlg.cb_clouds.checkState() == 0 and self.dlg.cb_cirrus.checkState() == 2 :
            logger.append('Selected: Clouds and cirrus removal for Landsat8 data.')
            ip_exclude_following[0], ip_exclude_following[2] = 1, 1

        # Exporting the data
        self.dlg.label_ip_exclude_following.setText('!@#$'.join([str(x) for x in ip_exclude_following]))

    def CheckB_status(self, object, num, list):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global ip_toa_ra ,ip_toa_re, ip_extras, ip_exclude_following
        if object.checkState() == 0:
            status = 'Deselected'
            if list == 1:
                ip_toa_re[num]=0
            elif list == 2:
                ip_toa_ra[num]=0
            elif list == 3:
                ip_extras[num]=0
        else:
            status = 'Selected'
            if list == 1:
                ip_toa_re[num]=1
            elif list == 2:
                ip_toa_ra[num]=1
            elif list == 3:
                ip_extras[num]=1

        # Identifing band names
        if list in [1, 2]:
            if num == 0:
                band='Deep blue'
            elif num == 1:
                band='Blue'
            elif num == 2:
                band='Green'
            elif num == 3:
                band='Red'
            elif num == 4:
                band='Near IR'
            elif num == 5:
                band='Short Wave IR'
            elif num == 6:
                band='Thermal IR'
            elif num == 7:
                band='PAN'
            elif num == 8:
                band='Cirrus'

        # Output for logger terminal
        if list == 1:
            logger.append('%s: %s band top of atmosphere reflectance' %(status, band))
        elif list == 2:
            logger.append('%s: %s band top of atmosphere radiance' %(status, band))
        elif list == 3:
            if num == 0:
                logger.append('%s: True Color Composite' %status)
            elif num == 1:
                logger.append('%s: False Color Composite' %status)
            elif num == 2:
                logger.append('%s: Normalized Difference Vegetation Index' %status)
            elif num == 3:
                logger.append('%s: Normalized Difference Water Index' %status)
            elif num == 4:
                logger.append('%s: At-satellite brightness temperature' %status)
            elif num == 5:
                logger.append('%s: Land Surface Temperature' %status)

        # Exporting the data
        self.dlg.label_ip_toa_ra.setText('!@#$'.join([str(x) for x in ip_toa_ra]))
        self.dlg.label_ip_toa_re.setText('!@#$'.join([str(x) for x in ip_toa_re]))
        self.dlg.label_ip_extras.setText('!@#$'.join([str(x) for x in ip_extras]))

    def Cb_clip(self):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global clip_status
        if self.dlg.cb_clip.checkState() == 0:
            clip_status = '0'
            logger.append('\nDon\'t use Area of Interest shape file for clipping the raw data.\n')
        else:
            clip_status = '1'
            logger.append('\nUse Area of Interest shape file for clipping the raw data.\n')
        #Exporting the clip_status
        self.dlg.label_clip_status.setText(clip_status)

    def Pb_cancel(self):
        self.dlg.close()

    def Cob_mode(self):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global browse_selected_mode

        browse_selected_mode=self.dlg.cob_mode.currentIndex()
        if browse_selected_mode == 1:
            logger.append('\nUser selection mode:\n    Compressed file/s\n')
            logger.append('*Hint-\nBrowse and select the downloaded compressed file/s:\n'
                          '    > Use control and shift key to select multiple satellite data files in compressed file format.\n'
                          '    > Use this option for batch processing.\n'
                          '    > Supported file formats: \'tar\' and \'zip\'\n')
            self.dlg.pb_browse.setEnabled(True)
        elif browse_selected_mode == 2:
            logger.append('\nUser selection mode:\n    Extracted files\n')
            logger.append('*Hint-\nBrowse and select all the extracted files of a single satellite tile:\n'
                          '    > Make sure to select all the required files including metadata file.\n'
                          '    > Use this option for single tile process.\n'
                          '    > Supported file formats: \'tif\' and \'txt\'\n')
            self.dlg.pb_browse.setEnabled(True)
        elif browse_selected_mode == 3:
            logger.append('\nUser selection mode:\n    Folder containing the extracted data folder/s\n')
            logger.append('*Hint-\nBrowse and select the directory that contains all the data folder/s:\n'
                          '    > Every folder contains extracted files of a downloaded satellite data in compressed file format.\n'
                          '    > Use this option for batch processing.\n'
                          '    > User has to select a single folder.\n')
            self.dlg.pb_browse.setEnabled(True)
        else:
            self.dlg.pb_browse.setEnabled(False)

        self.dlg.pb_processing.setEnabled(False)

        # Exporting the data
        self.dlg.label_browse_selected_mode.setText(str(browse_selected_mode))

    def Pb_browse(self, browse_selected_mode):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global browse_raw, browse_selected_ext, browse, browse_selected
        if browse_selected_mode in [1]:
            browse_raw_obj=QtGui.QFileDialog.getOpenFileNames(self.dlg, "Select Compressed File/s", '', '*.tar.gz *.zip')
            if browse_raw_obj:
                browse_raw = []
                for path in browse_raw_obj:
                    browse_raw.append(str(path))
        elif browse_selected_mode in [2]:
            browse_raw_obj=QtGui.QFileDialog.getOpenFileNames(self.dlg, "Select Extracted Files", '', '*.TIF *.tif *.txt')
            if browse_raw_obj:
                browse_raw = []
                for path in browse_raw_obj:
                    browse_raw.append(str(path))
        elif browse_selected_mode in [3]:
            browse_raw_obj=str(QtGui.QFileDialog.getExistingDirectory(self.dlg, "Select Folder"))
            browse_raw = browse_raw_obj
            if browse_raw_obj:
                browse=browse_raw[:]
                browse_selected=[d for d in os.listdir(browse) if os.path.isdir(os.path.join(browse, d))]

        if browse_raw_obj:
            self.dlg.pb_processing.setEnabled(True)

            if browse_selected_mode in [1, 2]:
                browse_selected=browse_raw[:]
                browse_selected_ext=[None] * len(browse_selected)
                browse=os.path.split(browse_selected[0])[0]
                num_for=0
                for file in browse_selected:
                    browse_selected[num_for]=os.path.split(file)[1]
                    browse_selected_ext[num_for]="*" + os.path.splitext(os.path.splitext(file)[0])[1]+os.path.splitext(file)[1]
                    num_for+=1
                del num_for, file

            logger.append('\nCurrent working directory:')
            logger.append('    %s\n' %browse)
            logger.append('Selected files for processing:')
            for file in browse_selected:
                logger.append('    %s' %file)
                # Status bar msg

            if not browse_selected:
                logger.append('    ------ None ------')
            logger.append('')
            logger.append('>>> Please make sure:\n'
                         '         1. There is enough storage space in the current working directory\n'
                         '         2. There is no blank space in the current working directory address\n'
                         '\nStatus:')
            if ' ' in browse:
                logger.append('            :-( Your current working directory address consists blank space/s\n')
            else:
                logger.append('            :-) Your current working directory address does not consist blank space\n')

            logger.append('*Hint-\nSelect all the desired outputs:\n'
                          '    > Select AoI shape file if you want to clip the data to your polygon shape file(.shp)\n'
                          '    > For Landsat 8 data select if you want to exclude cloud and cirrus pixels for calculation\n'
                          '    > If you are intrested in some custom indices, write the name of the index and index band expression\n\n'
                          '    > Finally click the button "Start Processing" to start the band operations\n'
                          '    > Process once started takes some time to complete.\n'
                          '>>>----------------------------------------------------------------------<<<\n')

            # Exporting the data
            self.dlg.label_browse.setText(browse)
            self.dlg.label_browse_selected.setText('!@#$'.join(browse_selected))
            if browse_selected_mode in [1,2]:
                self.dlg.label_browse_selected_ext.setText('!@#$'.join(browse_selected_ext))

    def Pb_shape(self):
        # For terminal outputs
        logger = self.dlg.tb_terminal
        global shape_path
        shape_path_obj = QtGui.QFileDialog.getOpenFileNames(self.dlg, "Select area of interest shape file", '', '*.shp')
        if shape_path_obj:
            shape_path = []
            for path in shape_path_obj:
                shape_path.append(str(path))
            if shape_path:
                self.dlg.cb_clip.setEnabled(True)
                self.dlg.cb_clip.setChecked(True)
                self.dlg.label_clip_status.setText('1')
                shape_location = os.path.split(shape_path[0])[0]
                shape_file = os.path.split(shape_path[0])[1]
                logger.append('\nSelected Area of Interest shape file location:\n'
                             '    %s\n'
                             'Selected Area of Interest shape file:\n'
                             '    %s\n' %(shape_location, shape_file))
                 # Exporting the path selected
                self.dlg.label_shape_path.setText(shape_path[0])

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/RSGIS/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Derived Outputs'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&RS&GIS_V17.0'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        self.dlg.setFixedSize(self.dlg.size())
        # Run the dialog event loop
        # self.dlg.exec_()
