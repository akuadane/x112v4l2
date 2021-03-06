"""
	Functionality for dealing with our thumbnails
"""
import os
import time
import tempfile
import shutil

from x112v4l2 import x11
from x112v4l2 import ffmpeg


THUMB_WIDTH = 160
THUMB_HEIGHT = 90
CACHE_PATH = os.path.join(tempfile.gettempdir(), 'x112v4l2', 'thumbs')


def mkdir():
	""" Create the directory in which we store thumbnails """
	return os.makedirs(CACHE_PATH, exist_ok=True)
	
def rmdir():
	""" Remove the temporary thumbs and directory """
	return shutil.rmtree(CACHE_PATH)
	

def get_win_filename(window):
	"""
		Return the base filename to be used for the given `window`
	"""
	return '{scr}.{win}.png'.format(
		scr=window.screen['full_id'],
		win=window.id,
	)

def create_all(parallel=4):
	"""
		Create thumbnails for all (interesting) X11 windows
		
		The `parallel` parameter determines how many simultaneous
		processes will be started to create the thumbnails
		
		Returns a dict of {win_id: filename}
	"""
	windows = list(x11.get_windows())
	procs = {}
	thumbs = {}
	while windows or procs:
		while windows and len(procs) < parallel:
			# Start a new process
			window = windows.pop()
			win_id = get_win_filename(window)
			filename = os.path.join(CACHE_PATH, win_id)
			procs[win_id] = ffmpeg.capture_window(
				window=window,
				filename=filename,
				max_width=THUMB_WIDTH,
				max_height=THUMB_HEIGHT,
			)
			thumbs[win_id] = filename
		
		# Check for finished processes
		for win_id, proc in procs.copy().items():
			if proc.poll() is not None:
				procs.pop(win_id)
			
		# Wait a bit
		time.sleep(0.4)
		
	return thumbs
	
