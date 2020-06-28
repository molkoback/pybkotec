import asyncio

class DeviceException(Exception):
	pass

class Device:
	def __init__(self, **kwargs):
		self.name = kwargs.get("name")
		self.cfg = kwargs.get("cfg")
		self.delay = kwargs.get("delay")
		self._quit = asyncio.Event()
	
	async def run(self):
		if await self.init():
			while not self._quit.is_set() and await self.cycle():
				await asyncio.sleep(self.delay)
			await self.close()
	
	def start(self):
		asyncio.get_event_loop().run_until_complete(self.run())
	
	def stop(self):
		self._quit.set()
	
	async def init(self) -> bool:
		return True
	
	async def close(self) -> None:
		pass
	
	async def cycle(self) -> bool:
		return False
