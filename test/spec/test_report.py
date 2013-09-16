import os

import bauble.db as db
import bauble.report as report
from bauble.model import Family

import test.fixtures as fixtures
from test.fixtures import org
import test.utils as utils

def test_saving_reports():
    pass

def test_gen_from_saved_report():
    pass

#@with_default_families

def test_xsl_pdf(org):
    session = None
    try:
        session = db.connect()
        session.add(org)
        db.set_session_schema(session, org.pg_schema)

        family = Family(family=utils.random_str())
        session.add(family)
        session.commit()

        f = open(os.path.join(os.path.dirname(__file__), "test.xsl"))
        stylesheet = f.read()
        f.close()
        query = session.query(Family).all()
        pdf = report.create_pdf_from_xsl(query, stylesheet)
        assert pdf is not None

    finally:
        if session:
            session.close()
