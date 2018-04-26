""" Podcast scoop, main module. """

import datetime
import os
import sys
import urllib.request as ur

from . import rssxml
from . import sql

# dl podcast file
def downloadurl(url, dbfile):
    agent = sql.getconfig('useragent', dbfile)['value']
    req = ur.Request(url, headers={'User-Agent': agent})
    with ur.urlopen(req) as f:
        # TODO write this to a file as it's being downloaded. Some of these media files are pretty large...
        contentbytes = f.read()
        # Some podcast will contain items whose URLs *all* have the same filename.
        # These URLs will redirect to things that look like a filename we can use.
        urlobj = ur.urlparse(f.url)
        fullpath = ur.unquote(urlobj.path)
        _, filename = os.path.split(fullpath)
    return contentbytes, filename

def downloadrss(rssurl, dbfile, cache=False):
    rssxmlbytes, _ = downloadurl(rssurl, dbfile)
    # Cache rssxmlbytes to file if config.saverss = True
    if cache:
        poddict = rssxml.podcastdict(rssxml.getxmltree(rssxmlbytes), rssurl)
        destdir = os.path.expanduser(sql.getconfig('downloaddir', dbfile)['value'])
        os.makedirs(destdir, exist_ok=True)
        rssfile = os.path.join(destdir, '{}.rss'.format(poddict['title']))
        with open(rssfile, 'w') as f:
            f.write(str(rssxmlbytes, 'utf-8'))
    return rssxml.getxmltree(rssxmlbytes)

def addpodcasturl(rssurl, dbfile, limit=False):
    """ Adds a new podcast from network URL to track.
    Also add all the podcast episodes, as well as download items for 'limit' number of the newest episodes. """
    root = downloadrss(rssurl, dbfile, cache=sql.getconfig('saverss', dbfile)['value'])
    podcast = sql.addpodcast(rssxml.podcastdict(root, rssurl), dbfile)
    # Insert podcast episodes.
    episodes = sql.addepisodes(podcast, rssxml.episodedicts(root), dbfile)
    # Create dl orders for episodes.
    downloads = sql.adddownloads(episodes, dbfile, limit)

def printpodcasts(dbfile, title=None):
    podcasts = sql.getpodcasts(dbfile, title)
    for p in podcasts:
        print(p.title)

def editpodcast(dbfile, podtitle, title=None, rssurl=None):
    if any([title, rssurl]):
        sql.editpodcast(dbfile, podtitle, title=title, rssurl=rssurl)
        printpodcasts(dbfile, title)
    else:
        print('Nothing to do! Supply either a new title or rssurl.')

def syncpodcasts(dbfile, title=None, limit=False):
    podcasts = sql.getpodcasts(dbfile, title)
    for p in podcasts:
        addpodcasturl(p.rssurl, dbfile, limit=limit)

def downloadepisode(dbfile, dl):
    # Download episode from dl.mediaurl > config:downloaddir/dl.podtitle/dl.mediaurl:filename
    # Ensure destdir exists.
    destdir = os.path.join(os.path.expanduser(sql.getconfig('downloaddir', dbfile)['value']), dl.podtitle)
    os.makedirs(destdir, exist_ok=True)
    contentbytes, filename = downloadurl(dl.mediaurl, dbfile)
    fullpath = os.path.join(destdir, filename)
    # TODO test fullpath exists and size == episode.mediasize.
    # TODO update dl entry with progress?
    with open(fullpath, 'wb') as f:
        f.write(contentbytes)
    return filename

def syncdls(dbfile):
    dls = sql.getdls(dbfile, statelist=['w'])
    for d in dls:
        try:
            filename = downloadepisode(dbfile, d)
        except Exception as e:
            # Mark download failed.
            state = 'e'
            print(str(e), file=sys.stderr)
            filename = None
        else:
            # Download success.
            state = 'd'
        sql.markdl(dbfile, d, state, filename)
        print('{:<5} {} {:32} {}'.format(d.dlid, state, d.podtitle, d.eptitle))

def printepisodes(dbfile, podcasttitle=None, episodetitle=None):
    episodes = sql.getepisodes(dbfile, podcasttitle=podcasttitle, episodetitle=episodetitle)
    for e in episodes:
        print('{:<5} {:32} {} {}'.format(e.episodeid, e.podtitle, datetime.date.fromtimestamp(e.pubdate), e.title))

def dlnewepisodes(dbfile):
    """ Adds download orders for new episodes. """
    newepisodes = sql.getnewepisodes(dbfile)
    if newepisodes:
        dlorders = sql.adddownloads(newepisodes, dbfile, limit=False)
        for d in dlorders:
            print('{:<5} {} {:16} {}'.format(d.episodeid, d.status, d.podtitle, d.eptitle))

def printdls(dbfile, podcasttitle=None, episodetitle=None):
    dls = sql.getdls(dbfile, podcasttitle=podcasttitle, episodetitle=episodetitle)
    for d in dls:
        filename = '' if d.filename is None else d.filename
        print('{:<5} {} {:16} {:16} {}'.format(d.dlid, d.status, d.podtitle, filename, d.eptitle))

def init(dbfile):
    sql.init(dbfile)

def printallconfig(dbfile):
    for row in sql.getallconfig(dbfile):
        print('{:16} {:16} {}'.format(row['key'], row['value'], row['description']))

def printconfig(key, dbfile):
    row = sql.getconfig(key, dbfile)
    print('{:16} {}'.format(key, row['value']))

def setconfig(key, value, dbfile):
    sql.setconfig(key, value, dbfile)
