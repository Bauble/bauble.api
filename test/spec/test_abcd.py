import bauble.abcd as abcd
import bauble.abcd.adapters as adapters
import bauble.db as db
from test.fixtures import org, user_session, family, genus, taxon
import test.utils as utils

def test_abcd(user_session, taxon):
    user_session.add(taxon)

    data = abcd.create_abcd([abcd.adapters.TaxonABCDAdapter(t) for t in [taxon]], validate=False)
