# auth/tests/test_real_mongo_models.py
#
# Opt-in A-1 integration checks for MongoDB index and atomic-update semantics.

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import functools
import os
from threading import Barrier
from urllib.parse import urlparse
from uuid import uuid4

import mongoengine
from mongoengine import NotUniqueError
import pytest
import pytz

from models.data.connected_service import ConnectedService
from models.data.service_entitlement import ServiceEntitlement
from models.data.signing_key import SigningKey
from models.data.user import User


REAL_MONGO_URI = os.environ.get('AUTH_A1_REAL_MONGO_URI')
pytestmark = pytest.mark.skipif(
    not REAL_MONGO_URI,
    reason='set AUTH_A1_REAL_MONGO_URI to run real MongoDB A-1 checks',
)


@pytest.fixture
def real_mongo():
    parsed = urlparse(REAL_MONGO_URI)
    if parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        pytest.fail('AUTH_A1_REAL_MONGO_URI must point to loopback')

    database_name = f'thinkx_auth_a1_test_{uuid4().hex}'
    connect = mongoengine.connect
    real_connect = connect.func if isinstance(connect, functools.partial) else connect
    mongoengine.disconnect()
    connection = real_connect(database_name, host=REAL_MONGO_URI)
    try:
        yield
    finally:
        connection.drop_database(database_name)
        mongoengine.disconnect()


def test_real_mongo_a1_indexes_and_atomic_updates(real_mongo):
    for model in (User, ConnectedService, ServiceEntitlement, SigningKey):
        model.ensure_indexes()

    User(email='shared@example.com').save()
    with pytest.raises(NotUniqueError):
        User(suspended_email='shared@example.com').save()

    SigningKey(
        kid='active-one',
        public_key='public-one',
        private_key='private-one',
        status='active',
    ).save()
    with pytest.raises(NotUniqueError):
        SigningKey(
            kid='active-two',
            public_key='public-two',
            private_key='private-two',
            status='active',
        ).save()

    workers = 16
    connection_barrier = Barrier(workers)

    def connect_once():
        connection_barrier.wait()
        return ConnectedService.connect('subject-real', 'reference').id

    with ThreadPoolExecutor(max_workers=workers) as executor:
        connection_ids = list(
            executor.map(lambda _index: connect_once(), range(workers))
        )
    assert len(set(connection_ids)) == 1
    assert ConnectedService.objects.count() == 1

    base_time = datetime.now(pytz.utc)
    ServiceEntitlement.apply_projection(
        subject='subject-real',
        client_id='reference',
        plan='free',
        billing_status='none',
        payment_event_id='event-base',
        source_event_timestamp=base_time,
    )
    update_barrier = Barrier(2)

    def apply(event_id, timestamp, billing_status):
        update_barrier.wait()
        return ServiceEntitlement.apply_projection(
            subject='subject-real',
            client_id='reference',
            plan='pro',
            billing_status=billing_status,
            payment_event_id=event_id,
            source_event_timestamp=timestamp,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        older = executor.submit(
            apply,
            'event-older',
            base_time + timedelta(seconds=1),
            'past_due',
        )
        newer = executor.submit(
            apply,
            'event-newer',
            base_time + timedelta(seconds=2),
            'active',
        )
        older.result()
        newer.result()

    projection = ServiceEntitlement.objects.get(
        subject='subject-real', client_id='reference'
    )
    assert projection.payment_event_id == 'event-newer'
    assert projection.billing_status == 'active'
