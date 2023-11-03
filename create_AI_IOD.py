import io
import re
import json
import torch
import base64
import datetime
import pandas as pd
import pydicom as pdc
from pydicom.uid import UID
from json import JSONDecoder
import matplotlib.pylab as plt
from pydicom.dataset import Dataset, FileDataset


class EncodeDecode():
    def __init__(self):
        self.ciao = "ciao"

    def encode(self, data):
        data_bytes = io.BytesIO()
        torch.save(data, data_bytes)
        data_base64 = base64.b64encode(data_bytes.getvalue()).decode('utf-8')
        return data_base64

    def decode(self, data):
        data_bytes = base64.b64decode(data.encode('utf-8'))
        data_bytesio = io.BytesIO(data_bytes)
        return data_bytesio 
        

#/ IOD Generator
class CreateGenericIOD(EncodeDecode):
    def __init__(self, model_json, weights):
        super(CreateGenericIOD, self).__init__()
        self.model = model_json
        self.weights = weights
        self.dict_tag = {
            'SOP Class UID': ['00080016', 'UI'],
            'SOP Instance UID': ['00080018', 'UI'],
            'Modality': ['00080060', 'CS'],
         "Referring Physician's Name": ['00080090', 'PN'],
         "Patient's Name": ['00100010', 'PN'],
         'Patient ID': ['00100020', 'LO'],
         "Patient's Birth Date": ['00100030', 'DA'],
         "Patient's Sex": ['00100040', 'CS'],
         'Series Instance UID': ['0020000E', 'UI'], 
         'Patient Orientation': ['00200020', 'CS'],
         'Samples per Pixel': ['00280002', 'US'],
         'Photometric Interpretation': ['00280004', 'CS'],
         'Planar Configuration': ['00280006', 'US'],
         'Row': ['00280010', 'US'],
         'Columns': ['00280011', 'US'],
         'Body Part Examinated': ['00180015', 'CS'],
         'Study Instance UID': ['0020000D', 'UI'],

           }
        
    def generateIOD(self, nn_type:str, photo_int:str, net_info:dict, dcm_name:str=None):
        #! add new tag in pydicom library
        pdc.datadict.add_private_dict_entry(private_creator="DNNArchitecture", tag=0x00170001, VR="UT", description="jsonDNN")
        pdc.datadict.add_private_dict_entry(private_creator="DNNweights", tag=0x00170002, VR="UT", description="DNNweights")
        pdc.datadict.add_private_dict_entry(private_creator="DNNName", tag=0x00170003, VR="PN", description="name")
        pdc.datadict.add_private_dict_entry(private_creator="DNNUID", tag=0x00170004, VR="UI", description="uid")


        dt = datetime.datetime.now()
        if dcm_name == None:
            dcm_name = f"net_{dt}.dcm"
        #/ Set creation date/time
        self.dict_dcm = {}
        #/ iod info
        #! generic uid
        generic_uid = pdc.uid.generate_uid()
        sop_uid = generic_uid
        sop_insta_uid = generic_uid 
        modality = nn_type
        meds_name = ""
        patient_name = ""
        patient_id = ""
        patient_birth_date = ""
        patient_sex = ""
        series_insta_uid = generic_uid
        patient_orient = "A"
        sample_pixel = str(3) if photo_int == "RGB" else str(1)
        photo_interpr = photo_int
        planar_conf = "0"
        rows = str(self.model['input_shape']['input_shape1'])
        columns = str(self.model['input_shape']['input_shape2'])
        body_parts = str(netInfo["body_parts"])
        study_uid = UID(generic_uid)
        value_list = [
            sop_uid,
            sop_insta_uid, modality,  
            meds_name, patient_name, 
            patient_id, patient_birth_date, patient_sex,
            series_insta_uid,
            patient_orient, sample_pixel,
            photo_interpr, planar_conf, rows, columns, body_parts, study_uid
            ]

        for idx, item in enumerate(zip(self.dict_tag.values(), value_list)):
            if len(item[1]) > 0:
                self.dict_dcm[f'{item[0][0]}'] = {'vr': item[0][1], 'Value': [item[1]]}
            else:
                self.dict_dcm[f'{item[0][0]}'] = {'vr': item[0][1]}


        ds = Dataset.from_json(self.dict_dcm)
        ds = FileDataset(None, dataset=ds)
        #! add private tag 
        #! DNN module
        ds.add_new(["0x0017", "0x0016"], "UT", str(self.model))
        ds.add_new(["0x0017", "0x0018"], "UT", self.encode(data=self.weights))
        ds.add_new(["0x0017", "0x0020"], "ST", str(net_info["net_name"]))
        ds.add_new(["0x0017", "0x0022"], "UI", UID(generic_uid))
        print(ds)
        #/ aggiungo i file meta 
        ds.file_meta.MediaStorageSOPClassUID = UID("1.2.840.10008.5.1.4.1.1.66")
        ds.file_meta.MediaStorageSOPInstanceUID = UID(generic_uid)
        ds.file_meta.TransferSyntaxUID = pdc.uid.ImplicitVRLittleEndian
        #/ aggiungo rete e pesi
        #/ salvo il dcm 
        pdc.filewriter.dcmwrite(f"{dcm_name}.dcm", ds)
        print("Salvataggio completato")


if "name" == "__main__":
    netInfo = {
        'net_description': 'Unet 2D with 3 channels trained on MRI Brain Head',
        'body_parts': 'HEAD',
        'net_name': "unet_mri"
    }
    data_parameter = json.load("architecture.json")
    weights_MRI = torch.load("weights.pth")
    gen_iod = CreateGenericIOD(model_json=data_parameter, weights=weights_MRI)
    gen_iod.generateIOD(
        nn_type="MR", photo_int="MONOCHROME2",
        dim_img=(224, 224), netInfo=netInfo,
        dcm_name="IODeepMRI_head"
        )
