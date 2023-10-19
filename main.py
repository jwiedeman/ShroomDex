

from roboflow import Roboflow
rf = Roboflow(api_key="2LWmJCnLVplwB4tyX71r")
project = rf.workspace("jacob-solawetz").project("na-mushrooms")
dataset = project.version(2).download("yolov5")