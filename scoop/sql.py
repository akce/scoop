"""
Scoop SQL commands.
Copyright (c) 2018 Acke, see LICENSE file for allowable usage.
"""
import collections
import os
import time

def makeinsertquery(query, columns):
    return query.format(','.join(columns), ','.join(':{}'.format(x) for x in columns))

podcols = ['podcastid', 'title', 'rssurl', 'description', 'homepage', 'stopped']
addpodsql = makeinsertquery('''INSERT OR IGNORE INTO
podcast ({})
VALUES ({});''', podcols)

epcols = ['episodeid', 'podcastid', 'guid', 'permalink', 'mediaurl', 'mediatype', 'medialength', 'title', 'description', 'link', 'pubdate']
addepsql = makeinsertquery('''INSERT OR IGNORE INTO
episode ({})
VALUES ({});''', epcols)

dlcols = ['dlid', 'episodeid', 'status', 'added', 'actioned', 'filename']
adddlsql = makeinsertquery('''INSERT OR IGNORE INTO
dl ({})
VALUES ({});''', dlcols)

class Data:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class Podcast(Data):
    pass

class Episode(Data):
    pass

class Download(Data):
    pass

def getallconfig(db):
    with db as conn:
        curs = conn.execute('SELECT * FROM config')
        return curs.fetchall()

def getconfig(db, field):
    with db as conn:
        curs = conn.execute('SELECT value, description FROM config WHERE key = ?', (field,))
        return curs.fetchone()

def setconfig(db, field, value):
    with db as conn:
        curs = conn.execute('UPDATE config SET value = ? WHERE key = ?', (value, field,))
        db.commit()

def addpodcast(db, poddict, stopped=None):
    """ Adds a new podcast to the database, returns the new podcast object. """
    global addpodsql
    with db as conn:
        poddict['podcastid'] = None
        poddict['stopped'] = stopped
        cursor = conn.execute(addpodsql, poddict)
        if cursor.rowcount == 0:
            podcast = getpodcastbyrssurl(poddict['rssurl'], conn=conn)
        else:
            poddict['podcastid'] = cursor.lastrowid
            db.commit()
            podcast = Podcast(**poddict)
    return podcast

def getpodcastbyrssurl(rssurl, conn):
    curs = conn.execute('SELECT * FROM podcast WHERE rssurl = ?', (rssurl,))
    return Podcast(**curs.fetchone())

def getpodcasts(db, title=None):
    basequery = 'SELECT * FROM podcast'
    order = ' ORDER BY title'
    if title:
        query = basequery + " WHERE title LIKE ?" + order
        value = ('%{}%'.format(title),)
    else:
        query = basequery + order
        value = ()
    podcasts = []
    with db as conn:
        curs = conn.execute(query, value)
        for row in curs.fetchall():
            podcasts.append(Podcast(**row))
    return podcasts

def editpodcast(db, podcasttitle, title=None, rssurl=None, stopped=None):
    basequery = ['UPDATE podcast SET']
    setvalues = []
    values = []
    if title:
        setvalues.append('title = ?')
        values.append(title)
    if rssurl:
        setvalues.append('rssurl = ?')
        values.append(rssurl)
    if stopped is not None:
        setvalues.append('stopped = ?')
        if stopped:
            val = int(time.time())
        else:
            val = None
        values.append(val)
    whereelems = ['WHERE title LIKE ?']
    values.append('%{}%'.format(podcasttitle))
    query = ' '.join(basequery + [', '.join(setvalues)] + whereelems)
    with db as conn:
        conn.execute(query, values)
        db.commit()

def getepisodes(db, idlist=None, podcasttitle=None, episodetitle=None):
    queryelems = ['SELECT p.title as podtitle, e.* FROM episode as e JOIN podcast as p on e.podcastid = p.podcastid']
    order = 'ORDER BY podtitle, e.pubdate'
    where = []
    value = []
    if idlist:
        where.append('e.episodeid IN ({})'.format(('?,' * len(idlist))[:-1]))
        value.extend(idlist)
    if podcasttitle:
        where.append('p.title LIKE ?')
        value.append('%{}%'.format(podcasttitle))
    if episodetitle:
        where.append('e.title LIKE ?')
        value.append('%{}%'.format(episodetitle))
    # Build the query.
    if where:
        queryelems.append('WHERE')
        queryelems.append(' AND '.join(where))
    queryelems.append(order)
    query = ' '.join(queryelems)
    episodes = []
    with db as conn:
        curs = conn.execute(query, value)
        for row in curs.fetchall():
            episodes.append(Episode(**row))
    return episodes

def getnewepisodes(db):
    """ Return all episodes that have no download orders. """
    queryelems = ['SELECT e.episodeid, p.title as podtitle, e.pubdate, e.title FROM episode as e JOIN podcast as p USING(podcastid) LEFT JOIN dl ON e.episodeid = dl.episodeid']
    order = 'ORDER BY p.title, e.pubdate'
    # This subquery ensures that we don't include any entries that have already been actioned.
    where = ['(dl.episodeid NOT IN (SELECT x.episodeid FROM dl x WHERE x.status IS NOT NULL) OR dl.status IS NULL)']
    value = []
    # Build the query.
    if where:
        queryelems.append('WHERE')
        queryelems.append(' AND '.join(where))
    queryelems.append(order)
    query = ' '.join(queryelems)
    episodes = []
    with db as conn:
        curs = conn.execute(query, value)
        for row in curs.fetchall():
            episodes.append(Episode(**row))
    return episodes

def getdls(db, podcasttitle=None, episodetitle=None, episodeids=None, statelist=None, newerthan=None):
    queryelems = ['SELECT p.title as podtitle, e.title as eptitle, e.mediaurl, d.* FROM episode as e JOIN podcast as p USING(podcastid) JOIN dl as d USING(episodeid)']
    order = 'ORDER BY podtitle, e.pubdate'
    where = []
    value = []
    if podcasttitle:
        where.append('p.title LIKE ?')
        value.append('%{}%'.format(podcasttitle))
    if episodetitle:
        where.append('e.title LIKE ?')
        value.append('%{}%'.format(episodetitle))
    if episodeids:
        where.append('e.episodeid IN ({})'.format(('?,' * len(episodeids))[:-1]))
        value.extend(episodeids)
    if statelist:
        where.append('d.status IN (?)')
        value.append(','.join(statelist))
    if newerthan is not None:
        where.append('d.actioned > ?')
        value.append(newerthan)
    # Build the query.
    if where:
        queryelems.append('WHERE')
        queryelems.append(' AND '.join(where))
    queryelems.append(order)
    query = ' '.join(queryelems)
    dls = []
    with db as conn:
        curs = conn.execute(query, value)
        for row in curs.fetchall():
            dls.append(Download(**row))
    return dls

def markdl(db, dl, state, filename):
    with db as conn:
        conn.execute('UPDATE dl SET status = ?, actioned = ?, filename = ? WHERE dlid = ?', (state, int(time.time()), filename, dl.dlid))
        db.commit()

def addepisodes(db, podcast, episodedicts):
    global addepsql
    newepisodes = []
    with db as conn:
        for ep in episodedicts:
            ep['episodeid'] = None
            ep['podcastid'] = podcast.podcastid
            cursor = conn.execute(addepsql, ep)
            if cursor.rowcount == 0:
                # Assume we've hit episodes that we've already entered.
                break
            ep['episodeid'] = cursor.lastrowid
            ep['podtitle'] = podcast.title
            newepisodes.append(Episode(**ep))
        if newepisodes:
            db.commit()
    return newepisodes

def adddownloads(db, episodes, limit):
    global adddlsql
    newdownloads = []
    with db as conn:
        counter = collections.Counter()
        # SKIPPED is only for the initial import so podcasts with long history aren't fully downloaded.
        skippods = set()
        for ep in episodes:
            added = int(time.time())
            actioned = None
            # Downloads only apply to media episodes so automatically skip non-media items, at least until
            # we provide some kind of action (eg, send-email) for non-media types.
            if ep.mediaurl is None:
                state = 's'
            elif limit is False:
                # Always add a download order.
                state = 'w'
            else:
                # Limit is set to a number of episodes per podcast. Add waiting orders, otherwise skip.
                if ep.podtitle in skippods:
                    continue
                counter[ep.podtitle] += 1
                if counter[ep.podtitle] <= limit:
                    state = 'w'
                else:
                    state = 's'
            if state == 's':
                # SKIPPED is an end state so we'll set actioned to the order creation time.
                actioned = added
            # Insert a download workorder for the new episode.
            dl = {'dlid': None, 'episodeid': ep.episodeid, 'status': state, 'added': added, 'actioned': actioned, 'filename': None}
            cursor = conn.execute(adddlsql, dl)
            dl['dlid'] = cursor.lastrowid
            # And add some useful fields for printing.
            dl['podtitle'] = ep.podtitle
            dl['eptitle'] = ep.title
            newdownloads.append(Download(**dl))
        if newdownloads:
            db.commit()
    return newdownloads
