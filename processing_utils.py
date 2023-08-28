# encoding:utf-8
import os
import re
import time

import cv2
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from openpyxl import Workbook
import datetime
import threading

from insightface_models.common import Face

from mysql_model import Student, Teacher, Tch2Stu
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("mysql+pymysql://FaceAuth:FaceAuth@127.0.0.1:3306/Face")
Session = sessionmaker(bind=engine)


def check_name(filename):
    allowed_ext = ['jpg', 'jpeg', 'png']
    name = re.split(r'[,-. ]', filename)
    if name[-1] not in allowed_ext or len(name) != 3 or (len(name[0]) != 10 and len(name[0] != 8)):
        return False
    else:
        return name[:2]


def detect_name(filename):
    name = filename
    result = check_name(name)
    if result:
        id = result[0]

        name = result[1]
        return [id, name]
    else:
        return False


def remove_pref(data):
    decoded_data = data.decode()
    if 'base64' in decoded_data[:30]:
        decoded_data = decoded_data.replace('data:image/jpeg;base64,', '', 1)
    return decoded_data.encode()


def datatoCV2(file):
    data_img = file.read()
    img_np = np.asarray(bytearray(data_img))
    image_CV2 = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    return image_CV2


def base64toCV2(data):
    data = remove_pref(data)
    img_file = base64.b64decode(data)

    img_np = np.asarray(bytearray(img_file))
    return cv2.imdecode(img_np, cv2.IMREAD_COLOR)


def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
        "uming.ttc", textSize, encoding="utf-8")
    # 绘制文本
    draw.text((left, top), text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def draw_on(img, faces, result):
    for i in range(len(faces)):
        face = faces[i]
        box = face.bbox.astype(np.int)
        color = (0, 0, 255)
        cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), color, 2)
        img = cv2ImgAddText(img, result[i]['user_name'],
                            box[0], box[1])  # 坐标
    return img


def get_canavs_coordinate(faces, result):
    canvas_point_list = []
    # print(result)
    for i in range(len(faces)):
        # face = faces[i]
        # box = face.bbox.astype(np.int)
        # print(box)
        canvas_point = {
            # 'canvas_x': str(box[0]),
            # 'canvas_y': str(box[1]),
            # 'canvas_width': str(box[2] - box[0]),
            # 'canvas_height': str(box[3] - box[1]),
            'Name': result[i]['user_name'],
            'CID': result[i]['user_id']
        }
        # print(canvas_point)
        canvas_point_list.append(canvas_point)
    return canvas_point_list


def export_excel(TchCID, present):
    excel_root = "./static/excel"
    if not os.path.exists(excel_root):
        os.makedirs(excel_root)
    allstu = []
    session = Session()
    students = session.query(Tch2Stu).filter_by(TchCID=TchCID).all()
    for stu in students:
        _stu = session.query(Student).filter_by(CID=stu.StuCID).first()
        allstu.append({'user_id': str(_stu.CID), 'user_name': _stu.UserName})
    session.close()
    cor = []
    for stu in allstu:
        # print(stu['user_id'],present)
        if stu['user_id'] in present:
            cor.append([stu['user_id'], stu['user_name'], '已到'])
        else:
            cor.append([stu['user_id'], stu['user_name'], ' '])
    if 'unknown' in present:
        cor.append(['PRESENT:', len(present)-1])
    else:
        cor.append(['PRESENT:', len(present)])
    cor.append(['ALL', len(allstu)])
    # 新建一个excel文档
    wb = Workbook()
    ws = wb.active

    row_1 = ['学号', '姓名', '状态']
    ws.append(row_1)
    for stu in cor:
        ws.append(stu)

    curr_time = datetime.datetime.now()
    excel_name = curr_time.strftime("%Y%m%d%H%M%S")

    excel_path = excel_root + "/%s.xlsx" % excel_name
    wb.save(excel_path)

    return excel_path


class Worker_thread(threading.Thread):
    def __init__(self, instance, image):
        super(Worker_thread, self).__init__()
        self.instance = instance
        self.image = image
        self.faces = []
        self.results = []
        self.status = 1

    def process(self, image):
        time1 = time.time()
        self.faces = self.instance.model.get(image)
        self.results = self.instance.recognition_with_faces(self.faces)
        time2 = time.time()
        print('pure model time :',time2-time1)

    def run(self):
        self.process(self.image)
        self.status = 0

    def get_result(self):
        return self.faces, self.results


class Worker:
    def __init__(self, instance, serial_number):
        self.serial_number = serial_number
        self.instance = instance
        self.thread_list = []
        self.present = []

    def start_thread(self, image):
        # _thread = Worker_thread(self.instance, image)
        # _thread.start()
        # _thread.join()
        time1 = time.time()

        face = self.instance.get_face(image)
        results = self.instance.recognition_with_faces(face)
        time2 = time.time()
        print('pure model time :', time2-time1)

        # return _thread.get_result()
        return face, results

    def update_context(self, results):
        for result in results:
            stuid = result['user_id']
            if stuid not in self.present:
                self.present.append(stuid)

    def get_canvas_point(self, image_cv2):
        faces, results = self.start_thread(image_cv2)
        self.update_context(results)
        return get_canavs_coordinate(faces, results)

    def clear_present(self):
        self.present = []


class WorkerManager:
    def __init__(self, instance):
        self.worker_list = []
        self.instance = instance
        self.maxWorker = 10

    def create_worker(self, serial_number):
        worker = Worker(self.instance, serial_number)
        self.worker_list.append(worker)
        return worker

    def destroy_worker(self, serial_number):
        worker = self.find_worker(serial_number)
        if worker:
            worker.clear_present()
            self.worker_list.remove(worker)
            del worker

    def check_available(self):
        # print(len(self.worker_list))
        if len(self.worker_list) >= self.maxWorker:
            return False
        return True

    def find_worker(self, serial_number):
        for worker in self.worker_list:
            if worker.serial_number == serial_number:
                return worker
        return None

    def show_worker(self):
        print(self.worker_list)

# if __name__ =='__main__':
# Manager = WorkerManager()
# worker = Manager.create_worker(1)
# print(Manager.worker_list)
# Manager.destroy_worker(1)
# print(Manager.worker_list)
# list1 = [1,2,3,4]
# list1.remove(None)
# print(list1)
