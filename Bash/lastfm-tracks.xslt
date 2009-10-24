<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" disable-output-escaping="yes"/>

<xsl:template match="/">
	<xsl:for-each select="*/track">
		<xsl:value-of select="name"/>
		<xsl:if test="not(position()=last())">, </xsl:if>
	</xsl:for-each>
</xsl:template>

</xsl:stylesheet>
