from webcutter.dplex import PlexInterface
import os
import time
import subprocess


class CutterInterface:
	def __init__(self, server):
		self._server = server
		self._mcut_binary = os.path.dirname(__file__) + '/bin/mcut'
		self._reconstruct_apsc_binary = os.path.dirname(__file__) + '/bin/reconstruct_apsc'
		self._ffmpeg_binary = '/usr/bin/ffmpeg'

	def _call(self, exc_lst):
		try:
			res = subprocess.check_output(exc_lst)
			return res
		except subprocess.CalledProcessError as err:
			raise err		

	def _filename(self,movie):
		"""
		the movie filename
		"""
		m = PlexInterface.movie_rec(movie)
		if len(m['locations']) > 1:
			raise ValueError('cannot handle multiple Files in movie folder')
		else:
			return m['locations'][0].split('/')[-1]

	def _pathname(self,movie):
		"""
		path to the mounted movie file
		"""
		m = PlexInterface.movie_rec(movie)
		if len(m['locations']) > 1:
			raise ValueError('cannot handle multiple Files in movie folder')
		else:
			return os.path.dirname(__file__) + "/mnt/" + self._filename(movie)

	def _cutfilename(self,movie):
		"""
		the movie cut filename
		"""
		m = PlexInterface.movie_rec(movie)
		if len(m['locations']) > 1:
			raise ValueError('cannot handle multiple Files in movie folder')
		else:
			return m['locations'][0].split('/')[-1].split('.')[0] + ' cut.ts'

	def _cutname(self,movie):
		"""
		path to the mounted movie cut file (inplace = False)
		"""
		m = PlexInterface.movie_rec(movie)
		if len(m['locations']) > 1:
			raise ValueError('cannot handle multiple Files in movie folder')
		else:
			return os.path.dirname(__file__) + "/mnt/" + self._cutfilename(movie)

	def mount(self, movie):
		m = PlexInterface.movie_rec(movie)
		if len(m['locations']) > 1:
			raise ValueError('cannot cut multiple Files in movie folder')
		else:
			source = f"//{self._server}/{'/'.join(m['locations'][0].split('/')[2:-1])}"
			target = os.path.dirname(__file__) + "/mnt/"
			mount_lst = ["mount","-t","cifs", "-o", "credentials=/etc/smbcredentials", f"{source}", f"{target}"]
#			print()
#			print(" ".join(mount_lst))
#			print()
		try:
			res = subprocess.check_output(mount_lst)
			return res
		except subprocess.CalledProcessError as e:
			print(str(e))
			raise e

	def umount(self):
		target = os.path.dirname(__file__) + "/mnt/"
		umount_lst = ["umount","-l",f"{target}"]		
#		print()
#		print(" ".join(umount_lst))
#		print()
		try:
			res = subprocess.check_output(umount_lst)
			return res
		except subprocess.CalledProcessError as e:
			print(str(e))
			raise e

	def frame(self,movie, ftime, target = None):
		#frame_name = 'guid' + PlexInterface.movie_rec(movie)['guid'] + '_' + str(ftime).replace(':','-') + '.jpg'
		frame_name = 'frame.jpg'
		if target == None:
			target = os.path.dirname(__file__) + "/data/"
		target += frame_name
		exc_lst = [self._ffmpeg_binary,"-ss", ftime, "-i", f"{self._pathname(movie)}", 
			"-vframes", "1", "-q:v", "2", f"{target}", "-hide_banner", "-loglevel", "fatal", 
			"-max_error_rate","1","-y" ]
		self.mount(movie)
		try:
			res = subprocess.check_output(exc_lst)
			res = res.decode('utf-8')
			print(res)
		except subprocess.CalledProcessError as err:
			print(str(err))
		finally:
			self.umount()
			return frame_name

	def _apsc(self,movie):
		#check ob .ap und Datei existiert.
		try:
			self.mount(movie)
			return os.path.exists(self._pathname(movie)+'.ap')
		except FileNotFoundError as e:
			print(str(e))
		finally:
			self.umount()

	def _reconstruct_apsc(self, movie):
		print()
		print(f"'{self._filename(movie)}', *.ap und *.sp Files werden rekonstruiert.")
		exc_lst = [self._reconstruct_apsc_binary,self._pathname(movie)]
		try:
			res = subprocess.check_output(exc_lst)
			res = res.decode('utf-8')
			return res
		except subprocess.CalledProcessError as e:
			raise e
		finally:
			print(f"'{self._filename(movie)}', *.ap und *.sp Files wurden rekonstruiert.")

	def _mcut(self, movie, ss, to, inplace = False):
		print()
		print(f"'{self._filename(movie)}' wird geschnitten. -]+{ss},{to}+[-")
		if inplace:
			exc_lst = [self._mcut_binary,"-r","-n",f"'{movie.title}'","-d", f"'{movie.summary}'",f"{self._pathname(movie)}","-c",ss,to]
		else:
			exc_lst = [self._mcut_binary,"-n",f"'{movie.title}'","-d", f"'{movie.summary}'",f"{self._pathname(movie)}","-c",ss,to]
		try:
			res = subprocess.check_output(exc_lst)
			res = res.decode('utf-8')
			print(f"'{self._filename(movie)}' wurde geschnitten.")
			return res
		except subprocess.CalledProcessError as e:
			raise e

	def cut(self, movie, ss, to, inplace=False):
		t0 = time.time()
		t1 = time.time() #initialize t1, in case .ap files exist ...
		restxt = 'cut started ... \n'
		self.mount(movie)
		#check ob .ap und .sc Dateien existieren, wenn nicht, erzeugen
		restxt += f"{self._filename(movie)} exists ? {os.path.exists(self._pathname(movie))}\n"
		restxt += f"{self._filename(movie)+'.ap'} exists ? {os.path.exists(self._pathname(movie)+'.ap')}\n"
		restxt += f"{self._filename(movie)+'.sc'} exists ? {os.path.exists(self._pathname(movie)+'.sc')}\n\n"

		if ((inplace == False) and (os.path.exists(self._cutname(movie)))):
			try:
				os.remove(self._cutname(movie))
			except FileNotFoundError as e:
				print(str(e))
				raise e
			restxt += f"{self._cutfilename(movie)} existed already, file deleted ... \n\n"

		if not os.path.exists(self._pathname(movie)+'.ap'):
			try:
				res = self._reconstruct_apsc(movie)
				t1 = time.time()
				restxt += f"Ergebnis Reconstruct: {res}\n"
				restxt += f"ReSt Zeit: {(t1 - t0):7.0f} sec.\n\n"
			except subprocess.CalledProcessError as e:
				raise e
		
		try:
			res = self._mcut(movie,ss,to,inplace)
			t2 = time.time()
			restxt += f"Ergebnis Mcut: {res}\n"
			restxt += f"Mcut Zeit: {(t2 - t1):7.0f} sec.\n"
			restxt += f"Ges. Zeit: {(t2 - t0):7.0f} sec.\n\n"
			print(f"elapsed time: {(t2 - t0):7.0f} sec.")
			return restxt
		except subprocess.CalledProcessError as e:
			raise e
		finally:
			self.umount()
