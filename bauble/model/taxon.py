#
# taxon.py
#

import traceback
import xml.sax.saxutils as sax
from itertools import chain

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import collection

import bauble
import bauble.db as db
#import bauble.utils as utils
#from bauble.utils.log import debug
import bauble.types as types
from bauble.model.geography import Geography
from bauble.model.genus import Genus
import bauble.search as search


class VNList(list):
    """
    A Collection class for Taxon.vernacular_names

    This makes it possible to automatically remove a
    default_vernacular_name if the vernacular_name is removed from the
    list.
    """
    def remove(self, vn):
        super(VNList, self).remove(vn)
        try:
            if vn.taxon.default_vernacular_name == vn:
                del vn.taxon.default_vernacular_name
        except Exception as e:
            debug(e)


infrasp_rank_values = {'subsp.': _('subsp.'),
                       'var.': _('var.'),
                       'subvar.': _('subvar'),
                       'f.': _('f.'),
                       'subf.': _('subf.'),
                       'cv.': _('cv.'),
                       None: ''}



# TODO: there is a trade_name column but there's no support yet for editing
# the trade_name or for using the trade_name when building the string
# for the taxon, for more information about trade_names see,
# http://www.hortax.org.uk/gardenplantsnames.html

# TODO: the specific epithet should not be non-nullable but instead
# make sure that at least one of the specific epithet, cultivar name
# or cultivar group is specificed

class Taxon(db.Base):
    """
    :Table name: taxon

    :Columns:
        *sp*:
        *sp2*:
        *sp_author*:

        *hybrid*:
            Hybrid flag

        *infrasp1*:
        *infrasp1_rank*:
        *infrasp1_author*:

        *infrasp2*:
        *infrasp2_rank*:
        *infrasp2_author*:

        *infrasp3*:
        *infrasp3_rank*:
        *infrasp3_author*:

        *infrasp4*:
        *infrasp4_rank*:
        *infrasp4_author*:

        *cv_group*:
        *trade_name*:

        *sp_qual*:
            Taxon qualifier

            Possible values:
                *agg.*: An aggregate taxon

                *s. lat.*: aggregrate taxon (sensu lato)

                *s. str.*: segregate taxon (sensu stricto)

        *label_distribution*:
            UnicodeText
            This field is optional and can be used for the label in case
            str(self.distribution) is too long to fit on the label.

    :Properties:
        *accessions*:

        *vernacular_names*:

        *default_vernacular_name*:

        *synonyms*:

        *distribution*:

    :Constraints:
        The combination of sp, sp_author, hybrid, sp_qual,
        cv_group, trade_name, genus_id
    """
    __tablename__ = 'taxon'
    __mapper_args__ = {'order_by': ['sp', 'sp_author']}

    # columns
    sp = Column(Unicode(64), index=True)
    sp2 = Column(Unicode(64), index=True)  # in case hybrid=True
    sp_author = Column(Unicode(128))
    hybrid = Column(Boolean, default=False)
    sp_qual = Column(types.Enum(values=['agg.', 's. lat.', 's. str.', None]),
                     default=None)
    cv_group = Column(Unicode(50))
    trade_name = Column(Unicode(64))

    infrasp1 = Column(Unicode(64))
    infrasp1_rank = Column(types.Enum(values=infrasp_rank_values.keys(),
                                      translations=infrasp_rank_values))
    infrasp1_author = Column(Unicode(64))

    infrasp2 = Column(Unicode(64))
    infrasp2_rank = Column(types.Enum(values=infrasp_rank_values.keys(),
                                      translations=infrasp_rank_values))
    infrasp2_author = Column(Unicode(64))

    infrasp3 = Column(Unicode(64))
    infrasp3_rank = Column(types.Enum(values=infrasp_rank_values.keys(),
                                      translations=infrasp_rank_values))
    infrasp3_author = Column(Unicode(64))

    infrasp4 = Column(Unicode(64))
    infrasp4_rank = Column(types.Enum(values=infrasp_rank_values.keys(),
                                      translations=infrasp_rank_values))
    infrasp4_author = Column(Unicode(64))

    genus_id = Column(Integer, ForeignKey('genus.id'), nullable=False)

    label_distribution = Column(UnicodeText)

    # relations
    synonyms = association_proxy('_synonyms', 'synonym')
    _synonyms = relation('TaxonSynonym',
                         primaryjoin='Taxon.id==TaxonSynonym.taxon_id',
                         cascade='all, delete-orphan', uselist=True,
                         backref='taxon')

    # this is a dummy relation, it is only here to make cascading work
    # correctly and to ensure that all synonyms related to this genus
    # get deleted if this genus gets deleted
    _syn = relation('TaxonSynonym',
                     primaryjoin='Taxon.id==TaxonSynonym.synonym_id',
                     cascade='all, delete-orphan', uselist=True)

    vernacular_names = relation('VernacularName', cascade='all, delete-orphan',
                                 collection_class=VNList,
                                backref=backref('taxon', uselist=False))
    _default_vernacular_name = relation('DefaultVernacularName', uselist=False,
                                         cascade='all, delete-orphan',
                                         backref=backref('taxon',
                                                         uselist=False))
    distribution = relation('TaxonDistribution',
                            cascade='all, delete-orphan',
                            backref=backref('taxon', uselist=False))

    habit_id = Column(Integer, ForeignKey('habit.id'), default=None)
    habit = relation('Habit', uselist=False, backref='taxa')

    flower_color_id = Column(Integer, ForeignKey('color.id'), default=None)
    flower_color = relation('Color', uselist=False, backref='taxa')

    #hardiness_zone = Column(Unicode(4))

    awards = Column(UnicodeText)

    def __init__(self, *args, **kwargs):
        super(Taxon, self).__init__(*args, **kwargs)

    def __str__(self):
        '''
        returns a string representation of this taxon,
        calls Taxon.str(self)
        '''
        return Taxon.str(self)

    def _get_default_vernacular_name(self):
        if self._default_vernacular_name is None:
            return None
        return self._default_vernacular_name.vernacular_name

    def _set_default_vernacular_name(self, vn):
        if vn is None:
            del self.default_vernacular_name
            return
        if vn not in self.vernacular_names:
            self.vernacular_names.append(vn)
        d = DefaultVernacularName()
        d.vernacular_name = vn
        self._default_vernacular_name = d

    def _del_default_vernacular_name(self):
        utils.delete_or_expunge(self._default_vernacular_name)
        del self._default_vernacular_name
    default_vernacular_name = property(_get_default_vernacular_name,
                                       _set_default_vernacular_name,
                                       _del_default_vernacular_name)

    def distribution_str(self):
        if self.distribution is None:
            return ''
        else:
            dist = ['%s' % d for d in self.distribution]
            return unicode(', ').join(sorted(dist))


    def markup(self, authors=False):
        '''
        returns this object as a string with markup

        :param authors: flag to toggle whethe the author names should be
        included
        '''
        return Taxon.str(self, authors, True)


    # in PlantPlugins.init() we set this to 'x' for win32
    hybrid_char = '\u2a09' # U+2A09

    @staticmethod
    def str(taxon, authors=False, markup=False):
        '''
        returns a string for taxon

        :param taxon: the taxon object to get the values from
        :param authors: flags to toggle whether the author names should be
        included
        :param markup: flags to toggle whether the returned text is marked up
        to show italics on the epithets
        '''
        # TODO: this method will raise an error if the session is none
        # since it won't be able to look up the genus....we could
        # probably try to query the genus directly with the genus_id
        genus = str(taxon.genus)
        sp = taxon.sp
        sp2 = taxon.sp2
        if markup:
            # escape = utils.xml_safe_utf8
            escape = str  # from bauble2 conversion
            italicize = lambda s: '<i>%s</i>' % escape(s)
            genus = italicize(genus)
            if sp is not None:
                sp = italicize(taxon.sp)
            if sp2 is not None:
                sp2 = italicize(taxon.sp2)
        else:
            italicize = lambda s: '%s' % s
            escape = lambda x: x

        author = None
        if authors and taxon.sp_author:
            author = escape(taxon.sp_author)

        infrasp = ((taxon.infrasp1_rank, taxon.infrasp1,
                    taxon.infrasp1_author),
                   (taxon.infrasp2_rank, taxon.infrasp2,
                    taxon.infrasp2_author),
                   (taxon.infrasp3_rank, taxon.infrasp3,
                    taxon.infrasp3_author),
                   (taxon.infrasp4_rank, taxon.infrasp4,
                    taxon.infrasp4_author))

        infrasp_parts = []
        group_added = False
        for rank, epithet, iauthor in infrasp:
            if rank == 'cv.' and epithet:
                if taxon.cv_group and not group_added:
                    group_added = True
                    infrasp_parts.append(_("(%(group)s Group)") % \
                                             dict(group=taxon.cv_group))
                infrasp_parts.append("'%s'" % escape(epithet))
            else:
                if rank:
                    infrasp_parts.append(rank)
                if epithet and rank:
                    infrasp_parts.append(italicize(epithet))
                elif epithet:
                    infrasp_parts.append(escape(epithet))

            if authors and iauthor:
                infrasp_parts.append(escape(iauthor))
        if taxon.cv_group and not group_added:
            infrasp_parts.append(_("%(group)s Group") % \
                                     dict(group=taxon.cv_group))

        # create the binomial part
        binomial = []
        if taxon.hybrid:
            if taxon.sp2:
                binomial = [genus, sp, taxon.hybrid_char, sp2, author]
            else:
                binomial = [genus, taxon.hybrid_char, sp, author]
        else:
            binomial = [genus, sp, sp2, author]

        # create the tail a.k.a think to add on to the end
        tail = []
        if taxon.sp_qual:
            tail = [taxon.sp_qual]

        parts = chain(binomial, infrasp_parts, tail)
        s = ' '.join(filter(lambda x: x not in ('', None), parts))
        return s


    infrasp_attr = {1: {'rank': 'infrasp1_rank',
                        'epithet': 'infrasp1',
                        'author': 'infrasp1_author'},
                    2: {'rank': 'infrasp2_rank',
                        'epithet': 'infrasp2',
                        'author': 'infrasp2_author'},
                    3: {'rank': 'infrasp3_rank',
                        'epithet': 'infrasp3',
                        'author': 'infrasp3_author'},
                    4: {'rank': 'infrasp4_rank',
                        'epithet': 'infrasp4',
                        'author': 'infrasp4_author'}}


    def json(self, depth=1, markup=False):
        """Return a dictionary representation of the Taxon.

        Kwargs:
           depth (int): The level of detail to return in the dict
           markup (bool): Whether the returned str should include markup.  This
                          parameter is only relevant with a depth>0
        Returns:
           dict.
        """
        d = dict(ref="/taxon/" + str(self.id))
        if(depth > 0):
            d['str'] = Taxon.str(self, markup=markup)
            d['genus'] = self.genus.json(depth=depth - 1)
        if(depth > 1):
            d['sp'] = self.sp
            d['sp2'] = self.sp2
            d['sp_author'] = self.sp_author
            d['hybrid'] = self.hybrid
            d['infrasp1'] = self.infrasp1
            d['infrasp1_rank'] = self.infrasp1_rank
            d['infrasp1_author'] = self.infrasp1_author
            d['infrasp2'] = self.infrasp2
            d['infrasp2_rank'] = self.infrasp2_rank
            d['infrasp2_author'] = self.infrasp2_author
            d['infrasp3'] = self.infrasp3
            d['infrasp3_rank'] = self.infrasp3_rank
            d['infrasp3_author'] = self.infrasp3_author
            d['infrasp4'] = self.infrasp4
            d['infrasp4_rank'] = self.infrasp4_rank
            d['infrasp4_author'] = self.infrasp4_author
            d['cv_group'] = self.cv_group
            d['trade_name'] = self.trade_name
            d['sp_qual'] = self.sp_qual
            d['label_distribution'] = self.label_distribution
            # d['distribution'] = self.distribution.json(depth=depth - 1)
            d['habit'] = None  # self.habit.json(depth=depth - 1)
            d['flower_color'] = None  # self.flower_color.json(depth=depth - 1)
            d['awards'] = self.awards
            if(self.flower_color):
                d['flower_color'] = self.flower_color.json(depth=depth - 1)
            if self.habit:
                d['habit'] = self.habit.json(depth=depth - 1)

            d['synonyms'] = [syn.json(depth=depth - 1) for syn in self.synonyms]
            d['notes'] = [note.json(depth=depth - 1) for note in self.notes]

        return d



    def get_infrasp(self, level):
        """
        level should be 1-4
        """
        return getattr(self, self.infrasp_attr[level]['rank']), \
            getattr(self, self.infrasp_attr[level]['epithet']), \
            getattr(self, self.infrasp_attr[level]['author'])


    def set_infrasp(self, level, rank, epithet, author=None):
        """
        level should be 1-4
        """
        setattr(self, self.infrasp_attr[level]['rank'], rank)
        setattr(self, self.infrasp_attr[level]['epithet'], epithet)
        setattr(self, self.infrasp_attr[level]['author'], author)



class TaxonNote(db.Base):
    """
    Notes for the taxon table
    """
    __tablename__ = 'taxon_note'
    __mapper_args__ = {'order_by': 'taxon_note.date'}

    date = Column(types.Date, default=func.now())
    user = Column(Unicode(64))
    category = Column(Unicode(32))
    note = Column(UnicodeText, nullable=False)
    taxon_id = Column(Integer, ForeignKey('taxon.id'), nullable=False)
    taxon = relation('Taxon', uselist=False,
                     backref=backref('notes', cascade='all, delete-orphan'))


    def json(self, depth=1):
        """Return a JSON representation of this TaxonNote
        """
        d = dict(ref="/taxon/" + str(self.taxon_id) + "/note/" + str(self.id))
        if(depth > 0):
            d['date'] = self.date.strftime("%d/%m/%Y")
            d['user'] = self.user
            d['category'] = self.category
            d['note'] = self.note
            d['taxon'] = self.taxon.json(depth=depth - 1)
        return d



class TaxonSynonym(db.Base):
    """
    :Table name: taxon_synonym
    """
    __tablename__ = 'taxon_synonym'

    # columns
    taxon_id = Column(Integer, ForeignKey('taxon.id'),
                        nullable=False)
    synonym_id = Column(Integer, ForeignKey('taxon.id'),
                        nullable=False, unique=True)

    # relations
    synonym = relation('Taxon', uselist=False,
                       primaryjoin='TaxonSynonym.synonym_id==Taxon.id')

    def __init__(self, synonym=None, **kwargs):
        # it is necessary that the first argument here be synonym for
        # the Taxon.synonyms association_proxy to work
        self.synonym = synonym
        super(TaxonSynonym, self).__init__(**kwargs)


    def __str__(self):
        return str(self.synonym)


    def json(self, depth=1):
        """Return a JSON representation of this TaxonSynonym
        """
        d = dict(ref="/taxon/" + str(self.taxon_id) + "/synonym/" + str(self.id))
        if(depth > 0):
            d['taxon'] = self.taxon.json(depth=depth - 1)
            d['synonym'] = self.synonym.json(depth=depth - 1)
        return d



class VernacularName(db.Base):
    """
    :Table name: vernacular_name

    :Columns:
        *name*:
            the vernacular name

        *language*:
            language is free text and could include something like UK
            or US to identify the origin of the name

        *taxon_id*:
            key to the taxon this vernacular name refers to

    :Properties:

    :Constraints:
    """
    __tablename__ = 'vernacular_name'
    name = Column(Unicode(128), nullable=False)
    language = Column(Unicode(128))
    taxon_id = Column(Integer, ForeignKey('taxon.id'), nullable=False)
    __table_args__ = (UniqueConstraint('name', 'language',
                                       'taxon_id', name='vn_index'), {})

    def __str__(self):
        if self.name:
            return self.name
        else:
            return ''


    def json(self, depth=1):
        """Return a dictionary representation of the Habit.

        Kwargs:
           depth (int): The level of detail to return in the dict
        Returns:
           dict.
        """

        # TODO: we probably don't need the self.id part here since there's should only be one default vernacular
        # name for the taxon
        d = dict(ref="/taxon/" + str(self.taxon_id) + "/vernacular_name/" + str(self.id))
        if(depth > 0):
            d['name'] = self.name
            d['language'] = self.language
            d['taxon'] = self.taxon.json(depth=depth - 1)
            d['str'] = str(self)
            d['default'] = False
            if(self.taxon.default_vernacular_name == self):
                d['default'] = True
        return d



class DefaultVernacularName(db.Base):
    """
    :Table name: default_vernacular_name

    DefaultVernacularName is not meant to be instantiated directly.
    Usually the default vernacular name is set on a taxon by setting
    the default_vernacular_name property on Taxon to a
    VernacularName instance

    :Columns:
        *id*:
            Integer, primary_key

        *taxon_id*:
            foreign key to taxon.id, nullable=False

        *vernacular_name_id*:

    :Properties:

    :Constraints:
    """
    __tablename__ = 'default_vernacular_name'
    __table_args__ = (UniqueConstraint('taxon_id', 'vernacular_name_id',
                                       name='default_vn_index'), {})

    # columns
    taxon_id = Column(Integer, ForeignKey('taxon.id'), nullable=False)
    vernacular_name_id = Column(Integer, ForeignKey('vernacular_name.id'),
                                nullable=False)

    # relations
    vernacular_name = relation(VernacularName, uselist=False)

    def __str__(self):
        return str(self.vernacular_name)


    def json(self, depth=1):
        """Return a dictionary representation of the Habit.

        Kwargs:
           depth (int): The level of detail to return in the dict
        Returns:
           dict.
        """

        # TODO: we probably don't need the self.id part here since there's should only be one default vernacular
        # name for the taxon
        d = dict(ref="/taxon/" + str(self.taxon_id) + "/default_vernacular_name/" + str(self.id))
        if(depth > 0):
            d['taxon'] = self.taxon(depth=depth - 1)
            d['str'] = str(self)
            d['vernacular_name'] = None
            if(self.vernacular_name):
                self.vernacular_name.json(depth=depth - 1)
        return d


class TaxonDistribution(db.Base):
    """
    :Table name: taxon_distribution

    :Columns:

    :Properties:

    :Constraints:
    """
    __tablename__ = 'taxon_distribution'

    # columns
    geography_id = Column(Integer, ForeignKey('geography.id'), nullable=False)
    taxon_id = Column(Integer, ForeignKey('taxon.id'), nullable=False)

    def __str__(self):
        return str(self.geography)


    def json(self, depth=1):
        """Return a dictionary representation of the TaxonDistribution.

        Kwargs:
           depth (int): The level of detail to return in the dict
        Returns:
           dict.
        """
        d = dict(ref="/taxon/" + str(self.taxon_id) + "/distribution/" + str(self.id))
        if(depth > 0):
            d['taxon'] = self.taxon.json(depth=depth - 1)
            d['geography'] = self.geography.json(depth=depth - 1)
            d['str'] = str(self)
        return d

# late bindings
TaxonDistribution.geography = relation('Geography',
                primaryjoin='TaxonDistribution.geography_id==Geography.id',
                                         uselist=False)

class Habit(db.Base):
    __tablename__ = 'habit'

    name = Column(Unicode(64))
    code = Column(Unicode(8), unique=True)

    def __str__(self):
        if self.name:
            return '%s (%s)' % (self.name, self.code)
        else:
            return str(self.code)

    def json(self, depth=1):
        """Return a dictionary representation of the Habit.

        Kwargs:
           depth (int): The level of detail to return in the dict
        Returns:
           dict.
        """
        d = dict(ref="/habit/" + str(self.id))
        if(depth > 0):
            d['name'] = self.name
            d['code'] = self.code
            d['str'] = str(self)
        return d



class Color(db.Base):
    __tablename__ = 'color'

    name = Column(Unicode(32))
    code = Column(Unicode(8), unique=True)

    def __str__(self):
        if self.name:
            return '%s (%s)' % (self.name, self.code)
        else:
            return str(self.code)


    def json(self, depth=1):
        """Return a dictionary representation of the Color.

        Kwargs:
           depth (int): The level of detail to return in the dict
        Returns:
           dict.
        """
        d = dict(ref="/color/" + str(self.id))
        if(depth > 0):
            d['name'] = self.name
            d['code'] = self.code
            d['str'] = str(self)
        return d


# setup search matcher
mapper_search = search.get_strategy('MapperSearch')
mapper_search.add_meta(('species', 'sp'), Taxon,
                       ['sp', 'sp2', 'infrasp1', 'infrasp2',
                        'infrasp3', 'infrasp4'])
mapper_search.add_meta(('taxon', 'sp'), Taxon,
                       ['sp', 'sp2', 'infrasp1', 'infrasp2',
                        'infrasp3', 'infrasp4'])
mapper_search.add_meta(('vernacular', 'vern', 'common'),
                       VernacularName, ['name'])
