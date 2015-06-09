from django.db import models

# Create your models here.


class UserContext(object):

	def __init__(self, user_id):
		self._user_id = user_id

	def setUserConfigValue(self, key, value):
		o, created = UserConfig.objects.get_or_create(user_id=self._user_id, key=key)
		o.value = repr(value)
		o.save()
		
	def getUserConfigValue(self, key):
		try:
			return eval(UserConfig.objects.get(user_id=self._user_id, key=key).value, {}, {})
		except UserConfig.DoesNotExist:
			return None


class UserConfig(models.Model):
	user_id = models.IntegerField()
	key = models.TextField()
	value = models.TextField(blank=True)

	class Meta:
		unique_together = ['user_id', 'key']
