import os
import subprocess
import sys
import tempfile

def create_pdf_from_reportdef(query, reportdef):
    if reportdef.stylesheet_filename:
        return create_pdf_from_xsl(query)

def create_pdf_from_xsl(query, stylesheet):
    pdf = None
    try:
        out_handle, out_filename = tempfile.mkstemp()
        xsl_handle, xsl_filename = tempfile.mkstemp()

        f = os.fdopen(xsl_handle, "w")
        f.write(stylesheet)
        f.flush()

        returncode = subprocess.call(['fop', '-fo', xsl_filename, '-pdf', out_filename])
        if returncode == 0:
            raise Exception("fop returned 0")

        print("out: ", out_filename, file=sys.stderr)
        if os.path.exists(out_filename):
            pdf = open(out_filename).read()
    finally:
        os.close(xsl_handle)
        os.close(out_handle)
        # if os.path.exists(out_filename):
        #     os.remove(out_filename)
        os.remove(xsl_filename)

    return pdf


def create_pdf_from_mako(query, template):
    pass

def create_csv(query):
    pass
