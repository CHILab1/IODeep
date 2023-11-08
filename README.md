# IODeep

This repository contains the source code for using the IODeep module for integration within the DICOM Artificial Intelligence standard. 
The main file is 'viewer_python.py' which runs the client viewer that implements the following functionality:
- Selection of a Study 
- Selecting a Series within a Studio
- Instance image display 
- Automatic generation of the Region Of Interest (ROI) predicted by the AI algorithm, selected through a matching algorithm that queries the PACS server, retrieving the IODeep compatible with the image. 
<br>
The service has been developed using the Orthanc PACS server, the container of which can be downloaded at the following link: https://hub.docker.com/r/jodogne/orthanc

For the correct functionality of the module, it is necessary to download the parser developed by the authors in order to generate the neural architecture. The parser executable can be downloaded from the following link: https://cloud.unipa.it/index.php/s/XXG9fntDVrdkJvR
