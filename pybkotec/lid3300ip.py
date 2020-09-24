from pybkotec import version, homedir
from pybkotec.config import Config
from pybkotec.database import Database
from pybkotec.device import Device, DeviceException

import serial

import argparse
import asyncio
from datetime import datetime
import logging
import os
import sys
import time

_name = "LID-3300IP"
_versionMsg = """{} {}

Copyright (C) 2020 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(_name, version)

class LID3300IPException(DeviceException):
	pass

class LID3300IPConfig(Config):
	def set(self, dict):
		super().set(dict)
		self.args = None
		self.ser = type("SerialParam", (object,), {
			"port": dict["ser_port"]
		})
		self.sql = type("SQLParam", (object,), {
			"host": dict["sql_host"],
			"port": dict["sql_port"],
			"user": dict["sql_user"],
			"passwd": dict["sql_passwd"],
			"database": dict["sql_database"],
			"table": dict["sql_table"]
		})
		self.meas = type("MeasurementParam", (object,), {
			"interval": dict["meas_interval"]
		})

class LID3300IPDatabase(Database):
	def open(self):
		super().open()
		cmd = "CREATE DATABASE IF NOT EXISTS `{}`".format(self.database)
		self.sql([cmd])
		cmd = createTableFmt = ""\
			"CREATE TABLE IF NOT EXISTS `{}`.`{}` ("\
			"ID INT UNSIGNED NOT NULL AUTO_INCREMENT,"\
			"DateTime DATETIME NOT NULL,"\
			"TempSensor FLOAT NOT NULL,"\
			"TempOut FLOAT NOT NULL,"\
			"Ice TINYINT UNSIGNED NOT NULL,"\
			"Mode TINYINT UNSIGNED NOT NULL,"\
			"Fail TINYINT UNSIGNED NOT NULL,"\
			"PRIMARY KEY (ID)"\
			")".format(self.database, self.table)
		self.sql([cmd])
	
	def insert(self, meas):
		cmd = "INSERT INTO `{}`.`{}` (ID, DateTime, TempSensor, TempOut, Ice, Mode, Fail) VALUES (NULL, \"{}\", {}, {}, {}, {}, {})".format(
			self.database, self.table,
			meas["DateTime"].strftime("%Y-%m-%d %H:%M:%S"),
			meas["TempSensor"],
			meas["TempOut"],
			meas["Ice"],
			meas["Mode"],
			meas["Fail"],
		)
		self.sql([cmd])

class LID3300IP(Device):
	def __init__(self, cfg):
		super().__init__(name=_name, cfg=cfg, delay=0.0)
		self._ser = None
		self._db = LID3300IPDatabase(cfg)
		self._timeNext = None
	
	async def _read(self):
		t = time.time()
		while not self._ser.in_waiting:
			if time.time() - t > self._ser.timeout:
				raise TimeoutError()
			await asyncio.sleep(0.050)
		try:
			data = self._ser.read_until(b"\n\r")
			logging.debug("Read: {}".format(data))
			parts = data.decode("ascii").rstrip().split(" ", 3)
			meas = {
				"Fail": int(parts[0][0].upper(), 16),
				"Mode": int(parts[0][1].upper(), 16),
				"TempSensor": float(parts[1]),
				"TempOut": float(parts[2]),
				"Ice": int(parts[3][1:]),
				"DateTime": datetime.utcnow()
			}
		except:
			raise ValueError()
		return meas
	
	async def _connected(self):
		try:
			await self._read()
		except:
			return False
		return True
	
	async def _connect(self):
		if self._ser is not None:
			self._ser.close()
		self._ser = serial.Serial()
		self._ser.port = self.cfg.ser.port
		self._ser.baudrate = 2400
		self._ser.bytesize = serial.EIGHTBITS
		self._ser.parity = serial.PARITY_NONE
		self._ser.stopbits = serial.STOPBITS_ONE
		self._ser.timeout = 5.0
		self._ser.open()
		return await self._connected()
	
	def _resetTime(self):
		i = self.cfg.meas.interval
		now = int(time.time())
		self._timeNext = now // i * i + i if i > 0 else now
	
	async def init(self):
		if not await self._connect():
			return False
		logging.info("Sensor port {}".format(self.cfg.ser.port))
		
		self._db.open()
		logging.info("Database {}:{}/{}.{}".format(self.cfg.sql.host, self.cfg.sql.port, self.cfg.sql.database, self.cfg.sql.table))
		
		self._resetTime()
		logging.info("Start time {}".format(datetime.fromtimestamp(self._timeNext).strftime("%H:%M:%S")))
		return True
	
	async def close(self):
		self._ser.close()
	
	async def _reconnect(self, n):
		for i in range(1, n+1):
			logging.info("Reconnect attempt {}/{}".format(i, n))
			if await self._connect():
				return True
			await asyncio.sleep(60)
		return False
	
	async def cycle(self):
		try:
			meas = await self._read()
		except TimeoutError:
			# Try to reconnect
			logging.error("Timeout reached")
			if not await self._reconnect():
				raise LID3300IPException("No connection")
			self._resetTime()
			return True
		except ValueError:
			# Try to clear the input buffer
			logging.error("Invalid data")
			self._ser.reset_input_buffer()
			self._resetTime()
			return True
		
		if time.time() >= self._timeNext:
			self._db.insert(meas)
			logging.info("[{}] {}°C, {}*".format(
				meas["DateTime"].strftime("%H:%M:%S"),
				meas["TempOut"], meas["Ice"]
			))
			self._timeNext += self.cfg.meas.interval
		return True

def parseArgs():
	parser = argparse.ArgumentParser(_name)
	parser.add_argument("cfg", nargs="?", default=os.path.join(homedir, "lid-3300ip.yaml"), help="config file", metavar="str")
	parser.add_argument("-d", "--debug", action="store_true", help="enable debug messages")
	parser.add_argument("-V", "--version", action="store_true", help="print version information")
	return parser.parse_args()

def initLogging(level):
	root = logging.getLogger()
	root.setLevel(level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(level)
	formatter = logging.Formatter(
		"[%(asctime)s](%(levelname)s) %(message)s",
		datefmt="%H:%M:%S"
	)
	ch.setFormatter(formatter)
	root.addHandler(ch)

def main():
	args = parseArgs()
	if args.version:
		sys.stdout.write(_versionMsg)
		sys.exit(0)
	initLogging(logging.DEBUG if args.debug else logging.INFO)
	
	try:
		cfg = LID3300IPConfig(args.cfg)
		cfg.args = args
		device = LID3300IP(cfg)
		device.start()
	except KeyboardInterrupt:
		logging.info("Exiting")
	except Exception as e:
		logging.critical("{}: {}".format(e.__class__.__name__, e))
