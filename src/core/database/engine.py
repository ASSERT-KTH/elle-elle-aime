import copy
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from core.database.schema import Result

config = dotenv_values(".env")
RDS_USERNAME = config.get('RDS_USERNAME')
RDS_PASSWORD = config.get('RDS_PASSWORD')
RDS_HOSTNAME = config.get('RDS_HOSTNAME')
RDS_DATABASE = config.get('RDS_DATABASE')
RDS_URL = 'postgresql://{}:{}@{}/{}'.format(
    RDS_USERNAME, RDS_PASSWORD, RDS_HOSTNAME, RDS_DATABASE)


def get_engine():
    return create_engine(RDS_URL)


def connect():
    connection = get_engine().connect()
    return connection


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def save(obj):
    try:
        session = get_session()
        session.add(obj)
        session.commit()
    except Exception as e:
        # try again!
        print('Error: {}'.format(e))
        session = get_session()
        session.add(obj)
        session.commit()


def get_result_by_id(id):
    session = get_session()
    result = session.query(Result).get(id)
    if result == None:
        raise Exception('Cannot find result by id: ', id)
    return result


def update_result_by_id(id, obj):
    session = get_session()
    session.query(Result).filter(Result.id == id).update({'respond_code_token': obj.respond_code_token, 'respond_compiled_output': obj.respond_compiled_output,
                                                          'respond_test_output': obj.respond_test_output, 'result_type': obj.result_type, 'error_message': obj.error_message})
    print('Update result: {}'.format(obj.result_type))
    session.commit()


def find_all_success():
    session = get_session()
    results = session.query(Result).filter(
        Result.result_type == 'TEST_SUCCESS', Result.temperature == 0.8).all()
    return results


def find_samples_by_conditions(project, bug_id, result_type, temperature):
    session = get_session()
    results = session.query(Result).filter(
        Result.project == project, Result.bug_id == bug_id, Result.result_type == result_type, Result.temperature == temperature).order_by(Result.created_on).all()
    return results
