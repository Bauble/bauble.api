
import lxml.etree as etree
import os
import subprocess
import sys
import tempfile

import bauble.search as search
import bauble.utils as utils

def create_pdf_from_reportdef(query, reportdef):
    if reportdef.template_type == "mako":
        return create_mako_report(query, reportdef.template)
    elif reportdef.template_type == "xsl":
        return create_xsl_report(query, reportdef.template)
    elif reportdef.template_type == "csv":
        return create_csv_report(query)
    elif reportdef.template_type == "json":
        return create_json_report(query)
    else:
        raise ValueError("unknown template type: ", reportdef.template_type)



def create_xsl_report(query, stylesheet):
    fo_handle = out_handle = xsl_handle = None
    xsl_filename = None
    pdf = None
    try:
        if isinstance(query, str):
            results = search.search(query)
        else:
            # assume this is a SQLAlchemy query object that we can iterate for results
            results = query

        xml_data = ''.join([obj.xml() for obj in results])

        # transform the xml data into an XSL-FO file
        fo_handle, fo_filename = tempfile.mkstemp()
        stylesheet_etree = etree.XML(stylesheet)
        transform = etree.XSLT(stylesheet_etree)
        fo_data = transform(etree.XML(xml_data))
        fo_outfile = os.fdopen(fo_handle, 'w')
        fo_outfile.write(str(fo_data))
        fo_outfile.flush()

        pdf_handle, pdf_filename = tempfile.mkstemp()
        xsl_handle, xsl_filename = tempfile.mkstemp()

        # write the stylesheet to a file
        f = os.fdopen(xsl_handle, "w")
        f.write(stylesheet)
        f.flush()

        # run the FO file through FOP to create the PDF
        returncode = subprocess.call(['fop', '-fo', fo_filename, '-pdf', pdf_filename])
        if returncode != 0:
            raise Exception("Apache FOP returned ", returncode)

        if os.path.exists(pdf_filename):
            pdf = open(pdf_filename, "rb").read()
    finally:
        if fo_handle: os.close(fo_handle)
        if xsl_handle: os.close(xsl_handle)
        if pdf_handle: os.close(pdf_handle)
        if pdf_filename is not None and os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        if xsl_filename is not None and os.path.exists(xsl_filename):
            os.remove(xsl_filename)

    return pdf


def create_mako_report(query, template):
    pass


def create_csv_report(query):
    pass

def create_json_report(query):
    passp
