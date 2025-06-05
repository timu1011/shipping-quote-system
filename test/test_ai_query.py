import os
import sys
from datetime import datetime
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from src.app import app, db
from src.models import Port, ContainerType, Route, BaseRate, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # create sample data
        port_sha = Port(code='SHA', name='上海', country='CN', region='Asia')
        port_lax = Port(code='LAX', name='洛杉磯', country='US', region='America')
        ct_40hq = ContainerType(code='40HQ', name='40呎高櫃', size='40HQ', description='')
        db.session.add_all([port_sha, port_lax, ct_40hq])
        db.session.flush()
        route = Route(origin_port_id=port_sha.id, destination_port_id=port_lax.id, transit_time=15)
        db.session.add(route)
        db.session.flush()
        base_rate = BaseRate(route_id=route.id, container_type_id=ct_40hq.id,
                              price=1000, currency='USD', effective_date=datetime.utcnow().date())
        db.session.add(base_rate)
        db.session.commit()
        test_user = User(username='tester', email='t@example.com', password='hash', role='customer')
        db.session.add(test_user)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def login_session(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'tester'
        sess['role'] = 'customer'


def test_chinese_query(client):
    login_session(client)
    resp = client.post('/quote/process_ai_query', data={'query': '請提供從上海到洛杉磯的40HQ運費'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert '上海' in data['response']
    assert '洛杉磯' in data['response']


def test_english_query(client):
    login_session(client)
    resp = client.post('/quote/process_ai_query', data={'query': 'rate from shanghai to los angeles 40hq'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert '上海' in data['response']
    assert '洛杉磯' in data['response']
