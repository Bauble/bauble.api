import json

import pytest
import requests
from sqlalchemy.exc import IntegrityError

import bauble.db as db
from bauble.model import ReportDef
from test.fixtures import organization, user, session
import test.api as api

@pytest.fixture
def setup(organization, session):
    setup.organization = session.merge(organization)
    setup.user = setup.organization.owners[0]
    setup.session = session
    db.set_session_schema(session, setup.organization.pg_schema)
    return setup


def test_index(setup):
    reports = []

    for num in range(0, 5):
        reports.append(ReportDef(name=api.get_random_name()))
    setup.session.add_all(reports)
    setup.session.commit()

    # a list request should work
    response = api.get_resource('/report', user=setup.user)
    assert isinstance(response, list)

    for report in reports:
        setup.session.delete(report)
    setup.session.commit()


def test_patch(setup):
    session = setup.session

    report = ReportDef(name=api.get_random_name())
    session.add(report)
    session.commit()

    report.name += "_patched"

    # should fail with a 400 response if there is no request body
    response = api.update_resource('/report/{}'.format(report.id), report, setup.user)

    data = json.dumps(report.json())
    api.update_resource('/report/{}'.format(report.id), data, setup.user)
    session.delete(report)
    session.commit()


def test_post(setup):
    session = setup.session
    data = {
        'name': 'Test Report',
        'settings': {
            'visible_columns': ['name', 'str']
        }
    }

    report = api.create_resource('/report', data, setup.user)
    session.delete(session.query(ReportDef).get(report['id']))
    session.commit()


def test_delete(setup):
    session = setup.session

    report = ReportDef(name=api.get_random_name())
    session.add(report)
    session.commit()

    api.delete_resource('/report/{}'.format(report.id), setup.user)

    report_id = report.id
    session.expunge(report)
    assert session.query(ReportDef).get(report_id) is None
