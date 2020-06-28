import yaml

class ConfigException(Exception):
	pass

class Config:
	def __init__(self, fn):
		try:
			self.read(fn)
		except Exception as e:
			raise ConfigException("Couldn't parse config file '{}':\n{}".format(fn, e))
	
	def read(self, fn):
		with open(fn, "r") as fp:
			self.set(yaml.load(fp, Loader=yaml.Loader))
	
	def write(self, fn):
		with open(fn, "w") as fp:
			yaml.dump(self.dict, fp, Dumper=yaml.Dumper)
	
	def set(self, dict):
		self.dict = dict
