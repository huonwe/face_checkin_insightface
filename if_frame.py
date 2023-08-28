# encoding:utf-8
import math
import os
import numpy as np
# import insightface
# from insightface.app import FaceAnalysis
import cv2
import pickle
import insightface_models.scrfd
import insightface_models.arcface_onnx
# import insightface_models.handler
from insightface_models.common import Face

def distance(embeddings1, embeddings2):
    diff = np.subtract(embeddings1, embeddings2)
    # print(diff)
    dist = np.sum(np.square(diff))
    # print(dist)
    return dist


# def feature_compare(feat1, feat2):
#     from numpy.linalg import norm
#     feat1 = feat1.ravel()
#     feat2 = feat2.ravel()
#     sim = np.dot(feat1, feat2) / (norm(feat1) * norm(feat2))
#     return sim


class FaceRecognition:
    def __init__(self):
        # config
        self.face_img_db = "face_db/img/"
        self.face_bin_db = "face_db/data/"
        self.threshold = 390
        # 加载人脸识别模型
        self.detector = insightface_models.scrfd.SCRFD('./insightface_models/models/scrfd_10g_bnkps.onnx')
        self.handler = insightface_models.arcface_onnx.ArcFaceONNX('./insightface_models/models/msv3r50.onnx')
        # self.handler = insightface_models.handler.Handler()
        self.detector.prepare(0)
        self.handler.prepare(0)
        # self.model = FaceAnalysis(allowed_modules=['detection', 'recognition'])
        # self.model.prepare(ctx_id=self.gpu_id)
        # self.handler = self.model.models['recognition']

        # 人脸库
        self.faces_library = []
        # Faster Serach
        self.id_only_library = []
        self.load_all_faces()

    # 加载人脸库中的人脸
    def load_all_faces(self):
        self.faces_library = []
        if not os.path.exists(self.face_bin_db):
            os.makedirs(self.face_bin_db)
        for root, dirs, files in os.walk(self.face_bin_db):
            if files:
                for file in files:
                    # print(root)
                    user_info_file = open(root + file, 'rb')
                    user_info = pickle.load(user_info_file)
                    # print(user_info)
                    self.faces_library.append(user_info)
                    self.id_only_library.append(user_info['user_id'])

    def find_most_similar(self, embedding):
        dist_index = list()
        result = dict()
        if len(self.faces_library) == 0:
            return result, 0
        for face_existed in self.faces_library:
            dist = distance(embedding, face_existed["embedding"])
            dist_index.append(dist)
            # print(sim)
        most_similar_index = np.argmin(dist_index)
        result['user_name'] = self.faces_library[most_similar_index]['user_name']
        result['user_id'] = self.faces_library[most_similar_index]['user_id']
        return result, dist_index[most_similar_index]

    def get_face(self, img):
        bboxes, kpss = self.detector.detect(img, 0.3, input_size=(160, 160))
        # print(bboxes.shape)
        if bboxes.shape[0] == 0:
            return []
        ret = []
        for i in range(bboxes.shape[0]):
            bbox = bboxes[i, 0:4]
            det_score = bboxes[i, 4]
            kps = None
            if kpss is not None:
                kps = kpss[i]
            face = Face(bbox=bbox, kps=kps, det_score=det_score)
            self.handler.get(img, face)
            # print(face.bbox)
            ret.append(face)
        # print(len(ret))
        return ret

    def recognition_with_faces(self, faces):
        results = list()
        # if face
        for face in faces:
            result, dist = self.find_most_similar(face.embedding)
            if dist < self.threshold:
                results.append(result)
            else:
                result["user_id"] = "unknown"
                result["user_name"] = "unknown"
                results.append(result)
            # print(result)
        return results

    def register(self, image, id_name):
        user_id, user_name = id_name[0], id_name[1]
        if user_id in self.id_only_library:
            return -3, user_id + user_name + ":id crashed"
        # 判断人脸是否存在
        face = self.detector.detect(image)
        if len(face) != 1:
            return -2, 'error_content'  # error_content

        result = {}
        embedding = self.handler.get(image, face)
        # embedding = face[0]["embedding"]
        if len(self.faces_library) == 0:
            similarity = 0
        else:
            result, similarity = self.find_most_similar(embedding)

        if similarity < self.threshold:
            # is_exits = True
            return -1, result["user_id"] + "with similarity: " + str(similarity)

        # 符合注册条件保存图片，同时把特征添加到人脸特征库中
        cv2.imencode('.png', image)[1].tofile(os.path.join(
            self.face_img_db, '%s.png' % (user_id + '-' + user_name)))
        self.faces_library.append({
            "user_name": user_name,
            "user_id": user_id,
            "embedding": embedding
        })
        self.id_only_library.append(user_id)

        # 创建用户信息的二进制文件
        user_info = {
            "user_name": user_name,
            "user_id": user_id,
            "embedding": embedding
        }
        user_info_file = open(self.face_bin_db + user_id + '.pkl', 'wb')
        pickle.dump(user_info, user_info_file)
        user_info_file.close()
        return 0, user_id

    def clear_faces(self):
        self.faces_library = list()

# if __name__ == "__main__":
#     FR = FaceRecognition()
#     image1 = cv2.imread('./2013920207-HuHongwei.jpg')
#     image2 = cv2.imread('2013920206-GuoYue.png')
#
#     # print(image.size)
#     faces1 = FR.model.get(image1)
#     faces2 = FR.model.get(image2)
#     # print(faces1)
#     handler = FR.model.models['recognition']
#     feat1 = handler.get_feat(image1)
#     feat2 = handler.get_feat(image2)
