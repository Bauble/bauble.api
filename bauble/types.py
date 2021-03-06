#
# types.py
#

from datetime import datetime
import re

import dateutil.parser as date_parser
import sqlalchemy.types as types

import bauble.error as error

# TODO: define the _ function until we get i18n working
def _(s):
    return s


class EnumError(error.BaubleError):
    """Raised when a bad value is inserted or returned from the Enum type"""


class Enum(types.TypeDecorator):
    """A database independent Enum type. The value is stored in the
    database as a Unicode string.
    """
    impl = types.Unicode

    def __init__(self, values, empty_to_none=False, strict=True,
                 translations={}, **kwargs):
        """
        : param values: A list of valid values for column.
        :param empty_to_none: Treat the empty string '' as None.  None
        must be in the values list in order to set empty_to_none=True.
        :param strict:
        :param translations: A dictionary of values->translation
        """
        # create the translations from the values and set those from
        # the translations argument, this way if some translations are
        # missing then the translation will be the same as value
        self.translations = dict((v, v) for v in values)
        for key, value in translations.items():
            self.translations[key] = value
        if values is None or len(values) is 0:
            raise EnumError(_('Enum requires a list of values'))
        if empty_to_none and None not in values:
            raise EnumError(_('You have configured empty_to_none=True but '
                              'None is not in the values lists'))
        self.values = list(values)
        self.strict = strict
        self.empty_to_none = empty_to_none
        # the length of the string/unicode column should be the
        # longest string in values
        size = max([len(v) for v in values if v is not None])
        super(Enum, self).__init__(size, **kwargs)


    def process_bind_param(self, value, dialect):
        """
        Process the value going into the database.
        """
        if self.empty_to_none and value is '':
            value = None
        if value not in self.values:
            raise EnumError(_('"%(value)s" not in Enum.values: %(all_values)s') %
                            dict(value=value, all_values=self.values))
        return value


    def process_result_value(self, value, dialect):
        """
        Process the value returned from the database.
        """
        # if self.strict and value not in self.values:
        #     raise ValueError(_('"%s" not in Enum.values') % value)
        return value


    def copy(self):
        return Enum(self.values, self.empty_to_none, self.strict)



# class tzinfo(datetime.tzinfo):

#     """
#     A tzinfo object that can handle timezones in the format -HH:MM or +HH:MM
#     """
#     def __init__(self, name):
#         super(tzinfo, self).__init__()
#         self._tzname = name
#         hours, minutes = [int(v) for v in name.split(':')]
#         self._utcoffset = datetime.timedelta(hours=hours, minutes=minutes)

#     def tzname(self):
#         return self._tzname

#     def utcoffset(self, dt):
#         return self._utcoffset



class DateTime(types.TypeDecorator):
    """
    A DateTime type that allows strings
    """
    impl = types.DateTime

    _rx_tz = re.compile('[+-]')

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            # parse the datetime which should be iso 8601 format with a preference
            # for YY-MM-DD, although the parser is a little bit loose on
            # what it accepts
            value = date_parser.parse(value, dayfirst=False, yearfirst=True)

        return value


    def process_result_value(self, value, dialect):
        return value


    def copy(self):
        return DateTime()

    def __str__(self):
        return self.isoformat()



class Date(types.TypeDecorator):
    """
    A Date type that allows Date strings
    """
    impl = types.Date

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            # accept ISO 8601 formatted date strings only
            if '-' in value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            elif '/' in value:
                # not technically ISO 8601 but we can be a little flexible
                value = datetime.strptime(value, "%Y/%m/%d").date()
            elif len(value) == 8:
                value = datetime.strptime(value, '%Y%m%d').date()
            else:
                raise ValueError("Could not parse date string: " + value)

        return value


    def process_result_value(self, value, dialect):
        return value


    def copy(self):
        return Date()

    def __str__(self):
        return self.isoformat()
