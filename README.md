# Scoop

Scoop is a simple podcast downloader that follows rss feeds, retrieving new episodes as they become available.
It works by downloading RSS files, finding new episodes and adding download orders. New download orders then need to be downloaded.

## Dependencies

So far, only python3.

## Installing

Scoop needs a manual install, at least until a setup.py or similar is created.

For now, manually add the path to bin/scoop in your shell. eg, for sh-like shells with a scoop repository at ~/src/scoop:
```
export PATH=${PATH}:~/src/scoop/bin
```

And add the scoop module to python's modules list.
```
export PYTHONPATH=${PYTHONPATH}:~/src/scoop
```

## Quick start

Clone the repository.

```
$ git clone https://github.com/akce/scoop.git
```

Install path and python module path for your shell.
Scoop is run entirely from the command line. Show help:
```
$ scoop -h
```
And for subcommands. eg, for *podcast*:
```
$ scoop podcast --help
```

Initialise the scoop database. Scoop uses one sqlite db to track config and rss feeds.

```
$ scoop init
```

The default database location is *~/.scoop.db*.

Review and adjust configuration settings. To print all settings:
```
$ scoop config
```

To change download directory from *~/scoop*
```
$ scoop config set downloaddir '~/podcasts'
```

Add podcasts. Scoop will automatically generate download orders for all new episodes discovered for a podcast. This can be limited to a set amount by using the *--limit* argument.

Given an url for an rss, say RSSURL, add the podcast and limit downloads to the 3 newest episodes:
```
$ scoop podcast add --limit 3 RSSURL
```

To review or list podcasts:
```
$ scoop podcast ls
```

To list download orders:
```
$ scoop dl ls
```
Those that are *w*aiting for download will have a 'w' in the second column.

To download waiting episodes:
```
$ scoop dl get
```

Now that the podcasts' RSS feeds have been added, grabbing new episodes is only a matter of syncing the RSS feeds and then downloading the new work orders.

eg, To sync all tracked podcasts and generate download orders for each new episode:

```
$ scoop podcast sync
```

Then download new episodes:
```
$ scoop dl get
```

## Generating playlists

Scoop allows for generating m3u playlists based on any combination of podcast title, episode title, or download age.

### Create a playlist of todays downloads

```
$ scoop listgen --newerthan 0 today.m3u
```

### Create a playlist of all downloads for a podcast
```
$ scoop listgen --podcast podcastname podcastname.m3u
```
