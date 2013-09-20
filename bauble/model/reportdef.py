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

        *template
            The template to use

        *template_type
            The type of the template

        *template_filename
            The original filename of the template

        * output_type
            A hint to convert the output


    :Properties:
        *synonyms*:
            An association to _synonyms that will automatically
            convert a Family object and create the synonym.

    :Constraints:
        The family table has a unique constraint on family/qualifier.
    """
    __tablename__ = 'report_def'

    # columns
    name = Column(String, unique=True, nullable=False, index=True)
    query = Column(String)

    visible_columns = Column(String)  # a string that represents a JSON list/array
    column_widths = Column(String)  # a json object that maps column names to widths
    column_headers = Column(String) # a json object that maps column names to headers

    # template can either me a Mako template or an XSL stylesheet
    template = Column(String)
    template_filename = Column(String)
    template_type = Column(String)

    # more of a hint, used for xsl formatter to generate PDF
    output_type = Column(String)

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
            d['template_filename'] = self.template_filename
            d['template_mimetype'] = self.template_mimetype

        if depth > 1:
            d['template'] = self.template
