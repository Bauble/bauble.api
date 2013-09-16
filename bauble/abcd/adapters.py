import html

from sqlalchemy import *
from sqlalchemy.orm import *

from bauble.model import Family, Genus, Taxon, Accession, Plant

class ABCDAdapter(object):
    """
    An abstract base class for creating ABCD adapters.
    """
    # TODO: create a HigherTaxonRank/HigherTaxonName iteratorator for a list
    # of all the higher taxon

    # TODO: need to mark those fields that are required and those that
    # are optional
    def extra_elements(self, unit):
        """
        Add extra non required elements
        """
        pass

    def __init__(self, obj):
        self._object = obj

    def get_UnitID(self):
        """
        Get a value for the UnitID
        """
        pass

    def get_family(self):
        """
        Get a value for the family.
        """
        pass

    def get_FullScientificNameString(self, authors=True):
        """
        Get the full scientific name string.
        """
        pass

    def get_GenusOrMonomial(self):
        """
        Get the Genus string.
        """
        pass

    def get_FirstEpithet(self):
        """
        Get the first epithet.
        """
        pass

    def get_AuthorTeam(self):
        """
        Get the Author string.
        """
        pass

    def get_InformalNameString(self):
        """
        Get the common name string.
        """
        pass


class TaxonABCDAdapter(ABCDAdapter):
    """
    An adapter to convert a Taxa to an ABCD Unit, the TaxaABCDAdapter
    does not create a valid ABCDUnit since we can't provide the required UnitID
    """
    def __init__(self, taxa, for_labels=False):
        super(TaxonABCDAdapter, self).__init__(taxa)

        # hold on to the accession so it doesn't get cleaned up and closed
        self.session = object_session(taxa)
        self.for_labels = for_labels
        self.taxa = taxa


    def get_UnitID(self):
        # **** Returning the empty string for the UnitID makes the
        # ABCD data NOT valid ABCD but it does make it work for
        # creating reports without including the accession or plant
        # code
        return ""

    def get_DateLastEdited(self):
        return html.escape(self.taxa._last_updated.isoformat())

    def get_family(self):
        return html.escape(str(self.taxa.genus.family))

    def get_FullScientificNameString(self, authors=True):
        s = Taxon.str(self.taxa, authors=authors,markup=False)
        return html.escape(s)

    def get_GenusOrMonomial(self):
        return html.escape(str(self.taxa.genus))

    def get_FirstEpithet(self):
        return html.escape(str(self.taxa.sp))

    def get_AuthorTeam(self):
        author = self.taxa.sp_author
        if author is None:
            return None
        else:
            return html.escape(author)

    def get_InformalNameString(self):
        vernacular_name = self.taxa.default_vernacular_name
        if vernacular_name is None:
            return None
        else:
            return html.escape(vernacular_name)

    def get_Notes(self):
        if not self.taxa.notes:
            return None
        notes = []
        for note in self.taxa.notes:
            notes.append(dict(date=html.escape(note.date.isoformat()),
                              user=html.escape(note.user),
                              category=html.escape(note.category),
                              note=utils.html.escape(note.note)))
        return utf8(notes)

    def extra_elements(self, unit):
        # distribution isn't in the ABCD namespace so it should create an
        # invalid XML file
        if self.for_labels:
            if self.taxa.label_distribution:
                etree.SubElement(unit, 'distribution').text=\
                    self.taxa.label_distribution
            elif self.taxa.distribution:
                etree.SubElement(unit, 'distribution').text=\
                    self.taxa.distribution_str()




class AccessionABCDAdapter(TaxonABCDAdapter):
    """
    An adapter to convert a Plant to an ABCD Unit
    """
    def __init__(self, accession, for_labels=False):
        super(AccessionABCDAdapter, self).__init__(accession.taxa,
                                                   for_labels)
        self.accession = accession


    def get_UnitID(self):
        return html.escape(str(self.accession))


    def get_FullScientificNameString(self, authors=True):
        s = self.accession.taxa_str(authors=authors , markup=False)
        return html.escape(s)


    def get_DateLastEdited(self):
        return utils.html.escape(self.accession._last_updated.isoformat())


    def get_Notes(self):
        if not self.accession.notes:
            return None
        notes = []
        for note in self.accession.notes:
            notes.append(dict(date=html.escape(note.date.isoformat()),
                              user=html.escape(note.user),
                              category=html.escape(note.category),
                              note=html.escape(note.note)))
        return html.escape(notes)


    def extra_elements(self, unit):
        super(AccessionABCDAdapter, self).extra_elements(unit)
        if self.for_labels:
            if self.taxa.label_distribution:
                etree.SubElement(unit, 'distribution').text=\
                    self.taxa.label_distribution
            elif self.taxa.distribution:
                etree.SubElement(unit, 'distribution').text=\
                    self.taxa.distribution_str()

        if self.accession.source and self.accession.source.collection:
            collection = self.accession.source.collection
            utf8 = html.escape
            gathering = ABCDElement(unit, 'Gathering')

            if collection.collectors_code:
                ABCDElement(gathering, 'Code',
                            text=utf8(collection.collectors_code))

            # TODO: get date pref for DayNumberBegin
            if collection.date:
                date_time = ABCDElement(gathering, 'DateTime')
                ABCDElement(date_time, 'DateText',
                            html.escape(collection.date.isoformat()))

            if collection.collector:
                agents = ABCDElement(gathering, 'Agents')
                agent = ABCDElement(agents, 'GatheringAgent')
                ABCDElement(agent, 'AgentText', text=utf8(collection.collector))

            if collection.locale:
                ABCDElement(gathering, 'LocalityText',
                            text=utf8(collection.locale))

            if collection.region:
                named_areas = ABCDElement(gathering, 'NamedAreas')
                named_area = ABCDElement(named_areas, 'NamedArea')
                ABCDElement(named_area, 'AreaName',
                            text=utf8(collection.region))

            if collection.habitat:
                ABCDElement(gathering, 'AreaDetail',
                            text=utf8(collection.habitat))

            if collection.longitude or collection.latitude:
                site_coords = ABCDElement(gathering, 'SiteCoordinateSets')
                coord = ABCDElement(site_coords, 'SiteCoordinates')
                lat_long = ABCDElement(coord, 'CoordinatesLatLong')
                ABCDElement(lat_long, 'LongitudeDecimal',
                            text=utf8(collection.longitude))
                ABCDElement(lat_long, 'LatitudeDecimal',
                            text=utf8(collection.latitude))
                if collection.gps_datum:
                    ABCDElement(lat_long, 'SpatialDatum',
                                text=utf8(collection.gps_datum))
                if collection.geo_accy:
                    ABCDElement(coord, 'CoordinateErrorDistanceInMeters',
                                text=utf8(collection.geo_accy))

            if collection.elevation:
                altitude = ABCDElement(gathering, 'Altitude')
                if collection.elevation_accy:
                    text = '%sm (+/- %sm)' % (collection.elevation,
                                              collection.elevation_accy)
                else:
                    text = '%sm' % collection.elevation
                ABCDElement(altitude, 'MeasurementOrFactText', text=text)

            if collection.notes:
                ABCDElement(gathering, 'Notes', utf8(collection.notes))


class PlantABCDAdapter(AccessionABCDAdapter):
    """
    An adapter to convert a Plant to an ABCD Unit
    """
    def __init__(self, plant, for_labels=False):
        super(PlantABCDAdapter, self).__init__(plant.accession, for_labels)
        self.plant = plant


    def get_UnitID(self):
        return html.escape(str(self.plant))


    def get_DateLastEdited(self):
        return utils.html.escape(self.plant._last_updated.isoformat())


    def get_Notes(self):
        if not self.plant.notes:
            return None
        notes = []
        for note in self.plant.notes:
            notes.append(dict(date=utils.html.escape(note.date.isoformat()),
                              user=html.escape(note.user),
                              category=html.escape(note.category),
                              note=html.escape(note.note)))
        return html.escape(str(notes))


    def extra_elements(self, unit):
        bg_unit = ABCDElement(unit, 'BotanicalGardenUnit')
        ABCDElement(bg_unit, 'AccessionSpecimenNumbers',
                    text=html.escape(self.plant.quantity))
        ABCDElement(bg_unit, 'LocationInGarden',
                    text=html.escape(str(self.plant.location)))
        if self.for_labels:
            if self.taxa.label_distribution:
                etree.SubElement(unit, 'distribution').text=\
                    self.taxa.label_distribution
            elif self.taxa.distribution:
                etree.SubElement(unit, 'distribution').text=\
                    self.taxa.distribution_str()
        # TODO: AccessionStatus, AccessionMaterialtype,
        # ProvenanceCategory, AccessionLineage, DonorCategory,
        # PlantingDate, Propagation
        super(PlantABCDAdapter, self).extra_elements(unit)
