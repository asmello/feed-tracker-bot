from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def initialize_db(engine):
	Base.metadata.create_all(engine)

def recreate_db(engine):
	Base.metadata.drop_all(engine)
	initialize_db(engine)
