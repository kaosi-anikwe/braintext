from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String


Base = declarative_base()


class Messages(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    role = Column(String)
    content = Column(String)

    def __init__(self, message, db_path):
        self.role = message["role"]
        self.content = message["content"]
        self.db_path = db_path

    def session(self):
        Session = sessionmaker(bind=get_engine(self.db_path))
        return Session()

    def insert(self):
        session = self.session()
        session.add(self)
        session.commit()
        session.close()


def get_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}")


def create_all(engine):
    Base.metadata.create_all(engine)
