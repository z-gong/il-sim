import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, Text, Boolean

Base = declarative_base()
metadata = Base.metadata

db_file = 'sqlite:///ff.db'

engine = create_engine(db_file, echo=False)
Session = sessionmaker(engine)
session = Session()

class Paper(Base):
    __tablename__ = 'paper'
    id = Column(Integer, primary_key=True)
    code = Column(Text)

metadata.create_all(engine)

paper = Paper(code='wuyanzhu')
session.add(paper)
session.commit()

papers = session.query(Paper).filter(Paper.code=='zuyanzhu').all()