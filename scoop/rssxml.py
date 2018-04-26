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
    title = chan.find('title').text
    descr = chan.find('description').text
    homepage = chan.find('link').text
    return dict(title=title, rssurl=rssurl, description=descr, homepage=homepage)

def episodedicts(root):
    # RSS podcast episode iterator.
    # podcast iter / parse rss | atom | yahoo-media | itunes etc
    chan = root.find('channel')
    for x in chan.findall('item'):
        guidnode = x.find('guid')
        guid = guidnode.text
        permalink = True if guidnode.attrib['isPermaLink'] == 'true' else False
        pubdatestr = x.find('pubDate').text
        pubdate = round(eu.parsedate_to_datetime(pubdatestr).timestamp())
        # Remove trailing whitespace/newlines (rstrip) from title and description fields.
        description = x.find('description').text.rstrip()
        title = x.find('title').text.rstrip()
        link = x.find('link').text
        medianode = x.find('enclosure')
        try:
            mediaurl = medianode.attrib['url']
        except AttributeError as e:
            # Episode does not contain media.
            mediaurl = None
            mediatype = None
            medialength = None
        else:
            mediatype = medianode.attrib['type']
            medialength = int(medianode.attrib['length'])
        ep = dict(guid=guid, permalink=permalink, title=title, description=description, mediaurl=mediaurl, mediatype=mediatype, medialength=medialength, pubdate=pubdate, link=link)
        yield ep

def getxmltree(rssxmlstr):
    root = et.fromstring(rssxmlstr)
    assert root.tag == 'rss'
    return root
