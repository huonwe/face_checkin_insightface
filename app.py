# encoding:utf-8
from flask import Flask, render_template, Response, request, redirect, jsonify
import json
import processing_utils
from processing_utils import WorkerManager
from processing_utils import export_excel
from if_frame import FaceRecognition
import alive_detect
from code_status import code_status

from mysql_model import Student, Teacher, Tch2Stu, create_all_tables, drop_all_tables
from web_utils import create_token, verify_token, login_required, inputs_valid_check

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("mysql+pymysql://FaceAuth:FaceAuth@127.0.0.1:3306/Face")
Session = sessionmaker(bind=engine)

code = code_status()
Recognition = FaceRecognition()
workerManager = WorkerManager(instance=Recognition)

app = Flask(__name__)
app.secret_key = 'huonv'


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_data().decode()
        inputs = json.loads(data)
        if not inputs_valid_check(inputs):
            return jsonify(code=code.msg_inputIncorrect,
                           msg='no input or type error.ID must be 8 ints,length of password must >6 and < 20')

        session = Session()
        try:
            if session.query(Teacher).filter(Teacher.CID == inputs['id']).first():
                return jsonify(code=code.msg_inputChangeRequired, msg='user existed')
            else:
                session.add(Teacher(CID=inputs['id'], Password=inputs['password'], UserName=inputs['name']))
                session.commit()
                return jsonify(code=code.success, msg='signup succcess')
        except Exception:
            return jsonify(code=code.msg_dbOperationFailed, msg='db error')
        finally:
            session.close()

    return render_template('tchSignup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_data().decode()
        inputs = json.loads(data)
        resp = Response()
        if not inputs_valid_check(inputs):
            resp.data = 'please check your input'
            return resp
        session = Session()
        try:
            teacher = session.query(Teacher).filter(Teacher.CID == inputs['id'],
                                                    Teacher.Password == inputs['password']).first()
            if not teacher:
                resp.data = 'id or password incorrect'
                return resp
        except Exception:
            resp.data = 'db error'
            return resp
        finally:
            session.close()

        token = create_token(teacher.CID)
        resp.data = "success"
        resp.set_cookie('token', token)
        return resp
    return render_template('tchLogin.html')


@app.route('/home')
@login_required
def base():
    token = request.cookies.get('token')
    teacher = verify_token(token)
    UserName = teacher.UserName
    return render_template('Base.html', UserName=UserName)


@app.route('/')
def home():
    token = request.cookies.get('token')
    teacher = verify_token(token)
    if teacher:
        return redirect('/home')
    return redirect('/login')


@app.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    token = request.cookies.get('token')
    teacher = verify_token(token)
    TchCID = teacher.CID
    result_list = []
    session = Session()
    try:
        stu_list = session.query(Tch2Stu).filter_by(TchCID=TchCID).all()  # get all stu id of this teacher
        # print(stu_list)
        for stu in stu_list:  # to get stu name
            _stu = session.query(Student).filter_by(CID=stu.StuCID).first()
            if _stu:
                stu_info = {'id': stu.StuCID,
                            'name': _stu.UserName}
            else:
                stu_info = {'id': stu.StuCID,
                            'name': 'query failed'}
            result_list.append(stu_info)
        if len(result_list) == 0:
            return jsonify(code=code.success_EmptyResult, msg='You have not reg any stu.')
    except Exception:
        return jsonify(code=code.msg_dbOperationFailed, msg='db error')
    finally:
        session.close()
    return render_template('stuManager.html', result_list=result_list)


@app.route('/manager/del', methods=['POST'])
@login_required
def del_stu():
    token = request.cookies.get('token')
    teacher = verify_token(token)
    stu = json.loads(request.get_data())
    session = Session()
    try:
        session.query(Tch2Stu).filter(Tch2Stu.TchCID == teacher.CID, Tch2Stu.StuCID == stu['id']).delete()
        session.commit()
    except Exception:
        session.rollback()
        return jsonify(code=code.msg_dbOperationFailed, msg='db error')
    finally:
        session.close()
    return jsonify(code=code.success_elementActionRequired, msg='success')


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        token = request.cookies.get('token')
        this_teacher = verify_token(token)

        result_list = {'success': [],
                       'error_name': [],
                       'error_repeat': [],
                       'error_content': [],
                       'error_db': [],
                       'unknownError': []}

        TchCID = this_teacher.CID
        print(request.files)
        if len(request.files) == 0:
            return render_template('stuRegisterResult.html', resultList=result_list)
        files = request.files.getlist('file')

        session = Session()
        for file in files:
            filename = file.filename
            if not filename.endswith(('.jpg', '.png', '.JPG', '.PNG')):
                continue
            stu_info = processing_utils.detect_name(filename)
            if not stu_info:  # filename error
                result_list['error_name'].append(filename)
                continue
            image_cv2 = processing_utils.datatoCV2(file)

            try:
                _relation = session.query(Tch2Stu).filter_by(TchCID=TchCID, StuCID=stu_info[0]).first()
                if not _relation:
                    _stu = session.query(Student).filter_by(CID=stu_info[0]).first()
                    if not _stu:
                        status, info = Recognition.register(image_cv2, stu_info)
                        if status == -3:
                            session.add(Student(CID=stu_info[0], UserName=stu_info[1]))
                            session.add(Tch2Stu(TchCID=TchCID, StuCID=stu_info[0]))
                            session.commit()
                            result_list['success'].append(filename + '---->existed in Recognition system')
                            continue
                        elif status == -2:
                            result_list['error_content'].append(filename + '---->face should be only one')
                            continue
                        elif status == -1:
                            result_list['error_repeat'].append(
                                filename + '---->existed in Recognition system---->' + info)
                            continue
                        elif status == 0:
                            session.add(Student(CID=stu_info[0], UserName=stu_info[1]))
                            session.add(Tch2Stu(TchCID=TchCID, StuCID=stu_info[0]))
                            session.commit()
                            result_list['success'].append(filename + '---->found in db system')
                            continue
                        else:
                            result_list['unknownError'].append(filename)
                            continue
                    else:
                        session.add(Tch2Stu(TchCID=TchCID, StuCID=stu_info[0]))
                        session.commit()
                        result_list['success'].append(filename + '---->found in db system')
                        continue
                else:
                    # print(_stu)
                    result_list['error_repeat'].append(filename + '---->you have done it before')
                    continue

            except Exception:
                result_list['error_db'].append(filename)
                continue

        session.close()
        return render_template('stuRegisterResult.html', resultList=result_list)
    return render_template('stuRegister.html')


@app.route('/getStuList', methods=['GET'])
@login_required
def get_list():
    token = request.cookies.get('token')
    tch = verify_token(token)
    session = Session()
    worker = workerManager.find_worker(tch.CID)
    if worker:
        workerManager.destroy_worker(tch.CID)
    workerManager.create_worker(tch.CID)
    stu_list = session.query(Tch2Stu).filter_by(TchCID=tch.CID).all()
    stus = []
    for stu in stu_list:
        _stu = session.query(Student).filter_by(CID=stu.StuCID).first()
        info = {
            'CID': stu.StuCID,
            'NAME': _stu.UserName
        }
        stus.append(info)
    session.close()
    return jsonify(stus)


@app.route('/CheckInWithCamera', methods=['GET', 'POST'])
@login_required
def check_in():
    if request.method == 'POST':
        # time_start = time.time()
        token = request.cookies.get('token')
        teacher = verify_token(token)
        TchCID = teacher.CID
        worker = workerManager.find_worker(TchCID)
        if worker is None:
            worker = workerManager.create_worker(TchCID)

        data = request.get_data()
        image = processing_utils.base64toCV2(data)
        canvas_point_list = worker.get_canvas_point(image)
        # time_end = time.time()
        # print('ALL_TIME: ', time_end - time_start)
        # print(canvas_point_list)
        return jsonify(code=code.data_success, data=canvas_point_list)
    return render_template('CheckInWithCamera.html')


@app.route('/endCheckin', methods=['GET'])
@login_required
def end_checkin():
    token = request.cookies.get('token')
    teacher = verify_token(token)
    TchCID = teacher.CID
    worker = workerManager.find_worker(serial_number=TchCID)
    if worker:
        excel_path = export_excel(TchCID=TchCID, present=worker.present)
        workerManager.destroy_worker(TchCID)
        return jsonify(code=code.data_downloadable, path=excel_path)
    return jsonify(code=code.msg_operationFailed, msg='find no worker of yours')


@app.route('/downloadfile', methods=['GET', 'POST'])
@login_required
def downloadfile():
    if request.method == 'GET':
        filepath = request.args.get('filepath')
        filename = filepath.split('/')[-1]

        # 普通下载
        # response = make_response(send_from_directory(filepath, filename, as_attachment=True))
        # response.headers["Content-Disposition"] = "attachment; filename={}".format(filepath.encode().decode('latin-1'))
        # return send_from_directory(filepath, filename, as_attachment=True)

        # 流式读取
        def send_file(path):
            store_path = path
            with open(store_path, 'rb') as targetfile:
                while 1:
                    data = targetfile.read(20 * 1024 * 1024)  # 每次读取20M
                    if not data:
                        break
                    yield data

        response = Response(send_file(filepath),
                            content_type='application/octet-stream')
        response.headers["Content-disposition"] = 'attachment; filename=%s' % filename
        return response


@app.route('/recognitionWithPicture', methods=['GET', 'POST'])
@login_required
def recognition_with_img():
    if request.method == 'POST':
        if len(request.files) == 0:
            return jsonify(code=code.msg_inputIncorrect, msg='please upload files')

        files = request.files.getlist('file')
        # print(image_file)
        result_list = []
        for file in files:
            image = processing_utils.datatoCV2(file)
            faces = Recognition.get_face(image)
            result = Recognition.recognition_with_faces(faces)
            point_list = processing_utils.get_canavs_coordinate(faces, result)
            # info = Recognition.recognition_with_faces(faces)
            # image_circled = processing_utils.draw_on(image, faces, info)
            # _, jpg = cv2.imencode('.jpg', image_circled)
            # jpg_b64 = base64.b64encode(jpg).decode()
            # photos_reco.save(file)
            result = [point_list, len(faces)]
            result_list.append(result)
        print(result_list)
        return jsonify(result_list)

        # return render_template('recognitionWithPictureResult.html', result_list=result_list)
    return render_template('recognitionWithPicture.html')


@app.route('/android_post', methods=['POST'])
def android_get():
    data = request.get_data()
    image_cv2 = processing_utils.base64toCV2(data)
    # print(image.shape)
    judge, value = alive_detect.test(image_cv2, 0)
    if judge == True:
        # print("NOW IS",image.shape)
        result = Recognition.recognition(image_cv2)
        if len(result) != 1:
            return "person != 1"
        return result[0]["user_id"] + result[0]["user_name"]
    else:
        return "不是真人"

#
# @app.route('/wechat_get', methods=['POST'])
# def wechat_get_reg():
#     file = request.files.getlist('PhotoFromWechat')[0]
#     NAME = request.values.get('NAME')
#     ID = request.values.get('ID')
#     if file == None or NAME == None or ID == None:
#         return '个人信息有误，请联系开发者'
#
#     image = processing_utils.datatoCV2(file)
#
#     code, info = Recognition.register(image, ID + '-' + NAME)
#     if code != 0:
#         if code == -2:
#             return '人脸数不等于1'
#         elif code == -1:
#             return '库中检测到已注册人脸' + info
#     else:
#         return '注册成功'
#
#
# @app.route('/wechat_get_recognition', methods=['POST'])
# def wechat_get_recognition():
#     img = request.files.getlist("PhotoFromWechat")[0]
#     img = np.asarray(bytearray(img.read()), dtype="uint8")
#     # with open("D://t.png","wb") as f:
#     #     f.write(image)
#     #     f.close()
#     image = cv2.imdecode(img, cv2.IMREAD_COLOR)
#     result = Recognition.recognition(image)
#     if len(result) == 1 and result[0]['user_id'] != 'unknown':
#         print(result[0]['user_name'])
#         return result[0]['user_name']
#     else:
#         return '1'


# session = Session()
# drop_all_tables(engine)
# create_all_tables(engine)
# session.add(Teacher(CID='00000000', Password='000000000', UserName='1'))
# session.commit()
# session.close()
#
# a = session.query(Teacher).filter_by(id=2).first()
# print(a)
# if not a:
#     print('B')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
