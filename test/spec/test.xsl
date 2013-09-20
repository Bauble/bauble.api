<?xml version="1.0" ?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:fo="http://www.w3.org/1999/XSL/Format"
		version="1.0">

  <xsl:template match="/">

    <fo:root xmlns:fo="http://www.w3.org/1999/XSL/Format">
      <fo:layout-master-set>
	<fo:simple-page-master master-name="letter"
			       page-height="8.5in"
			       page-width="11in"
			       margin-top="0.5in"
			       margin-bottom="0.5in"
			       margin-left="0.5in"
			       margin-right="0.5in">
	  <fo:region-body column-count="2" column-gap="0" />
	</fo:simple-page-master>
      </fo:layout-master-set>

      <fo:page-sequence master-reference="letter">
        <xsl:for-each select=".//family">
	<fo:flow flow-name="xsl-region-body">
          
	  
            <fo:block-container>
            <fo:block>
	      <xsl:value-of select=".//field[@name='family']" />
	    </fo:block>
            </fo:block-container>
	  
          
	</fo:flow>
        </xsl:for-each>
      </fo:page-sequence>
    </fo:root>

  </xsl:template>
</xsl:stylesheet>
