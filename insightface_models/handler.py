# encoding:utf-8
from .common import Face
from .arcface_onnx import ArcFaceONNX
from .scrfd import SCRFD

class Handler:
    def __init__(self):
        self.detector = SCRFD()
        self.arcface = ArcFaceONNX()

    def prepare(self, ctx_id):
        self.detector.prepare(ctx_id=ctx_id)
        self.arcface.prepare(ctx_id=ctx_id)

    def detect(self, image, input_size=(160, 160)):
        if image is None:
            return None
        bbox, kps = self.detector.detect(image,0.5,input_size=input_size)
        face = Face(bbox=bbox,kps=kps)
        return face

    def get_embedding(self,image,face):
        if face.kps is None:
            return None
        self.arcface.get(image, face)
        return face.embedding

    def get(self, image, det_size=(160, 160)):
        if image is None:
            return None
        face = self.detect(image, input_size=det_size)
        self.get_embedding(image, face)
        return face
