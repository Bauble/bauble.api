#
# ReportDef table definition
#
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.associationproxy import association_proxy

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
#import bauble.utils.web as web
import bauble.types as types
import bauble.search as search

#
# ReportDef
#
class ReportDef(db.Base):
    """
    :Table name: report_def

    :Columns:
        *name*:
            The name if of the report definition.

        *query*:
            The query string.

        *visible_columns*:
            Visible columns.

        *column_widths
            Column widths.

        *column_headers
            Column_headers

        *xsl_stylesheet
            The XSL stylesheet text

        *xsl_stylesheet_filename
            The original filename of the XSL stylesheet.


    :Properties:
        *synonyms*:
            An association to _synonyms that will automatically
            convert a Family object and create the synonym.

    :Constraints:
        The family table has a unique constraint on family/qualifier.
    """
    __tablename__ = 'report_def'
    #__table_args__ = (UniqueConstraint('family', 'qualifier'),)
    #__mapper_args__ = {'order_by': ['Family.family', 'Family.qualifier']}

    # columns
    name = Column(String, unique=True, nullable=False, index=True)
    query = Column(String)

    visible_columns = Column(String)  # a string that represents a JSON list/array
    column_widths = Column(String)  # a json object that maps column names to widths
    column_headers = Column(String) # a json object that maps column names to headers

    xsl_stylesheet = Column(String)
    xsl_stylesheet_filename = Column(String)

    # TODO: fix the created and lastupdate user relationships..for some reason there's
    # an error when calling /admin/initdb that has to do with User not being defined,
    # this is probably some weird issues with the two mappers having different metadata
    # or pg schema
    #created_by_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # created_by_user = relationship('User', cascade='all,delete-orphan',
    #                                primaryjoin='ReportDef.created_by_user_id==User.id')

    #last_updated_by_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # last_updated_by_user = relationship('User', cascade='all,delete-orphan',
    #                                     primaryjoin='ReportDef.last_updated_by_user_id==User.id')


    def json(self, depth=1, markup=True):
        d = dict(ref="/report/" + str(self.id))
        if depth > 0:
            d['name']= self.name
            d['query'] = self.query
            d['visible_columns'] = self.visibile_columns
            d['column_widths'] = self.column_widths
            d['column_headers'] = self.column_headers
            d['xsl_stylesheet_filename'] = self.xsl_stylesheet_filename

        if depth > 1:
            d['xsl_stylesheet_filename'] = self.xsl_stylesheet_filename
