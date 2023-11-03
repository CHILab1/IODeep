import io
import re
import sys
import json
import cv2
import torch
import base64
import pydicom
import numpy as np
import simple_orthanc
import matplotlib.pyplot as plt
#! importare il wrapper del parser 
sys.path.append("C:\\Users\\esorc\\Desktop\\Unipa\\Project_Info\\Dicom\\Draft paper\\Code\\DMC_code_paper")
from  Pytorch_Framework.model_create.JsonToPytorch import PytorchCreator
from torchvision.transforms.functional import to_tensor


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


class DCMFinderNN(EncodeDecode):
    def __init__(self, ds_tag):
        super(DCMFinderNN, self).__init__()
        self.tag_type = {
            "Modality": "00080060",
            "BodyPartExaminated" : "00082218",
            "StudyDescription" : "00081030"
            }
        self.tag_image = {
            "SamplePerPixel" : "00280002",
            "Rows": "00280010",
            "Cols": "00280011",
            "PhotometricInterpretation": "00280004",
            "PixelRepresentation": "00280103"
            }

        self.tag_search = {
            "Modality": "00080060",
            "SamplesPerPixel" : "00280002",
            "BodyPartExaminated" : "00082218",
            "StudyDescription" : "00081030"
        }

        self.dictio_anatomy = {'SNOMED Code Value ': {0: 'T-D4000', 1: 'R-FAB57', 2: 'T-59490', 3: 'T-A0100', 4: 'T-04000', 5: 'T-26000', 6: 'T-A6000', 7: 'T-45510', 8: 'T-11501', 9: 'T-D00F7', 10: 'T-D3000', 11: 'R-FAB55', 12: 'R-FAB56', 13: 'T-59300', 14: 'T-58200', 15: 'T-59600', 16: 'T-71000', 17: 'T-D4200', 18: 'T-DD163', 19: 'T-63000', 20: 'T-48820', 21: 'T-D2600', 22: 'T-46420', 23: 'T-48720', 24: 'T-D4240', 25: 'T-D1400', 26: 'T-71000', 27: 'T-59000', 28: 'T-62000', 29: 'T-04003', 30: 'T-04005', 31: 'T-28000', 32: 'R-FAB52', 33: 'R-FAB53', 34: 'R-FAB54', 35: 'T-65000', 36: 'T-65010', 37: 'T-65600', 38: 'T-D3136', 39: 'T-58000', 40: 'T-57000', 41: 'T-D3000'}, 'Anatomy_area': {0: 'Abdomen', 1: 'Abdomen and Pelvis', 2: 'Anus, rectum and sigmoid colon', 3: 'Head', 4: 'Breast', 5: 'Bronchus', 6: 'Cerebellum', 7: 'Cerebral artery', 8: 'Cervical spine', 9: 'Cervico-thoracic spine', 10: 'Chest', 11: 'Chest and Abdomen', 12: 'Chest, Abdomen and Pelvis', 13: 'Colon', 14: 'Duodenum', 15: 'Endo-rectal', 16: 'Endo-renal', 17: 'Epigastric region', 18: 'Esophagus, stomach and duodenum', 19: 'Gallbladder', 20: 'Gastric vein', 21: 'Gluteal region', 22: 'Hepatic artery', 23: 'Hepatic vein', 24: 'Hypogastric region', 25: 'Intracranial', 26: 'Kidney', 27: 'Large intestine', 28: 'Liver', 29: 'Lower inner quadrant of breast', 30: 'Lower outer quadrant of breast', 31: 'Lung', 32: 'Neck and Chest', 33: 'Neck, Chest and Abdomen', 34: 'Neck, Chest, Abdomen and Pelvis', 35: 'Pancreas', 36: 'Pancreatic duct', 37: 'Pancreatic duct and bile duct systems', 38: 'Parasternal', 39: 'Small intestine', 40: 'Stomach', 41: 'Thorax', 42: 'Brain'}, 'Macro_group': {0: 'Abdomen', 1: 'Abdomen', 2: 'Abdomen', 3: 'Head', 4: 'Chest', 5: 'Chest', 6: 'Head', 7: 'Head', 8: 'Head', 9: 'Head', 10: 'Chest', 11: 'Abdomen', 12: 'Abdomen', 13: 'Abdomen', 14: 'Abdomen', 15: 'Abdomen', 16: 'Abdomen', 17: 'Abdomen', 18: 'Abdomen', 19: 'Abdomen', 20: 'Abdomen', 21: 'Abdomen', 22: 'Abdomen', 23: 'Abdomen', 24: 'Abdomen', 25: 'Head', 26: 'Abdomen', 27: 'Abdomen', 28: 'Abdomen', 29: 'Chest', 30: 'Chest', 31: 'Chest', 32: 'Chest', 33: 'Chest', 34: 'Abdomen', 35: 'Abdomen', 36: 'Abdomen', 37: 'Abdomen', 38: 'Chest', 39: 'Abdomen', 40: 'Abdomen', 41: 'Chest', 42:'Head'}}
        self.net_library = {
            # "1.2.826.0.1.3680043.8.498.77651929035869169582649803417132562445": ["MRI", "3", "Head"],
            "1.2.826.0.1.3680043.8.498.77651929035869169582649803417132562445": ["MRI", "1", "Head"],
            "1.2.826.0.1.3680043.8.498.11486421364957243988420552297274333504": ["MRI", "1", "Abdomen"]
        }
        self.ds_json = ds_tag

    def checkDatatype(self):
        self.dataType = []
        for i, tag in enumerate(self.tag_search.keys()):
            tag_value = self.ds_json[tag]
            if i == 0:
                self.dataType.append(tag_value)
            if i == 1:
                self.dataType.append(tag_value)
            if i == 2:
                if tag_value is None:
                    self.dataType.append(str(-1))
                else:
                    self.dataType.append(tag_value)
            if i == 3 and self.dataType[-1] == str(-1):
                print(tag_value)
                string = tag_value.split(" ")
                for word in string:
                    print(word.capitalize())
                    for item in self.dictio_anatomy["Anatomy_area"].items():
                        if item[1] == word.capitalize():
                            self.dataType.append(self.dictio_anatomy["Macro_group"][item[0]])
                            break

    def prepareImage(self, pixel_data, architecture_json):
        image_info = (self.ds_json['SamplesPerPixel'], self.ds_json['Rows'], self.ds_json['Columns'])
        net_input = (architecture_json["input_shape"]["input_shape0"],architecture_json["input_shape"]["input_shape1"],architecture_json["input_shape"]["input_shape2"])
        if self.ds_json['PhotometricInterpretation'] != "MONOCHROME2":
            image = np.invert(image)
        if self.ds_json['SamplesPerPixel'] != 1:
            image = np.array(image, type=np.float32).astype(np.uint8)
        if image_info != net_input:
            image_shape = [image_info[idx] if image_info[idx] == net_input[idx] else net_input[idx] for idx in range(len(image_info))]
            image = cv2.resize(pixel_data, tuple(el for el in image_shape[1:]), interpolation = cv2.INTER_LANCZOS4)
            if image_info[0] != net_input[0] :
                if net_input[0] == 1:
                    image= image[:,:,1]
                    image= torch.tensor(image)
                    image = image.unsqueeze(0).unsqueeze(0)
                else:
                    image= cv2.merge([image,image,image])
                    image = to_tensor(image)
                    image = image.unsqueeze(0)
        return image

    def matchNN(self):
        print(self.dataType)
        for item in self.net_library.items():
            control = 0
            if len(self.dataType) == 4:
                i= self.dataType.index(str(-1))
                if i != 2:
                    exit()
                else:
                    self.dataType.pop(2)
            for idx, compare_data in enumerate(zip(item[1], self.dataType)):
                if idx== 0:
                    a= re.match(f'^(MR)', compare_data[0])
                    b= re.match(f'^(MR)', compare_data[1])
                    if a and b:
                        control += 1
                if str(compare_data[0]) == str(compare_data[1]) and idx != 0:
                    control += 1
            if control == 3:
                sop_to_load = item[0]
                return sop_to_load
            else:
                sop_to_load = None
        return sop_to_load

    def loadDCMNet(self):
        sop_uid = self.matchNN()
        if sop_uid is not None:
            orthanc = simple_orthanc.Orthanc(host='127.0.0.1',
                                            port=8042,
                                            username='alice',
                                            password='alice')
            self.obj_net = orthanc.select(SOPInstanceUID=sop_uid)
            arch ="TextValue"
            weights= "LocalNamespaceEntityID"
            a_net= self.obj_net.get_dicom_tag(arch)[0]
            w_net= self.obj_net.get_dicom_tag(weights)[0]
            weights = self.decode(data=w_net)
            architecture_json = self.decode(data=a_net)
            architecture_json= torch.load(architecture_json, map_location=torch.device('cpu'))
            model = PytorchCreator(parameterList=architecture_json)
            weights_loaded = torch.load(weights, map_location=torch.device('cpu'))
            model.load_state_dict(weights_loaded)
        else:
            model = None
            architecture_json=None
        return model, architecture_json

    def predict(self, model, image):
        model.eval()
        with torch.no_grad():
            pred = model(image)
        return pred

    def loadAndPredict(self):
        net, architecture_json = self.loadDCMNet()
        if net is not None:
            #! prepare image
            image = self.prepareImage(pixel_data=self.pixel_data, architecture_json=architecture_json) # dim=, type=, image=
            prediction = self.predict(model=net, image=image)
            prediction_message = {"message": prediction}
            return prediction_message
        else:
            prediction_message = {"message":"There are no suitable neural networks"}
            return prediction_message

    def __execute__(self, pixel_data):
        self.checkDatatype()
        model, architecture_json = self.loadDCMNet()
        if model is not None or architecture_json is not None:
            image = self.prepareImage(pixel_data, architecture_json)
            preds = self.predict(model, image)
            preds = torch.squeeze(preds)
            preds = preds.detach().cpu().numpy()
            coords= self.define_contours(preds)
            return coords
        else:
            print('error')

    def define_contours(self, image):

        if len(image.shape) > 2:
            image= cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = np.array(image, dtype=np.uint8)
        _,thresh = cv2.threshold(image, 127, 255 , 0)
        contours, _= cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        lista={}
        for idx, c in enumerate(contours):
            a= np.array(c)
            b= np.ones(shape=(a.shape[0],1,1))
            d= np.concatenate([a,b], axis=-1).squeeze()
            lista[idx]=d
            cv2.drawContours(thresh, c, -1, (0, 0, 0), 1)
        cv2.imwrite('C:/Users/lucas/Documents/image.png', thresh)
        f = open(f"C:/Users/lucas/Documents/log.txt", 'w')
        f.write(f'dict:{lista}')
        f.close()
        return lista
