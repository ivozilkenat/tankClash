import pygame
from PygameCollection.gameObjects import MovableSprite
from PygameCollection.math import Vector2D
from abc import ABC
from enum import Enum
from timeit import default_timer
from math import pi

# PROJECTILE-classes ---------
class Projectile(MovableSprite, ABC):
	def __init__(self, game, img, pos, *args, **kwargs):
		super().__init__(game, img, pos, *args, **kwargs)
		self.born = default_timer()
		self.lifetime = 2 # in seconds

	def hasExpired(self):
		return default_timer() - self.born > self.lifetime


class CanonBall(Projectile):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.v = 10

	def update(self):
		oldPos = self.pos
		self.pos += self.dir * self.v
		super().update()

		#todo: collision system fails calculation
		if (wall := self.game.map.hitsWall(self)):
			self.pos = oldPos
			# handle reflection -> 1.) calc norm vector 2.) compare with direction of shot 3.) combine into a new direction vector
			normVec = wall.norm
			if self.dir.enclosedAngle(normVec) > pi/2:
				normVec.toCounter()
			from PygameCollection.math import rad2deg
			v = Vector2D.fromSymReflection(self.dir, normVec)
			v.toUnitVec()
			v.toCounter()
			a, b = rad2deg(self.dir.enclosedAngle(normVec)), rad2deg(v.enclosedAngle(Vector2D.asCounterVector(normVec)))
			d = abs(a-b)
			print(a, b, d)
			# if d > 60:
			# 	print(wall.start, wall.end)
			# 	quit()
			self.dir = v

# AMMO-classes ---------
class Ammunition:
	def __init__(self, ammoClass, shotInterval, shotMaximum, lifetime=None, img=None):
		assert issubclass(ammoClass, Projectile)
		self.ammoClass = ammoClass
		self.lifetime = lifetime
		self.img = img

		self.shotInterval = shotInterval
		self.lastShot = None
		self.shotMaximum = shotMaximum
		self.activeShots = set()

	# respects the shotMaximum
	def tryGetBullet(self, game, pos, *args, **kwargs):
		if len(self.activeShots) >= self.shotMaximum:
			return
		elif self.lastShot is not None and default_timer()-self.lastShot < self.shotInterval:
			return
		return self.forceGetBullet(game, pos, *args, **kwargs)

	def forceGetBullet(self, game, pos, *args, **kwargs):
		b = self.ammoClass(game, self.img, pos, *args, **kwargs)
		self.lastShot = default_timer()
		if self.lifetime is not None:
			b.lifetime = self.lifetime
		self.activeShots.add(b)
		return b

	def kill(self, projectile):
		self.activeShots.remove(projectile)

	# convenience method
	@classmethod
	def getAmmo(cls, ammoType):
		return AmmoType.getInstanceOf(ammoType)

class AmmoTypeData:
	def __init__(self, ammoClass, shotInterval, shotMaximum, lifetime=None, img=None):
		self.ammoClass = ammoClass
		self.shotInterval = shotInterval
		self.shotMaximum = shotMaximum
		self.lifetime = lifetime
		self.img = img

	def getAmmo(self):
		assert self.img is not None, "'img' attribute must be set"
		return Ammunition(self.ammoClass, self.shotInterval, self.shotMaximum, self.lifetime, self.img)

class AmmoType(Enum):
	NORMAL = AmmoTypeData(CanonBall, shotInterval=0.1, shotMaximum=100, lifetime=10)

	@classmethod
	def getInstanceOf(cls, ammoType):
		assert isinstance(ammoType, AmmoType)
		return ammoType.value.getAmmo()

	@classmethod
	def equals(cls, ammunition, ammoType):
		assert isinstance(ammunition, Ammunition)
		assert isinstance(ammoType, AmmoType)
		return ammunition.ammoClass == ammoType.value.ammoClass

	@classmethod
	def setImage(cls, ammoType, img):
		assert isinstance(ammoType, AmmoType)
		assert isinstance(img, pygame.Surface)
		ammoType.value.img = img