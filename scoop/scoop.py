"""
Podcast scoop, main module.
Copyright (c) 2018 Acke, see LICENSE file for allowable usage.
"""

import collections
import datetime
import os
import sys
import urllib.request as ur

from . import playlist
from . import rssxml
from . import sql

def openurl(url, dbfile):
    """ Return a url file pointer object. """
    agent = sql.getconfig('useragent', dbfile)['value']
    req = ur.Request(url, headers={'User-Agent': agent})
    return ur.urlopen(req)

def urlfpfilename(urlfp):
    """ Return filename from url file pointer object. """
    # Some podcast will contain items whose URLs *all* have the same filename.
    # These URLs will redirect to things that look like a filename we can use.
    urlobj = ur.urlparse(urlfp.url)
    fullpath = ur.unquote(urlobj.path)
    _, filename = os.path.split(fullpath)
    return filename

def getdestdir(dbfile, podtitle):
    return os.path.join(os.path.expanduser(sql.getconfig('downloaddir', dbfile)['value']), podtitle)

def downloadrss(rssurl, dbfile, cache=False):
    urlfp = openurl(rssurl, dbfile)
    try:
        rssxmlbytes = urlfp.read()
    finally:
        urlfp.close()
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
    # Print addition summary.
    statii = collections.Counter()
    for dl in downloads:
        statii[dl.status] += 1
    print('{}: {} new episodes ({} waiting {} skipped)'.format(podcast.title, len(episodes), statii['w'], statii['s']))

def printpodcasts(dbfile, title=None):
    podcasts = sql.getpodcasts(dbfile, title)
    for p in podcasts:
        print(p.title)

def editpodcast(dbfile, podtitle, title=None, rssurl=None):
    if any([title, rssurl]):
        podcasts = sql.getpodcasts(dbfile, podtitle)
        # Make sure that podtitle matches only one podcast before changing anything.
        np = len(podcasts)
        if np == 0:
            print('No podcasts found matching title "{}"'.format(podtitle))
        elif np == 1:
            sql.editpodcast(dbfile, podtitle, title=title, rssurl=rssurl)
            print('{}:'.format(podtitle))
            if title:
                print('title: {} -> {}'.format(podcasts[0].title, title))
                try:
                    os.rename(getdestdir(dbfile, podcasts[0].title), getdestdir(dbfile, title))
                except FileNotFoundError:
                    pass
            if rssurl:
                print('rssurl: {} -> {}'.format(podcasts[0].rssurl, rssurl))
        else:
            # np > 1
            print('More than one podcast matches title "{}", please narrow your search'.format(podtitle))
    else:
        print('Nothing to do! Supply either a new title or rssurl.')

def syncpodcasts(dbfile, title=None, limit=False):
    podcasts = sql.getpodcasts(dbfile, title)
    for p in podcasts:
        addpodcasturl(p.rssurl, dbfile, limit=limit)

def downloadepisode(dbfile, dl):
    # Download episode from dl.mediaurl > config:downloaddir/dl.podtitle/dl.mediaurl:filename
    # Ensure destdir exists.
    destdir = getdestdir(dbfile, dl.podtitle)
    os.makedirs(destdir, exist_ok=True)
    urlfp = openurl(dl.mediaurl, dbfile)
    filename = urlfpfilename(urlfp)
    fullpath = os.path.join(destdir, filename)
    try:
        with open(fullpath, 'wb') as f:
            for chunkbytes in iter(lambda: urlfp.read(0x4000), b''):
                f.write(chunkbytes)
    finally:
        urlfp.close()
    return filename

def syncdls(dbfile, updateindex=False):
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
        print('{} {:32} {}'.format(state, d.podtitle, d.eptitle))
    if updateindex and dls:
        # Update the index playlist for each podcast that had new episodes downloaded.
        indexfile = sql.getconfig('indexfile', dbfile)['value']
        for podtitle in sorted({p.podtitle for p in dls}):
            outfile = os.path.join(getdestdir(dbfile, podtitle), indexfile)
            playlist.makeplaylist(dbfile, outfile, podcasttitle=podtitle)

def getmaxpodtitlelen(lst):
    return len(max(lst, key=lambda x: len(x.podtitle)).podtitle)

def printepisodes(dbfile, podcasttitle=None, episodetitle=None):
    episodes = sql.getepisodes(dbfile, podcasttitle=podcasttitle, episodetitle=episodetitle)
    maxtitle = getmaxpodtitlelen(episodes)
    fmt = '{:<5} {:' + str(maxtitle) + '} {} {}'
    for e in episodes:
        print(fmt.format(e.episodeid, e.podtitle, datetime.date.fromtimestamp(e.pubdate), e.title))

def makedlsprintlines(dls):
    maxtitle = getmaxpodtitlelen(dls)
    fmt = '{} {:' + str(maxtitle) + '} {}'
    return (fmt.format(d.status, d.podtitle, d.eptitle) for d in dls)

def insertdls(dbfile, episodes):
    """ Insert new dl orders for each episode in episodes. """
    if episodes:
        dlorders = sql.adddownloads(episodes, dbfile, limit=False)
        print('\n'.join(makedlsprintlines(dlorders)))

def dlnewepisodes(dbfile):
    """ Adds download orders for new episodes. """
    insertdls(dbfile, sql.getnewepisodes(dbfile))

def dloldepisodes(dbfile, idlist=None, podcasttitle=None, episodetitle=None):
    """ Create dl orders for old/existing episodes. """
    episodes = sql.getepisodes(dbfile, idlist=idlist, podcasttitle=podcasttitle, episodetitle=episodetitle)
    # Remove episodes that already have outstanding 'w' dl orders.
    eids = [e.episodeid for e in episodes]
    waitingdlids = frozenset(d.episodeid for d in sql.getdls(dbfile, episodeids=eids, statelist=['w']))
    insertdls(dbfile, [e for e in episodes if e.episodeid not in waitingdlids])

def printdls(dbfile, podcasttitle=None, episodetitle=None, statelist=None, newerthan=None):
    dls = sql.getdls(dbfile, podcasttitle=podcasttitle, episodetitle=episodetitle, statelist=statelist, newerthan=newerthan)
    print('\n'.join(makedlsprintlines(dls)))

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
