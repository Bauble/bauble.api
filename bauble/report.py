
import lxml.etree as etree
import os
import subprocess
import sys
import tempfile

import bauble.search as search
import bauble.utils as utils

def create_pdf_from_reportdef(query, reportdef):
    if reportdef.stylesheet_filename:
        return create_pdf_from_xsl(query)


#
# TODO: we need to get away from generating the abcd data before converting to
# PDF, we should just give each method an xml() serialization method
#
def create_pdf_from_xsl(query, stylesheet):
    fo_handle = out_handle = xsl_handle = None
    xsl_filename = None
    pdf = None
    try:
        if isinstance(query, str):
            results = search.search(query)
        else:
            # assume this is a SQLAlchemy query object that we can iterate for results
            results = query

        # TODO: we need to adapt the results based on the search domain or
        # query mapper, for now we just assume everything is a plany
        #source = [FamilyABCDAdapter(plant) for plant in results]
        xml_data = ''.join([obj.xml() for obj in results])
        print("xml: ", xml_data)


        # transform the xml data into an XSL-FO file
        fo_handle, fo_filename = tempfile.mkstemp()
        stylesheet_etree = etree.XML(stylesheet)
        transform = etree.XSLT(stylesheet_etree)
        fo_data = transform(etree.XML(xml_data))
        fo_outfile = os.fdopen(fo_handle, 'w')
        fo_outfile.write(str(fo_data))
        fo_outfile.flush()

        out_handle, out_filename = tempfile.mkstemp()
        xsl_handle, xsl_filename = tempfile.mkstemp()

        f = os.fdopen(xsl_handle, "w")
        f.write(stylesheet)
        f.flush()

        returncode = subprocess.call(['fop', '-fo', fo_filename, '-pdf', out_filename])
        if returncode == 0:
            raise Exception("fop returned 0")

        print("out: ", out_filename, file=sys.stderr)
        if os.path.exists(out_filename):
            pdf = open(out_filename).read()
    finally:
        if fo_handle: os.close(fo_handle)
        if xsl_handle: os.close(xsl_handle)
        if out_handle: os.close(out_handle)
        # if os.path.exists(out_filename):
        #     os.remove(out_filename)
        if xsl_filename is not None and os.path.exists(xsl_filename):
            os.remove(xsl_filename)

    return pdf


def create_pdf_from_mako(query, template):
    pass

def create_csv(query):
    pass
