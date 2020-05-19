"""
RSS/XML parser module.
Copyright (c) 2018 Acke, see LICENSE file for allowable usage.

RSS 2.0 Spec:
https://cyber.harvard.edu/rss/rss.html
ATOM Spec:
http://tools.ietf.org/html/rfc4287
"""
# Python standard modules.
import email.utils as eu
import xml.etree.ElementTree as et

# Local modules.

## XML Namespaces used for RSS.
xmlns = {
    'atom':	"http://www.w3.org/2005/Atom",
    'itunes':	"http://www.itunes.com/dtds/podcast-1.0.dtd",
    'media':	"http://search.yahoo.com/mrss/",
    }

def podcastdict(root, rssurl):
    """ Create a podcast dict from rss xml. """
    # rss.channel.title
    chan = root.find('channel')
    # The 3 elements below are required for RSS channels so not checking for now.
    title = chan.find('title').text
    descr = chan.find('description').text
    homepage = chan.find('link').text
    return dict(title=title, rssurl=rssurl, description=descr, homepage=homepage)

def episodedicts(root):
    # RSS podcast episode iterator.
    # podcast iter / parse rss | atom | yahoo-media | itunes etc
    chan = root.find('channel')
    for x in chan.findall('item'):
        # All elements of an 'item' are optional, but there must be at least one of 'title' or 'description'.
        # Remove trailing whitespace/newlines (rstrip) from title and description fields.
        try:
            title = x.find('title').text.rstrip()
        except AttributeError:
            title = None
        try:
            description = x.find('description').text.rstrip()
        except AttributeError:
            description = None
        if not any([title, description]):
            # Invalid, skip item.
            continue
        guidnode = x.find('guid')
        try:
            guid = guidnode.text
            permalink = True if guidnode.attrib['isPermaLink'] == 'true' else False
        except AttributeError:
            guid = None
            permalink = None
        try:
            pubdatestr = x.find('pubDate').text
        except AttributeError:
            pubdate = None
        else:
            pubdate = round(eu.parsedate_to_datetime(pubdatestr).timestamp())
        try:
            link = x.find('link').text
        except AttributeError:
            link = None
        medianode = x.find('enclosure')
        try:
            mediaurl = medianode.attrib['url']
        except AttributeError as e:
            # Episode does not contain media.
            mediaurl = None
            mediatype = None
            medialength = None
        else:
            # RSS2.0 specifies that enclosure has 3 required attributes: url, type, and length.
            # They're not always provided though. eg, length in "Bludging on the Blindside"!
            # So make them optional.
            mediatype = medianode.attrib.get('type', None)
            medialength = int(medianode.attrib.get('length', -1))
        ep = dict(guid=guid, permalink=permalink, title=title, description=description, mediaurl=mediaurl, mediatype=mediatype, medialength=medialength, pubdate=pubdate, link=link)
        yield ep

def getxmltree(rssxmlstr):
    root = et.fromstring(rssxmlstr)
    assert root.tag == 'rss'
    return root
