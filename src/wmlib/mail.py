# -*- coding: Cp1251 -*-

from toolib.text.email.EmailMessage import EmailMessage
import os
import smtplib

DEBUG = 0

def sendMessage(
		sender,
		recipients,
		cc       = None,
		bcc      = None,
		subject  = None,
		text     = None,

		data     = None,
		mimetype = None,
		filename = None,

		charset = 'windows-1251',
	):

	message = EmailMessage(
		sender,
		[i.strip() for i in recipients.split(',')] if recipients else [],
		subject,
		text,
		cc  = cc,
		bcc = bcc,
		charset = charset,
	)

	if data:
		message.attach(data, mimetype, filename)

	sendEmailMessage(message)


def sendEmailMessage(message):
	conf = {}
	from gnue.paths import config
	execfile(os.path.join(config, 'smtplib.conf.py'), {}, conf)

	if DEBUG:
		open(u'C:\\wmlib_mail.eml', 'wt').write(str(message))
		return
	
	smtp = smtplib.SMTP(**conf)
	smtp.sendmail(message.getSender(), message.getRecipients(), str(message))
	smtp.close()


if __name__ == '__main__':
	message = EmailMessage(
		'nogus@ukr.net',
		['oleg.noga@gmail.com'],
		u'Сабж',
		u'Тело\nВторая строка',
		sender='noga@ua.fm',
		cc=['nogus@mail.ru'],
		bcc=['noga@ukr.net'],
	)

	print message

	sendEmailMessage(message)
