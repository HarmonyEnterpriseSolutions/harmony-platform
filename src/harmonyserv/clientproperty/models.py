import datetime
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import random

EXPIRE_DAYS = 31


class StorageManager(models.Manager):

	def get_storage(self, request, response):
		"""
		if response is None, 
		"""

		# remove expired storages
		Storage.objects.filter(expire_date__lt = datetime.datetime.now()).delete()

		key = request.COOKIES.get('clientpropertystorageid')

		while True:

			new_key = key is None

			if new_key:
				key = '%032x' % random.getrandbits(128)

			storage, created = self.get_or_create(key=key)

			# if no collision
			if not (new_key and not created):
				break
				
		# defer cookie expiration
		response.set_cookie(
			'clientpropertystorageid', 
			key, 
			expires = datetime.datetime.utcnow() + datetime.timedelta(EXPIRE_DAYS),
			domain  = settings.SESSION_COOKIE_DOMAIN, 
			secure  = settings.SESSION_COOKIE_SECURE or None
		)

		# defer storage expire date
		storage.expire_date = datetime.datetime.now() + datetime.timedelta(EXPIRE_DAYS)
		storage.save()

		return storage


class Storage(models.Model):

	objects = StorageManager()

	key         = models.TextField()
	expire_date = models.DateTimeField(blank=True, null=True)
	
	def __getitem__(self, key):
		try:
			prop = self.properties.get(key=key)
			try:
				return eval(prop.value, {}, {})
			except:
				prop.delete()
				print "* invalid clientproperty removed"
				raise KeyError, key
		except ObjectDoesNotExist:
			raise KeyError, key
	
	def __setitem__(self, key, value):
		if value is not None:
			prop, created = self.properties.get_or_create(key=key)
			prop.value = repr(value)
			prop.save()
		else:
			try:
				self.properties.get(key=key).delete()
			except ObjectDoesNotExist:
				pass


class Property(models.Model):

	storage = models.ForeignKey(Storage, related_name='properties')
	key     = models.TextField()
	value   = models.TextField(blank=True)

	class Meta:
		unique_together = ['storage', 'key']
