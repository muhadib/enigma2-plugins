#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import sys, traceback

# Config
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

# Screen
from Components.ActionMap import ActionMap
from Components.ActionMap import HelpableActionMap
from Components.ScrollLabel import ScrollLabel
from enigma import eSize, ePoint, getDesktop
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Tools.BoundFunction import boundFunction

# Plugin internal
from . import _
from PushService import PushService
from PushServiceBase import PushServiceBase
from ModuleBase import ModuleBase
from ServiceBase import ServiceBase
from ControllerBase import ControllerBase


# States
(MAIN, SERVICES, PLUGINS) = range(3)
#IDEA combine into one screen
#(MAIN, SERVICES, ADDSERVICE, REMOVESERVICE, PLUGINS, ADDPLUGIN, REMOVEPLUGIN) = range(7)


#######################################################
# Configuration screen
class ConfigScreen(Screen, ConfigListScreen, HelpableScreen, PushServiceBase):

	skin = """
		<screen name="ConfigScreen" title="" position="center,center" size="565,350">
			<ePixmap position="0,5" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,5" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,5" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,5" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="280,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="420,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="5,50" size="555,225" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,275" zPosition="1" size="565,2" />
		</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["ConfigScreen", "ConfigListScreen"]
		
		from plugin import NAME, VERSION, gPushService
		self.setup_title = NAME + " " + _("Configuration") + " " + VERSION
		
		PushServiceBase.__init__(self)
		if gPushService:
			gPushService.stop()
		
		# Load local plugins to work on
		self.load()
		
		# Buttons
		self["key_red"]    = StaticText("")
		self["key_green"]  = StaticText("")
		self["key_blue"]   = StaticText("")
		self["key_yellow"] = StaticText("")
		
		self.help_window = None
		
		# Define Actions
		#E2 Bug self["custom_actions"] = HelpableActionMap(self, ["SetupActions", "ColorActions", "PushServiceConfigActions"],
		self["custom_actions"] = HelpableActionMap(self, "PushServiceConfigActions",
		{
			"pageUp":				(self.pageUp,       _("Page up")),
			"pageDown":			(self.pageDown,     _("Page down")),
		}, -2) # higher priority
		
		self["main_actions"] = HelpableActionMap(self, "PushServiceConfigActions",
		{
			"red":					(self.keyCancel,       _("Exit without saving")),
			"green":				(self.keySave,         _("Save and exit")),
		}, -2) # higher priority
		self["main_actions"].setEnabled(False)
		
		self["main_actions_enabled"] = HelpableActionMap(self, "PushServiceConfigActions",
		{
			"yellow":				(self.showServices,    _("Show Services")),
			"blue":					(self.showPlugins,     _("Show Plugins")),
		}, -2) # higher priority
		self["main_actions_enabled"].setEnabled(False)
		
		self["service_actions"] = HelpableActionMap(self, "PushServiceConfigActions",
		{
			"red":					(self.showMain,        _("Back to main screen")),
			"green":				(self.testService,     _("Test selected Service")),
			"yellow":				(self.addServices,     _("Add Service")),
			"blue":					(self.removeServices,  _("Remove Service")),
		}, -2) # higher priority
		self["service_actions"].setEnabled(False)
		
		self["plugin_actions"] = HelpableActionMap(self, "PushServiceConfigActions",
		{
			"red":					(self.showMain,        _("Back to main screen")),
			"green":				(self.testPlugin,      _("Test selected Plugin")),
			"yellow":				(self.addPlugins,      _("Add Plugin")),
			"blue": 				(self.removePlugins,   _("Remove Plugin")),
		}, -2) # higher priority
		self["plugin_actions"].setEnabled(False)
		
		# Initialize Configuration part
		self.list = []
		self.state = MAIN
		self.build()
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.change)
		
		# Override selectionChanged because our config tuples are bigger
		self.onChangedEntry = [ ]
		def selectionChanged():
			current = self["config"].getCurrent()
			if self["config"].current != current:
				if self["config"].current:
					self["config"].current[1].onDeselect(self.session)
				if current:
					current[1].onSelect(self.session)
				self["config"].current = current
			for x in self["config"].onSelectionChanged:
				x()
		self["config"].selectionChanged = selectionChanged
		
		self.setTitle(self.setup_title)

	def change(self, uniqueid=None):
		select = self.build(uniqueid)
		self["config"].setList( self.list )
		
		if select is not None:
			self["config"].instance.moveSelectionTo(select)

	def build(self, uniqueid=None):
		self.list = []
		select = None
		
		def buildEntries(entries):
			select = None
			if entries:
				for idx, entry in enumerate(entries):
					self.list.append( getConfigListEntry( entry.getNameId(), entry.getConfigEnable(), idx ) )
					if entry.getUniqueID() == uniqueid:
						# Select the added entry
						select = len(self.list)-1
					if entry.getEnable():
						for key, element, description in entry.getConfigOptions():
							self.list.append( getConfigListEntry( "  " + str(description), element, idx ) )
			return select
		
		if self.state == MAIN:
			self["key_red"].setText(_("Cancel"))
			self["key_green"].setText(_("OK"))
			self["service_actions"].setEnabled(False)
			self["plugin_actions"].setEnabled(False)
			self["main_actions"].setEnabled(True)
			if config.pushservice.enable.value:
				self["key_yellow"].setText(_("Services"))
				self["key_blue"].setText(_("Plugins"))
				self["main_actions_enabled"].setEnabled(True)
			else:
				self["key_yellow"].setText(_(""))
				self["key_blue"].setText(_(""))
				self["main_actions_enabled"].setEnabled(False)
			
			self.list.append( getConfigListEntry( _("Enable PushService"), config.pushservice.enable, 0 ) )
			
			if config.pushservice.enable.value:
				self.list.append( getConfigListEntry( _("Dreambox name"), config.pushservice.boxname, 0 ) )
				self.list.append( getConfigListEntry( _("Config file"), config.pushservice.xmlpath, 0 ) )
				
				self.list.append( getConfigListEntry( _("Start time (HH:MM)"), config.pushservice.time, 0 ) )
				self.list.append( getConfigListEntry( _("Period in hours (0=disabled)"), config.pushservice.period, 0 ) )
				self.list.append( getConfigListEntry( _("Run on boot"), config.pushservice.runonboot, 0 ) )
			
		elif self.state == SERVICES:
			self["key_red"].setText(_("Main"))
			self["key_green"].setText(_("Test"))
			self["key_yellow"].setText(_("Add service"))
			self["key_blue"].setText(_("Remove service"))
			self["main_actions"].setEnabled(False)
			self["main_actions_enabled"].setEnabled(False)
			self["plugin_actions"].setEnabled(False)
			self["service_actions"].setEnabled(True)
			
			select = buildEntries(self.getServices())
		
		elif self.state == PLUGINS:
			self["key_red"].setText(_("Main"))
			self["key_green"].setText(_("Test"))
			self["key_yellow"].setText(_("Add plugin"))
			self["key_blue"].setText(_("Remove plugin"))
			self["main_actions"].setEnabled(False)
			self["main_actions_enabled"].setEnabled(False)
			self["service_actions"].setEnabled(False)
			self["plugin_actions"].setEnabled(True)
			
			select = buildEntries(self.getPlugins())
			
		return select

	def getCurrentEntry(self):
		current = self["config"].getCurrent()
		return current and current[0]

	def getCurrentValue(self):
		current = self["config"].getCurrent()
		value = current and current[1]
		return value and str(value.getText()) or ""

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def showMain(self):
		self.hideHelpWindow()
		self.state = MAIN
		self.change()

	def showServices(self):
		self.hideHelpWindow()
		self.state = SERVICES
		self.change()

	def addServices(self):
		self.hideHelpWindow()
		self.session.openWithCallback(self.addServicesCB, ChoiceBox,_("Add Service"), self.getAvlServices())

	def addServicesCB(self, result):
		module = result and result[1]
		if module:
			id = self.addService(module)
			self.change( id )

	def removeServices(self):
		self.hideHelpWindow()
		select = 0
		current = self["config"].getCurrent()
		if current:
			select = current[2]
		slist = self.getServiceInstances()
		if slist:
			self.session.openWithCallback(self.removeServicesCB, ChoiceBox,_("Remove plugin"), list=slist, selection=select)

	def removeServicesCB(self, result):
		service = result and result[1]
		if service:
			self.removeService(service)
			self.change()

	def showPlugins(self):
		self.hideHelpWindow()
		self.state = PLUGINS
		self.change()

	def addPlugins(self):
		self.hideHelpWindow()
		self.session.openWithCallback(self.addPluginsCB, ChoiceBox,_("Add Plugin"), self.getAvlPlugins())

	def addPluginsCB(self, result):
		module = result and result[1]
		if module:
			id = self.addPlugin(module)
			self.change( id )

	def removePlugins(self):
		self.hideHelpWindow()
		select = 0
		current = self["config"].getCurrent()
		if current:
			select = current[2]
		plist = self.getPluginInstances()
		if plist:
			self.session.openWithCallback(self.removePluginsCB, ChoiceBox,_("Remove plugin"), list=plist, selection=select)

	def removePluginsCB(self, result):
		plugin = result and result[1]
		if plugin:
			self.removePlugin(plugin)
			self.change()

	# Overwrite ConfigListScreen keySave function
	def keySave(self):
		self.hideHelpWindow()
		
		# Save E2 PushService config
		self.saveAll()
		
		# Build xml config and write it
		self.save()
		
		# If we need assign / "write" access import the plugin
		# global won't work across module scope
		import plugin
		if config.pushservice.enable.value:
			if plugin.gPushService:
				plugin.gPushService.copyfrom(self)
				plugin.gPushService.start()
			else:
				#global gPushService
				plugin.gPushService = PushService()
				plugin.gPushService.start()
		else:
			#global gPushService
			plugin.gPushService = None
		
		self.close()

	# Overwrite ConfigListScreen keyCancel function
	def keyCancel(self):
		self.hideHelpWindow()
		# Always ask user, because we don't get a change notification from the services or plugins
		self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))

	# Overwrite ConfigListScreen cancelConfirm function
	def cancelConfirm(self, result):
		from plugin import gPushService
		if gPushService:
			# Make sure the configuration is still consistent
			gPushService.load()
			gPushService.start()
		
		# Call baseclass function
		ConfigListScreen.cancelConfirm(self, result)

	# Overwrite Screen close function
	def close(self):
		self.hideHelpWindow()
		from plugin import ABOUT
		self.session.openWithCallback(self.closeConfirm, MessageBox, ABOUT, MessageBox.TYPE_INFO)

	def closeConfirm(self, dummy=None):
		# Call baseclass function
		Screen.close(self)

	def testService(self):
		# Allows testing the actually not saved configuration
		#if self.state != SERVICES: return
		self.hideHelpWindow()
		
		# Get the selected Service
		current = self["config"].getCurrent()
		service = current and self.getService(current[2])
		
		if service and service.getEnable():
			self.session.open(TestConsole, service)

	def testPlugin(self):
		# Allows testing the actually not saved configuration
		#if self.state != PLUGINS: return
		self.hideHelpWindow()
		
		# Get the selected Plugin
		current = self["config"].getCurrent()
		plugin = current and self.getPlugin(current[2])
		
		if plugin and plugin.getEnable():
			self.session.open(TestConsole, plugin)

	def hideHelpWindow(self):
		current = self["config"].getCurrent()
		if current and hasattr(current[1], "help_window"):
			help_window = current[1].help_window
			if help_window:
				help_window.hide()


class TestConsole(Screen):
	def __init__(self, session, test):
		Screen.__init__(self, session)
		self.skinName = ["TestBox", "Console"]
		title = ""
		text = ""
		self.test = test
		
		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"], 
		{
			"ok":    self.cancel,
			"back":  self.cancel,
			"up":    self["text"].pageUp,
			"down":  self["text"].pageDown
		}, -1)
		
		# Set title and text
		test.begin()
		if isinstance(test, ServiceBase):
			title = _("Testing Service") + " " + test.getName()
			text = _("Testing...\n\nCancel?")
		elif isinstance(test, ControllerBase):
			title = _("Testing Plugin") + " " + test.getName()
			text = _("Testing...\n\nCancel?")
		else:
			title = _("Testing")
			text = _("Nothing to test")
		
		self.setTitle(title)
		self.setText(text)
		
		# Starting test
		try:
			if isinstance(test, ServiceBase):
				test.push( self.callback, self.errback, _("PushService Config"), _("Push test"), _("If You can see this, Your configuration is correct.") )
			elif isinstance(test, ControllerBase):
				test.run( self.callback, self.errback )
		except Exception, e:
			text = _("PushService Test exception:") + "\n\n"
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
			for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
				text += line
			self.setText(text)

	def callback(self, *args):
		text = _("Test has been finished successfully") + "\n\n"
		if args:
			for arg in args:
				text += str(arg) + "\n"
		elif self.test and isinstance(self.test, ControllerBase):
			text += _("Nothing to push")
		self.setText(text)

	def errback(self, *args):
		text = ""
		for arg in args:
			if isinstance(arg, Exception):
				text += _("Test failed:\n\n%s\n\n%s") % (arg.type, arg.value) + "\n"
			elif arg:
				text += _("Test failed\n\n%s") % str(arg) + "\n"
			else:
				text += _("Test failed") + "\n"
		self.setText(text)

	def cancel(self):
		if self.test:
			self.test.cancel()
		self.close()

	def setText(self, text):
		self["text"].setText(text)

	def close(self):
		if self.test:
			self.test.end()
		Screen.close(self)