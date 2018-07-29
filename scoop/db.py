"""
Mini database connection wrapper
Copyright (c) 2018 Acke, see LICENSE file for allowable usage.
"""
import os
import sqlite3

class DB:

    def __init__(self, dbfile):
        self.filename = dbfile
        self._cursors = []
        if dbfile == ':memory:' or not os.path.exists(dbfile):
            self._createandloaddb()
        else:
            self._loaddb()

    def _loaddb(self):
        self.conn = sqlite3.connect(self.filename)
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.row_factory = sqlite3.Row

    def _loadschema(self):
        schemafile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema.sqlite')
        return open(schemafile).read()

    def _createandloaddb(self):
        """ Create the db: load in the schema and populate with default config. """
        basedir = os.path.dirname(self.filename)
        # basedir will return '' if self.filename is in the current directory.
        if basedir != '':
            os.makedirs(basedir, exist_ok=True)
        self._loaddb()
        with self as conn:
            conn.executescript(self._loadschema())
            self.commit()

    def __enter__(self):
        c = self.conn.cursor()
        self._cursors.append(c)
        return c

    def __exit__(self, exc_type, exc_val, exc_tb):
        c = self._cursors.pop()
        c.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
