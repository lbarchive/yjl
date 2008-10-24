SEARCH_RESULT_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:google="http://base.google.com/ns/1.0" xml:lang="en-US" xmlns:openSearch="http://a9.com/-/spec/opensearch/1.1/" xmlns="http://www.w3.org/2005/Atom" xmlns:twitter="http://api.twitter.com/">
  <id>tag:search.twitter.com,2005:search/twitter</id>
  <link type="text/html" href="http://search.twitter.com/search?q=twitter" rel="alternate"/>
  <link type="application/atom+xml" href="http://search.twitter.com/search.atom?q=twitter" rel="self"/>
  <title>twitter - Twitter Search</title>
  <link type="application/opensearchdescription+xml" href="http://search.twitter.com/opensearch.xml" rel="search"/>
  <link type="application/atom+xml" href="http://search.twitter.com/search.atom?q=twitter&amp;since_id=955300766" rel="refresh"/>
  <twitter:warning>adjusted since_id, it was older than allowed</twitter:warning>
  <updated>2008-10-11T09:34:37Z</updated>
  <openSearch:itemsPerPage>15</openSearch:itemsPerPage>
  <openSearch:language>en</openSearch:language>
  <link type="application/atom+xml" href="http://search.twitter.com/search.atom?max_id=955300766&amp;page=2&amp;q=twitter" rel="next"/>
  <entry>
    <id>tag:search.twitter.com,2005:955300766</id>
    <published>2008-10-11T09:34:37Z</published>
    <link type="text/html" href="http://twitter.com/livibetter/statuses/123456789" rel="alternate"/>
    <title>A twitter message</title>
    <content type="html">A &lt;b&gt;twitter&lt;/b&gt; message</content>
    <updated>2008-10-11T09:34:37Z</updated>
    <link type="image/png" href="http://s3.amazonaws.com/twitter_production/profile_images/12345678/avatar_normal.png" rel="image"/>
    <author>
      <name>livibetter</name>
      <uri>http://twitter.com/livibetter</uri>
    </author>
  </entry>
</feed>"""
