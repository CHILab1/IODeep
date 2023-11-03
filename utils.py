from PyQt5.QtWidgets import QGridLayout, QPushButton, QSlider, QLabel, QFrame, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QWheelEvent, QImage
from PyQt5.QtGui import QPolygon
from pyorthanc import Orthanc
from functools import partial
from PyQt5 import QtWidgets
import simple_orthanc
import numpy as np
import requests
import pydicom
import asyncio
import json
import vtk
import time
import sys
sys.path.append("C:\\Users\\lucas\\Documents\\DMC_code_paper")
from DCM_reader import DCMFinderNN

class exServer():

    def __init__(self, dcm):
        self.server_info= {'host':'127.0.0.1', 'port':8042, 'username':'alice', 'password':'alice'}
        self.dcm= dcm

    def orthanc_solution(self, UID):
        list_tag_name = [
            "Modality", "AnatomicRegionSequenceAttribute", "StudyDescription",
            "SamplesPerPixel", "Rows","Columns", "PhotometricInterpretation", "PixelRepresentation"
            ]
        # list_tag_name = ["SpecificCharacterSet", "ImageType", "InstanceCreationDate", "InstanceCreationTime", "InstanceCreatorUID", "SOPClassUID", "SOPInstanceUID", "StudyDate", "SeriesDate", "StudyTime", "SeriesTime", "AccessionNumber", "Modality", "Manufacturer", "InstitutionName", "ReferringPhysicianName", "StudyDescription", "SeriesDescription", "ManufacturerModelName", "PatientName", "PatientID", "PatientBirthDate", "PatientSex", "PatientWeight", "ScanningSequence", "SequenceVariant", "ScanOptions", "MRAcquisitionType", "SliceThickness", "RepetitionTime", "EchoTime", "InversionTime", "NumberOfAverages", "ImagingFrequency", "ImagedNucleus", "EchoNumbers", "MagneticFieldStrength", "SpacingBetweenSlices", "NumberOfPhaseEncodingSteps", "EchoTrainLength", "PercentSampling", "PercentPhaseFieldOfView", "DeviceSerialNumber", "SoftwareVersions", "ProtocolName", "LowRRValue", "HighRRValue", "IntervalsAcquired", "IntervalsRejected", "HeartRate", "ReceiveCoilName", "TransmitCoilName", "InPlanePhaseEncodingDirection", "FlipAngle", "PatientPosition", "StudyInstanceUID", "SeriesInstanceUID", "StudyID", "SeriesNumber", "AcquisitionNumber", "InstanceNumber", "ImagePositionPatient", "ImageOrientationPatient", "FrameOfReferenceUID", "PositionReferenceIndicator", "ImageComments", "SamplesPerPixel", "PhotometricInterpretation", "Rows", "Columns", "PixelSpacing", "BitsAllocated", "BitsStored", "HighBit", "PixelRepresentation", "WindowCenter", "WindowWidth", "PixelData", "DataSetTrailingPadding"]
        dictio_tag = {}
        info_list = []
        dcm_retr= self.dcm
        pixel_data = dcm_retr.get_array()
        for item in list_tag_name:
            try:
                dictio_tag[item] = dcm_retr.get_dicom_tag(item, unique=False)[0]
            except:
                dictio_tag[item] = None
        data_shape = pixel_data.shape[1:] if len(pixel_data.shape) > 3 else pixel_data.shape
        list_to_check = ["Rows", "Columns", "SamplesPerPixel", ] #, "PixelRepresentation"
        for idx, keys in enumerate(list_to_check):
            if dictio_tag[keys] is None:
                dictio_tag[keys] = data_shape[idx]
        pixel_data= np.array(pixel_data, dtype=np.uint8)
        pixel_data= np.squeeze(pixel_data)
        finder = DCMFinderNN(ds_tag=dictio_tag)
        roi = finder.__execute__(pixel_data)
        return roi

class Spinner():
    def __init__(self):
        self.loading_popup = QMessageBox()
        self.loading_popup.resize(500,500)
        self.loading_popup.setIcon(QMessageBox.Information)
        self.loading_popup.setText("Loading...")
        self.loading_popup.setWindowTitle("Please wait")
        self.loading_popup.setStandardButtons(QMessageBox.NoButton)

    def show_spinner(self):
        self.loading_popup.show()

    def dismiss_spinner(self):
        self.loading_popup.hide()

    def alert_message(self, title, message, success=True):
        if success:
            # QMessageBox.information(None, title=title, message=message)
            self.loading_popup.information(None, title, message)
        else:
            QMessageBox.critical(None, title=title, text=message)
            # QMessageBox.critical(None, title=title, message=message)

class Lista(QDialog):
    return_value = pyqtSignal(tuple)

    def __init__(self,tipologia="Study", StudyID=None):
        super().__init__()
        orthanc = Orthanc('http://127.0.0.1:8042', username='alice', password='alice')
        self.lista= []
        self.name=""
        if tipologia == "Study":
            for instance in orthanc.get_studies():
                patient_info = orthanc.get_studies_id(instance)
                patient_name = patient_info['PatientMainDicomTags']['PatientName']
                StudyInstanceUID = patient_info['MainDicomTags']['StudyInstanceUID']
                self.lista.append((patient_name, patient_info))
        else:
            for instance in orthanc.get_studies_id_series(StudyID):
                print(instance)
                patient_info = orthanc.get_series_id(instance['ID'])
                if patient_info["MainDicomTags"]["SeriesInstanceUID"] is not None:
                    number = patient_info["MainDicomTags"]["SeriesInstanceUID"]
                else:
                    number = patient_info["MainDicomTags"]["SeriesNumber"]
                self.lista.append((number, patient_info))
        self.layout = QVBoxLayout()
        self.resize(600,400)
        self.setLayout(self.layout)
        for item in self.lista:
            label = QPushButton(item[0])
            self.layout.addWidget(label)
            label.clicked.connect(partial(self.clicked,item))

    def clicked(self, label):
        self.return_value.emit(label)

    def get_name(self, name):
        self.name=name

class ConfirmBox(QDialog):
    return_value = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        accept = QPushButton('Accept')
        not_accept = QPushButton('Not Accept')
        self.layout.addWidget(accept)
        self.layout.addWidget(not_accept)
        self.values= -1
        accept.clicked.connect(partial(self.clicked,True))
        not_accept.clicked.connect(partial(self.clicked,False))

    def setValues(self, value):
        self.values= value

    def clicked(self, label):
        if label:
            self.return_value.emit((-1, self.values))
        else:
            self.return_value.emit((self.values, self.values))

class ShowInfo(QFrame):
    def __init__(self, info):
        super().__init__()
        self.info= info
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        layout = QVBoxLayout()
        # Create a QLabel with some content
        for key, value in self.info.items():
            label = QLabel(f"{key}: {value}")
            # label.adjustSize()
            layout.addWidget(label)
        self.setLayout(layout)
        self.setWindowTitle('Adapt Size to Content')

class DICOMViewer(QtWidgets.QWidget):

    def __init__(self, patient_info, studInfo):
        super().__init__()
        self.dcm= None
        self.aspectRatio=5
        print(patient_info, studInfo)
        self.StudyInstanceUID = patient_info['MainDicomTags']['StudyInstanceUID']
        # self.StudyInstanceUID = patient_info['MainDicomTags']['SeriesInstanceUID']
        self.image= None
        self.image_label = QLabel()
        self.index_label = QLabel()
        self.current_index=0
        self.total_index=0
        asyncio.run(self.load_dicom_image())
        self.setWindowTitle("DICOM Viewer")
        sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        self.resize(round(sizeObject.width()/1.10), round(sizeObject.height()/1.10))
        self.patient_info= patient_info
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.roi_button = QPushButton("AI ROI")
        self.next = QPushButton(">")
        self.prev = QPushButton("<")
        self.showDataP= ShowInfo(self.patient_info['PatientMainDicomTags'])
        self.showDataS= ShowInfo(self.patient_info['MainDicomTags'])
        self.showDataP.setMinimumHeight(64)
        self.showDataP.setMinimumWidth(64)
        self.showDataS.setMinimumHeight(64)
        self.showDataS.setMinimumWidth(64)
        self.exServer= exServer(self.dcm)
        self.index_label.setText(f"Current Frame:{self.getCurrentIndex()+1}/ Total:{1 if self.total_index==0 else self.total_index}")
        self.rois = []
        self.current_roi = []
        self.drawing_roi = False
        self.zoom_level = 1
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(10)
        self.contrast_slider.setValue(0)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(1000)
        self.zoom_slider.setValue(100)
        self.layout = QGridLayout()
        self.layout.setColumnStretch(2, 1)
        self.button_layout= QHBoxLayout()
        self.cinerate_layout= QHBoxLayout()
        self.contrast_slider.valueChanged.connect(self.update_contrast)
        self.roi_button.clicked.connect(self.main_toggle_roi)
        self.prev.clicked.connect(partial(self.moveTo, 'prev'))
        self.next.clicked.connect(partial(self.moveTo, 'next'))
        self.spinner = Spinner()
        self.image_label.setMinimumHeight(64)
        self.image_label.setMinimumWidth(64)
        self.confirmBox= ConfirmBox()
        self.confirmBox.return_value.connect(self.handle_returned_value)
        #layout section
        self.layout.addWidget(self.showDataP, 0, 0,1,1)
        self.layout.addWidget(self.showDataS, 0, 1,1,1, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.image_label,2, 0, 1, 2,alignment=Qt.AlignCenter)
        self.auto_play_button = QPushButton("Auto Play")
        self.auto_play_button.clicked.connect(self.on_auto_play_button_clicked)
        # Set up the timer for auto-playing
        self.auto_play_timer = QTimer()
        self.auto_play_timer.timeout.connect(self.on_auto_play_timeout)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop_button_clicked)
        self.stop_button.setEnabled(False)
        #! BUTTONS LAYOUT
        # self.button_layout.addWidget(self.contrast_slider)
        self.button_layout.setAlignment(Qt.AlignCenter)
        self.button_layout.setContentsMargins(750,0,300,0)
        self.button_layout.addWidget(self.prev)
        self.button_layout.addWidget(self.auto_play_button)
        self.button_layout.addWidget(self.next)
        self.button_layout.addWidget(self.confirmBox)
        self.button_layout.addWidget(self.roi_button)
        self.layout.addLayout(self.button_layout, 3,0)
        self.layout.addLayout(self.cinerate_layout, 1,0)
        #! CINERATE LAYOUT
        self.cinerate_layout.addWidget(self.index_label)
        self.setLayout(self.layout)
        self.confirmBox.hide()
        self.show()

    def on_auto_play_button_clicked(self):
        if not self.auto_play_timer.isActive():
            # Start auto-playing
            self.auto_play_button.setText("Pause")
            self.stop_button.setEnabled(True)
            self.auto_play_timer.start(400)  # Set the auto-play interval (in milliseconds)
        else:
            # Pause auto-playing
            self.auto_play_button.setText("Auto Play")
            self.auto_play_timer.stop()

    def on_stop_button_clicked(self):
        # Stop auto-playing
        self.auto_play_button.setText("Auto Play")
        self.stop_button.setEnabled(False)
        self.auto_play_timer.stop()

    def on_auto_play_timeout(self):
        self.moveTo('next')


    def getCurrentIndex(self):
        return self.current_index

    # def play_slides(self):
    #     #print(self.image.shape)
    #     for i in range(self.image.shape[0]-1):
    #         self.moveTo('next')
    #         time.sleep(0.4)

    async def play_slides(self):
        for i in range(self.image.shape[0] - 1):
            self.moveTo('next')
            await asyncio.sleep(0.4)

    def moveTo(self, action):
        #print(self.current_index)
        if action == 'next' and self.current_index < self.total_index:
            self.current_index +=1
            asyncio.run(self.load_dicom_image(self.current_index))
        elif action == 'prev' and self.current_index >0:
            self.current_index -=1
            asyncio.run(self.load_dicom_image(self.current_index-1))
        else:
            pass


    def handle_returned_value(self, value):
        self.confirmBox.hide()
        values= int(value[0])
        value_idx = int(value[1])
        if values != -1:
            del self.rois[values]
        # lunghezza rimasta > 0 e diverso dall'ultimo
        if len(list(self.rois.keys())[value_idx:-1]) > 0 and value_idx != (len(list(self.rois.keys()))-1):
            self.toggle_roi(value_idx+1)
        elif value == -1 and len(list(self.rois.keys())[value_idx:-1]) > 0 and value_idx != len(list(self.rois.keys()) -1):
            self.toggle_roi(value_idx+1)
        else:
            self.final_toggle_roi()


    def update_contrast(self, value):
        # Aggiorna il contrasto dell'immagine
        pass


    def main_toggle_roi(self):
        # Example usage
        # url = "http://localhost:7250/"
        self.spinner.show_spinner()
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.call_api(url))
        # asyncio.run(self.call_api(url))
        self.rois = self.exServer.orthanc_solution(self.patient_info)
        if len(self.rois.keys()) > 0:
            self.spinner.dismiss_spinner()
            self.spinner.alert_message(title="Task Complete", message="The task has been completed.")
            self.toggle_roi(0)
        else:
            self.spinner.dismiss_spinner()
            self.spinner.alert_message(title="Error", message=f"API request failed with status code:{response.status_code}")



    def toggle_roi(self,idx):
        points = []
        colors= [Qt.red, Qt.blue, Qt.yellow]
        self.rois_elaborate = self.rois
        # for idx, roi in enumerate(list(self.rois.keys())[:-1]):
        painter = QPainter(self.pixmap_original)
        painter.setPen(QPen(colors[int(idx)], 1))
        for r in self.rois[idx]:
            r = r[:2]
            if len(r) > 1:
                points.append(QPoint(int(r[0]*self.aspectRatio), int(r[1]*self.aspectRatio)))
                fill_color = QColor(255, 0, 0)  # Rosso
                brush = painter.brush()
                brush.setColor(fill_color)
                # Imposta il pennello di riempimento per il poligono
                painter.setBrush(brush)
                polygon = QPolygon(points)
                painter.drawPolyline(polygon)
            self.confirmBox.setValues(idx)
            self.confirmBox.show()
        painter.end()
        # if self.drawing_roi:
        #     if len(self.current_roi) > 1:
        #         for i in range(len(self.current_roi) - 1):
        #             painter.drawLine(self.current_roi[i], self.current_roi[i+1])
        # self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setPixmap(self.pixmap_original)
        self.image_label.adjustSize()


    def final_toggle_roi(self):
        points = []
        colors= Qt.green
        for roi2 in list(self.rois.keys())[:-1]:
                painter = QPainter(self.pixmap_original)
                painter.setPen(QPen(colors, 1))
                for r2 in self.rois[roi2]:
                    self.confirmBox.hide()
                    r2 = r2[:2]
                    if len(r2) > 1:
                        points.append(QPoint(int(r2[0]*self.aspectRatio), int(r2[1]*self.aspectRatio)))
                        fill_color = QColor(255, 0, 0)  # Rosso
                        brush = painter.brush()
                        brush.setColor(fill_color)
                        # Imposta il pennello di riempimento per il poligono
                        painter.setBrush(brush)
                        polygon = QPolygon(points)
                        painter.drawPolyline(polygon)
                painter.end()
        self.image_label.setPixmap(self.pixmap_original)
        self.image_label.adjustSize()

    def update_contrast(self, value):
        self.contrast_values = value
        image = self.pixmap_original.toImage()
        image.convertToFormat(QImage.Format_Grayscale8)
        for y in range(image.height()):
            for x in range(image.width()):
                intensity = image.pixelColor(x, y).value()
                new_intensity = max(0, min(int(intensity * self.contrast_values), 255))
                new_color = QColor()
                new_color.setRgb(new_intensity, new_intensity, new_intensity)
                image.setPixelColor(QPoint(x, y), QColor(new_color))
        image.convertToFormat(QImage.Format_Grayscale8)
        self.pixmap_contrast = QPixmap.fromImage(image)
        self.update_image(contrast=True)

    def update_image(self, contrast=False):
        painter = QPainter(self.pixmap_original)
        painter.setPen(QPen(Qt.red, 1))
        if contrast:
            self.image_label.setPixmap(self.pixmap_contrast)
            self.image_label.adjustSize()
        else:
            self.image_label.setPixmap(self.pixmap_original)
            self.image_label.adjustSize()


    async def load_dicom_image(self, index=0):
        if self.image is None:
            orthanc = simple_orthanc.Orthanc(host='127.0.0.1', port=8042, username='alice', password='alice')
            ds = orthanc.select(StudyInstanceUID=self.StudyInstanceUID)
            self.dcm=ds
            pixel_array = ds.get_array()
            pixel_array = np.array(pixel_array, np.uint8).squeeze()
            self.image= pixel_array
            if len(self.image.shape) > 2:
                pixel_array= self.image[index]
                self.total_index= pixel_array.shape[0]
            else:
                pixel_array= self.image
                self.total_index= 1

            #print(f"IMage NONE:{self.image.shape}")
        else:
            #print(f"IMage not NONE:{self.image.shape}")
            if len(self.image.shape) > 2:
                pixel_array= self.image[index]
            else:
                pixel_array= self.image

        #! Controllo quante dimensioni ha l'immagine
        if len(pixel_array.shape) == 2:
            pixel_array = QImage(pixel_array, pixel_array.shape[1], pixel_array.shape[0], QImage.Format_Grayscale8)
        elif len(pixel_array.shape) == 3:
            pixel_array = QImage(bytes(pixel_array), pixel_array.shape[0], pixel_array.shape[1], QImage.Format_Indexed8)
        else:
            pixel_array = QImage(pixel_array, pixel_array.shape[1], pixel_array.shape[0], QImage.Format_RGB16)

        self.pixmap_original = QPixmap.fromImage(pixel_array)
        self.pixmap_original=  self.pixmap_original.scaled(pixel_array.width()*self.aspectRatio, pixel_array.height()*self.aspectRatio, aspectRatioMode=self.aspectRatio)
        self.image_label.setPixmap(self.pixmap_original)
        self.index_label.setText(f"Current Frame:{self.getCurrentIndex()+1}/ Total:{1 if self.total_index==0 else self.total_index+1}")


    async def call_api(self, url):
      formData = { 'info': self.StudyInstanceUID }
      self.contrast_slider.setValue(0)
      formData = json.dumps(formData, separators=(',', ':'))
      loop = asyncio.get_event_loop()
      future1 = loop.run_in_executor(None, requests.post, url, formData)
      response = await future1
      print(response.json)
      if response.status_code == 200:
          # Successful API call
          self.rois = dict(response.json())
          self.spinner.dismiss_spinner()
          self.spinner.alert_message(title="Task Complete", message="The task has been completed.")
          # Process the data as needed
      else:
          # Error in API call
          self.spinner.dismiss_spinner()
          self.spinner.alert_message(title="Error", message=f"API request failed with status code:{response.status_code}")




def imageCheck(self):

    tags_to_check=['NumberOfFrames', 'PhotometricInterpretation', 'Rows', 'Columns', 'PhotometricInterpretation']


    for tag in tags_to_check:
        if self.dcm[tag]:
            print(self.dcm[tag])
        else:
            print(f"Il DICOM non contiene: {tag}")
