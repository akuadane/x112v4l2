"""
	Signal handlers for the UI
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

from x112v4l2 import v4l2
from x112v4l2 import v4l2
from x112v4l2 import x11
from x112v4l2 import ffmpeg
from x112v4l2 import thumbs


class BaseHandler(object):
	"""
		Base class for common handler-object functionality
	"""
	def __init__(self, ui, **kwargs):
		"""
			Create a new signal handler
			
			The `ui` parameter should be an instance of a UI class
		"""
		self.ui = ui
		super().__init__(**kwargs)
		
	
class MainHandler(BaseHandler):
	"""
		Handle all the signals
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		thumbs.mkdir()
		
	
	def exit_application(self, *args):
		self.ui.stop()
		
	
	def future_callback(self, func, *args, **kwargs):
		"""
			Return a function which can be used as a future callback
			
			At the time of the callback, the `future.result()` is sent
			to the function as the first argument, followed by any
			additional arguments specified here.
		"""
		def callback(future):
			return GObject.idle_add(func, future.result(), *args, **kwargs)
			
		return callback
		
	
	def on_show_main(self, *args):
		"""
			Triggered when the main window is shown
		"""
		self.refresh_v4l2_info()
		self.refresh_ffmpeg_info()
		self.refresh_x11_info()
		self.regen_x11_thumbs()
	
	def refresh_v4l2_info(self, *args):
		"""
			Recheck the state of the v4l2loopback kernel module
		"""
		# Indicate that stuff is reloading
		self.ui.show_v4l2_available(self.ui.STATE_RELOADING)
		self.ui.show_v4l2_loaded(self.ui.STATE_RELOADING)
		self.ui.show_v4l2_devices(self.ui.STATE_RELOADING)
		
		# Async info-getting
		avail_future = self.ui.executor.submit(v4l2.get_module_available)
		avail_future.add_done_callback(
			self.future_callback(self.ui.show_v4l2_available)
		)
		
		loaded_future = self.ui.executor.submit(v4l2.get_module_loaded)
		loaded_future.add_done_callback(
			self.future_callback(self.ui.show_v4l2_loaded)
		)
		
		devices_future = self.ui.executor.submit(v4l2.get_devices)
		devices_future.add_done_callback(
			self.future_callback(self.ui.show_v4l2_devices)
		)
		
	def set_v4l2_device_info(self, *args):
		"""
			Applies any changes made to the v4l2 configuration
		"""
		## TODO: Indicate we're updating
		names = self.ui.get_device_names()
		devices_future = self.ui.executor.submit(v4l2.configure_devices, names)
		devices_future.add_done_callback(
			self.future_callback(self.refresh_v4l2_info)
		)
		
	
	def refresh_x11_info(self, *args):
		"""
			Recheck the X11 situation
		"""
		# Indicate stuff is reloading
		self.ui.show_x11_display_info(self.ui.STATE_RELOADING)
		self.ui.show_x11_screen_info(self.ui.STATE_RELOADING)
		self.ui.show_x11_window_info(self.ui.STATE_RELOADING)
		
		# Xlib classes aren't picklable, so we can't future this :/
		displays = x11.get_displays()
		self.ui.show_x11_display_info(displays)
		screens = x11.get_screens()
		self.ui.show_x11_screen_info(screens)
		windows = x11.get_windows()
		self.ui.show_x11_window_info(list(windows))
		
	def regen_x11_thumbs(self, *args):
		"""
			(Re-)Generate thumbnails of all X11 windows
		"""
		self.ui.show_x11_thumb_path(thumbs.CACHE_PATH)
		self.ui.show_x11_thumbs(self.ui.STATE_RELOADING)
		
		future = self.ui.executor.submit(thumbs.create_all)
		future.add_done_callback(
			self.future_callback(self.ui.show_x11_thumbs)
		)
		
	
	def refresh_ffmpeg_info(self, *args):
		"""
			Recheck the state of the ffmpeg binary
		"""
		# Indicate that stuff is reloading
		self.ui.show_ffmpeg_installed(self.ui.STATE_RELOADING)
		self.ui.show_ffmpeg_version(self.ui.STATE_RELOADING)
		
		version_future = self.ui.executor.submit(ffmpeg.get_version)
		version_future.add_done_callback(
			self.future_callback(self.ui.show_ffmpeg_installed)
		)
		version_future.add_done_callback(
			self.future_callback(self.ui.show_ffmpeg_version)
		)
		
	

class DeviceHandler(BaseHandler):
	"""
		Handler for events triggered from a device tab
	"""
	def update_source_config(self, list_box, item, *args):
		"""
			Update the source config based on thumbnail selection
		"""
		if item is None:
			return
		
		# Find the source window instance
		source_window = getattr(item, 'source_window', None)
		if not source_window:
			for child in item.get_children():
				source_window = getattr(child, 'source_window', None)
				if source_window is not None:
					break
		
		if not source_window:
			raise TypeError('No source window found on object: {!r}'.format(item))
		
		self.ui.set_source_window(source_window)
		
	
