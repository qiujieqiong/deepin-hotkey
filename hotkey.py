#!/usr/bin/env python
#encoding:utf-8

import subprocess
import os
import sys
import time
import dbus
import unittest
import wnck
import gtk
from Xlib import X,display
from pymouse import PyMouse
from pykeyboard import PyKeyboard

m = PyMouse()
k = PyKeyboard()

def sendSingleKey(key):
	k.press_key(key)
	k.release_key(key)

def sendMutiKeys(*keys):
	for key in keys:
		k.press_key(key)
	for key in reversed(keys):
		k.release_key(key)

def typewrite(char_string):
	k.type_string(char_string, interval=0.25)

class Window:
	def __init__(self, display):
		self.d = display
		self.root = self.d.screen().root
		self.root.change_attributes(event_mask = X.SubstructureNotifyMask)

	def loop(self):
		window_changed = False
		while True:
			event = self.d.next_event()
			if event.type == X.MapNotify:
				window_changed = True
				break

		return window_changed

def get_active_window_name():
	winName = subprocess.check_output(["xdotool getactivewindow getwindowname"],shell=True).decode().split("\n")
	winName = [ n for n in winName if len(n.strip()) > 0]
	winName = ''.join(winName)
	return winName

def get_output(cmd):
	output = subprocess.check_output([cmd],shell=True).decode().split("\n")
	output = [ n for n in output if len(n.strip()) > 0]
	output = ''.join(output)
	return output

def get_language():
	lang = os.environ["LANGUAGE"]
	return lang

def get_window_infos():
	xid_name = []
	screen = wnck.screen_get_default()
	while gtk.events_pending():
		gtk.main_iteration()

	for window in screen.get_windows():
		xid = window.get_xid()
		name = window.get_name()
		x_n = "%d %s" % (xid,name)
		xid_name.append(x_n)
	return xid_name

def get_window_names():
	names = []
	screen = wnck.screen_get_default()
	while gtk.events_pending():
		gtk.main_iteration()

	for window in screen.get_windows():
		name = window.get_name()
		names.append(name)
	return names

def get_window_max(name):
	screen = wnck.screen_get_default()
	while gtk.events_pending():
		gtk.main_iteration()

	for window in screen.get_windows():
		if name == window.get_name():
			return window.is_maximized()

def get_window_geometry(name):
	screen = wnck.screen_get_default()
	while gtk.events_pending():
		gtk.main_iteration()

	for window in screen.get_windows():
		if name == window.get_name():
			return window.get_geometry()

def get_diff_from_oldApp(old_apps):

	if Window(display.Display()).loop():
		new_apps = get_window_infos()
		if (len(new_apps) > len(old_apps)):
			print "new_apps: ", new_apps
			new_apps = get_window_infos()
			new_app = list(set(new_apps).difference(set(old_apps)))
			new_app = new_app[0].split(" ",1)
			new_app_xid = new_app[0]
			new_app_name = new_app[1]
			newApp = AppAction(new_app_xid,new_app_name)
	return newApp

class AppAction:
	def __init__(self,xid,name):
		self.xid = xid
		self.name = name

	def closeApp(self):
		if self.name in ("dde-desktop","Dock","running script"):
			return
		screen = wnck.screen_get_default()
		while gtk.events_pending():
			gtk.main_iteration()
		print "Closed Window: name[%s] xid[%s]" % (self.name,self.xid)
		wrapped_window = gtk.gdk.window_foreign_new(int(self.xid))
		wrapped_window.destroy()

def get_ifc():
	session_bus = dbus.SessionBus()
	session_obj = session_bus.get_object('com.deepin.daemon.Keybinding', '/com/deepin/daemon/Keybinding')
	session_if = dbus.Interface(session_obj,dbus_interface='com.deepin.daemon.Keybinding')

class HotKey(unittest.TestCase):
	@classmethod
	def setUp(cls):
		cls.passwd = 'a'
	@classmethod
	def tearDown(cls):
		pass

	def test_launcher(self):
		#sendSingleKey(k.windows_l_key)
		sendSingleKey(k.super_l_key)
		if Window(display.Display()).loop():
			self.assertIn("dde-launcher", get_window_names())
			if(self.assertIn("dde-launcher", get_window_names()) is None):
				sendSingleKey(k.super_l_key)
			
		else:
			print "launcher did not opend!"
			sys.exit(1)

	def test_show_desktop(self):
		old_apps = get_window_infos()
		sendSingleKey(k.super_l_key)
		time.sleep(1)
		if "dde-launcher" in get_window_names():
			typewrite("deepin-movie")
			time.sleep(1)
			sendSingleKey(k.return_key)
			print "old_apps: ", old_apps
			newApp = get_diff_from_oldApp(old_apps)
			lang = get_language()
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
			else:
				self.assertEqual("深度影院",get_active_window_name())
			time.sleep(1)
			#show desktop
			sendMutiKeys(k.windows_l_key,'d')
			time.sleep(1)
			self.assertEqual("dde-desktop",get_active_window_name())
			time.sleep(1)
			#show app 
			sendMutiKeys(k.windows_l_key,'d')
			time.sleep(1)
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
				if (self.assertEqual("Deepin Movie",get_active_window_name()) is None):
					newApp.closeApp()
			else:
				self.assertEqual("深度影院",get_active_window_name())
				if (self.assertEqual("深度影院",get_active_window_name())is None):
					newApp.closeApp()
		else:
			print "launcher did not opend!"
			sys.exit(1)

	def test_lock_screen(self):
		sendMutiKeys(k.windows_l_key,'l')
		ps = get_output("ps aux |grep -w \"/usr/bin/dde-lock\" |grep -v grep |awk '{print $11}'")
		self.assertEqual("/usr/bin/dde-lock",ps)
		if (self.assertEqual("/usr/bin/dde-lock",ps) is None):
			typewrite(self.passwd)
			sendSingleKey(k.return_key)
			self.assertEqual("dde-desktop",get_active_window_name())

	def test_file_manager(self):
		old_apps = get_window_infos()
		print "old_apps: ", old_apps
		sendMutiKeys(k.windows_l_key,'e')
		newApp = get_diff_from_oldApp(old_apps)
		#print "Opend: ", new_app_name
		lang = get_language()
		if lang == "en_US":
			self.assertEqual("Home",get_active_window_name())
			time.sleep(1)
			if (self.assertEqual("Home",get_active_window_name()) is None):
				newApp.closeApp()
		else:
			self.assertEqual("主文件夹",get_active_window_name())
			time.sleep(1)
			if (self.assertEqual("主文件夹",get_active_window_name()) is None):
				newApp.closeApp()

	def test_screenshot(self):
		sendMutiKeys(k.control_l_key,k.alt_l_key,'a')
		time.sleep(1)
		lang = get_language()
		if lang == "en_US":
			self.assertEqual("Deepin Screenshot",get_active_window_name())
			time.sleep(1)
			if (self.assertEqual("Deepin Screenshot",get_active_window_name()) is None):
				sendSingleKey(k.escape_key)
		else:
			self.assertEqual("深度截图",get_active_window_name())
			time.sleep(1)
			if (self.assertEqual("深度截图",get_active_window_name()) is None):
				sendSingleKey(k.escape_key)

	def test_close_window(self):
		old_apps = get_window_infos()
		sendSingleKey(k.super_l_key)
		time.sleep(1)
		if "dde-launcher" in get_window_names():
			typewrite("deepin-movie")
			time.sleep(1)
			sendSingleKey(k.return_key)
			newApp = get_diff_from_oldApp(old_apps)
			lang = get_language()
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
				if (self.assertEqual("Deepin Movie",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.alt_l_key,k.lookup_character_keycode('F4'))
					time.sleep(1)
					self.assertEqual("dde-desktop",get_active_window_name())

			else:
				self.assertEqual("深度影院",get_active_window_name())
				if (self.assertEqual("深度影院",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.alt_l_key,k.lookup_character_keycode('F4'))
					time.sleep(1)
					self.assertEqual("dde-desktop",get_active_window_name())

			
	def test_maximize_window(self):
		old_apps = get_window_infos()
		sendSingleKey(k.super_l_key)
		time.sleep(1)
		if "dde-launcher" in get_window_names():
			typewrite("deepin-movie")
			time.sleep(1)
			sendSingleKey(k.return_key)
			print "old_apps: ", old_apps
			newApp = get_diff_from_oldApp(old_apps)
			lang = get_language()
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
				if (self.assertEqual("Deepin Movie",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.super_l_key,k.up_key)
					self.assertTrue(get_window_max("Deepin Movie"))
					newApp.closeApp()
			else:
				self.assertEqual("深度影院",get_active_window_name())
				if (self.assertEqual("深度影院",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.super_l_key,k.up_key)
					self.assertTrue(get_window_max("深度影院"))
					newApp.closeApp()
			
	def test_restore_window(self):
		old_apps = get_window_infos()
		sendSingleKey(k.super_l_key)
		time.sleep(1)
		if "dde-launcher" in get_window_names():
			typewrite("deepin-movie")
			time.sleep(1)
			sendSingleKey(k.return_key)
			print "old_apps: ", old_apps
			newApp = get_diff_from_oldApp(old_apps)
			lang = get_language()
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
				if (self.assertEqual("Deepin Movie",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.super_l_key,k.up_key)
					time.sleep(1)
					self.assertTrue(get_window_max("Deepin Movie"))
					time.sleep(1)
					sendMutiKeys(k.super_l_key,k.down_key)
					time.sleep(1)
					self.assertFalse(get_window_max("Deepin Movie"))
					newApp.closeApp()
			else:
				self.assertEqual("深度影院",get_active_window_name())
				if (self.assertEqual("深度影院",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.super_l_key,k.up_key)
					time.sleep(1)
					self.assertTrue(get_window_max("深度影院"))
					time.sleep(1)
					sendMutiKeys(k.super_l_key,k.down_key)
					time.sleep(1)
					self.assertFalse(get_window_max("深度影院"))
					newApp.closeApp()

	def test_move_window(self):
		old_apps = get_window_infos()
		sendSingleKey(k.super_l_key)
		time.sleep(1)
		if "dde-launcher" in get_window_names():
			typewrite("deepin-movie")
			time.sleep(1)
			sendSingleKey(k.return_key)
			print "old_apps: ", old_apps
			newApp = get_diff_from_oldApp(old_apps)
			lang = get_language()
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
				if (self.assertEqual("Deepin Movie",get_active_window_name()) is None):
					time.sleep(1)
					default = get_window_geometry("Deepin Movie")
					sendMutiKeys(k.alt_l_key,k.lookup_character_keycode('F7'))
					time.sleep(1)
					sendSingleKey(k.right_key)
					time.sleep(1)
					sendSingleKey(k.down_key)
					time.sleep(1)
					sendSingleKey(k.return_key)
					time.sleep(1)
					changed = get_window_geometry("Deepin Movie")
					self.assertGreater(changed[0],default[0])
					self.assertGreater(changed[1],default[1])
					newApp.closeApp()
			else:
				self.assertEqual("深度影院",get_active_window_name())
				if (self.assertEqual("深度影院",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.alt_l_key,k.lookup_character_keycode('F7'))
					time.sleep(1)
					sendSingleKey(k.right_key)
					time.sleep(1)
					sendSingleKey(k.down_key)
					time.sleep(1)
					sendSingleKey(k.return_key)
					time.sleep(1)
					changed = get_window_geometry("深度影院")
					self.assertGreater(changed[0],default[0])
					self.assertGreater(changed[1],default[1])
					newApp.closeApp()

	def test_resize_window(self):
		old_apps = get_window_infos()
		sendSingleKey(k.super_l_key)
		time.sleep(1)
		if "dde-launcher" in get_window_names():
			typewrite("deepin-movie")
			time.sleep(1)
			sendSingleKey(k.return_key)
			print "old_apps: ", old_apps
			newApp = get_diff_from_oldApp(old_apps)
			lang = get_language()
			if lang == "en_US":
				self.assertEqual("Deepin Movie",get_active_window_name())
				if (self.assertEqual("Deepin Movie",get_active_window_name()) is None):
					time.sleep(1)
					default = get_window_geometry("Deepin Movie")
					sendMutiKeys(k.alt_l_key,k.lookup_character_keycode('F8'))
					time.sleep(1)
					sendSingleKey(k.right_key)
					time.sleep(1)
					sendSingleKey(k.right_key)
					time.sleep(1)
					sendSingleKey(k.down_key)
					time.sleep(1)
					sendSingleKey(k.down_key)
					time.sleep(1)
					sendSingleKey(k.return_key)
					time.sleep(1)
					changed = get_window_geometry("Deepin Movie")
					self.assertGreater(changed[2],default[2])
					self.assertGreater(changed[3],default[3])
					newApp.closeApp()
			else:
				self.assertEqual("深度影院",get_active_window_name())
				if (self.assertEqual("深度影院",get_active_window_name()) is None):
					time.sleep(1)
					sendMutiKeys(k.alt_l_key,k.lookup_character_keycode('F8'))
					time.sleep(1)
					sendSingleKey(k.right_key)
					time.sleep(1)
					sendSingleKey(k.right_key)
					time.sleep(1)
					sendSingleKey(k.down_key)
					time.sleep(1)
					sendSingleKey(k.down_key)
					time.sleep(1)
					sendSingleKey(k.return_key)
					time.sleep(1)
					changed = get_window_geometry("深度影院")
					self.assertGreater(changed[2],default[2])
					self.assertGreater(changed[3],default[3])
					newApp.closeApp()


if __name__ == '__main__':
	suite = unittest.TestSuite()
	suite.addTest(HotKey('test_launcher'))
	suite.addTest(HotKey('test_show_desktop'))
	suite.addTest(HotKey('test_lock_screen'))
	suite.addTest(HotKey('test_file_manager'))
	suite.addTest(HotKey('test_screenshot'))
	suite.addTest(HotKey('test_close_window'))
	suite.addTest(HotKey('test_maximize_window'))
	suite.addTest(HotKey('test_restore_window'))
	suite.addTest(HotKey('test_move_window'))
	suite.addTest(HotKey('test_resize_window'))
	unittest.TextTestRunner(verbosity=2).run(suite)


