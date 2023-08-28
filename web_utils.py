# encoding:utf-8
import re

from flask import current_app, request, jsonify
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import functools
from mysql_model import Student, Teacher, Tch2Stu
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("mysql+pymysql://FaceAuth:FaceAuth@127.0.0.1:3306/Face")
Session = sessionmaker(bind=engine)

from code_status import code_status

code = code_status()


def create_token(api_user):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=36000)
    token = s.dumps({'id': api_user}).decode('ascii')
    return token


def verify_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except Exception:
        return None

    # user = Teacher.query.get(data['id'])
    session = Session()
    try:
        user = session.query(Teacher).filter_by(CID=data['id']).first()
        if not user:
            return False
    except Exception:
        return False
    finally:
        session.close()
    return user


def login_required(view_func):
    @functools.wraps(view_func)
    def verify(*args, **kwargs):
        try:
            # 在请求头上拿到token
            token = request.cookies.get('token')
        except Exception:
            # 没接收的到token,给前端抛出错误
            return jsonify(code=code.msg_redirect_tokenRequired, msg='token required')
            # return render_template('')

        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            s.loads(token)
        except Exception:
            return jsonify(code=code.msg_redirect_tokenOutdate, url='/', msg="login outdate")

        teacherid = verify_token(token)
        if not teacherid:
            return jsonify(code=code.msg_redirect_noAccess, url='/', msg='no access')

        return view_func(*args, **kwargs)

    return verify


def inputs_valid_check(inputs):
    if inputs is None:
        return False
    id = inputs["id"]
    password = inputs['password']
    if not all([id, password]):
        return False
    _id_s = re.match("[A-Z][a-z]", id)
    if _id_s or len(id) != 8:
        return False
    _id_n = re.match("[0-9]{8}", id)
    if len(_id_n.group()) != 8:
        return False
    if len(password)<6 or len(password)>20:
        return False
    _p = re.match("[a-zA-Z0-9_'@]{6,20}", password)
    if _p.group() != password:
        return False
    return True
