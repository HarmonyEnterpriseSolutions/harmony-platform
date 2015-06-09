# -*- coding: UTF-8 -*-
import os
import time
import platform
import sys
import wx
from cefpython3.wx import chromectrl
from cefpython3 import cefpython

class Chrome(chromectrl.ChromeWindow):
	def __init__(self, parent, id=None):
		initialize()
		super(Chrome, self).__init__(parent)
		self.browser.SetClientHandler(ClientHandler(self))

	def setUrl(self, url):
		if url is not None:
			self.browser.Navigate(url)

	def onExit(self):
		shutdown()


_initialized = False

def initialize():
	global _initialized
	if not _initialized:	
		chromectrl.Initialize()
		_initialized = True

def shutdown():
	global _initialized
	if _initialized:
		chromectrl.Shutdown()
		_initialized = False


class AuthCredentials():
	ok = False
	ready = False

class ClientHandler(object):

	def __init__(self, window):
		self.window = window

	def GetAuthCredentials(self, browser, frame, isProxy, host, port, realm, scheme, callback):
		#rint("GetAuthCredentials: isProxy=%s, host=%s, port=%s, realm=%s, scheme=%s" % (isProxy, host, port, realm, scheme))

		credentials = AuthCredentials()
		
		def f():
			dlg = AuthCredentialsDialog(self.window.GetParent().GetParent(), isProxy, host, port, realm, scheme)
			try:
				res = dlg.ShowModal()
				if res == wx.ID_OK:
					credentials.username=dlg.username.GetValue()
					credentials.password=dlg.password.GetValue()
					credentials.ok = True
			finally:
				dlg.Destroy()
				credentials.ready = True

		wx.CallAfter(f)
		
		while not credentials.ready:
			time.sleep(0.1)
		
		if credentials.ok:
			callback.Continue(username=credentials.username, password=credentials.password)

		return credentials.ok 


	def GetCookieManager(self, browser, mainUrl):
		# Create unique cookie manager for each browser.
		# --
		# Buggy implementation in CEF, reported here:
		# https://code.google.com/p/chromiumembedded/issues/detail?id=1043
		cookieManager = browser.GetUserData("cookieManager")
		if cookieManager:
			return cookieManager
		else:
			cookieManager = cefpython.CookieManager.CreateManager("")
			if os.name == 'nt':
				from toolib.win32.shell import getSpecialFolderPath
				path = os.path.join(getSpecialFolderPath('PROFILE'), '.cefpython', 'cookies')
				cookieManager.SetStoragePath(path)

			browser.SetUserData("cookieManager", cookieManager)
			return cookieManager


class AuthCredentialsDialog(wx.Dialog):
    
	def __init__(self, parent, isProxy, host, port, realm, scheme):
		super(AuthCredentialsDialog, self).__init__(parent, title=u"Требуется аутентификация") 

		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer.AddSpacer(5)

		label = wx.StaticText(self, -1, u"Прокси «%s:%s» запрашивает имя пользователя и пароль.\nСайт сообщает: «%s»" %(host, port, realm))
		sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 10)

		box = wx.BoxSizer(wx.HORIZONTAL)

		label1 = wx.StaticText(self, -1, u"Имя пользователя:")
		box.Add(label1, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

		self.username = wx.TextCtrl(self, -1, "", size=(80,-1))
		box.Add(self.username, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		box = wx.BoxSizer(wx.HORIZONTAL)

		label2 = wx.StaticText(self, -1, u"Пароль:")
		box.Add(label2, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

		self.password = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD)
		box.Add(self.password, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		#line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		#sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

		btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.Add(btn, 0, wx.ALL, 5)

		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.Add(btn, 0, wx.ALL, 5)

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sizer.AddSpacer(5)

		self.SetSizer(sizer)
		sizer.Fit(self)

		label1.MinSize = label2.MinSize = (max(label1.BestSize[0], label2.BestSize[0]), -1)

		#self.username.SetValue('gleb.mironov')
		#self.password.SetValue('123')


        
if __name__ == '__main__':
	from toolib.wx.TestApp import TestApp

	def oninit(self):
		chromectrl.Initialize()
		self.cb = Chrome(self)
		def f():
			self.cb.setUrl('http://google.com/')
		wx.CallAfter(f)

	def ondestroy(self):
		pass

	TestApp(oninit, ondestroy).MainLoop()
	chromectrl.Shutdown()
