import pymysql

import logging
import warnings

class DatabaseException(Exception):
	pass

class Database:
	def __init__(self, cfg):
		self.host = cfg.sql.host
		self.port = cfg.sql.port
		self.user = cfg.sql.user
		self.passwd = cfg.sql.passwd
		self.database = cfg.sql.database
		self.table = cfg.sql.table
		self._conn = None
	
	def open(self):
		self._conn = pymysql.connect(
			host=self.host,
			port=self.port,
			user=self.user,
			password=self.passwd,
			cursorclass=pymysql.cursors.DictCursor
		)
	
	def close(self):
		self._conn.close()
	
	def sql(self, cmds):
		with self._conn.cursor() as curs:
			for cmd in cmds:
				logging.debug("SQL: {}".format(cmd))
				with warnings.catch_warnings():
					warnings.simplefilter("ignore")
					curs.execute(cmd)
		self._conn.commit()
