# encoding:utf-8
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Student(Base):
    __tablename__ = 'stu'
    ID = Column(Integer, autoincrement=True, primary_key=True)
    CID = Column(String(10))
    UserName = Column(String(20))
    Password = Column(String(20))


class Teacher(Base):
    __tablename__ = 'tch'
    ID = Column(Integer, autoincrement=True, primary_key=True)
    CID = Column(String(8))
    UserName = Column(String(20))
    Password = Column(String(20))


class Tch2Stu(Base):
    __tablename__ = 'tch2stu'
    EventID = Column(Integer, autoincrement=True, primary_key=True)
    TchCID = Column(Integer)
    StuCID = Column(Integer)
    # StuGroup = Column(String(20))


def create_all_tables(engine):
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    Base.metadata.drop_all(engine)
