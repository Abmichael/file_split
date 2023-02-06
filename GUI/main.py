from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from filesplit import Ui_MainWindow
import os


class Worker(QThread,QObject):
	chunkcopied = pyqtSignal(int)
	def __init__(self,path,listWidget,pieces,files):
		super().__init__()
		self.path = path
		self.listWidget = listWidget
		self.pieces = pieces
		self.files = files
		self.current_buffer = 0

	def copyfileobj(self,fsrc, fdst, start, end, length=1024 * 1024):
		fsrc.seek(start)
		while start<=fsrc.tell()<end:
			
			if fsrc.tell()+length>end:
				length = end - fsrc.tell()
			buf = fsrc.read(length)
			
			if not buf:
				break
			fdst.write(buf)
			self.current_buffer += length
			self.chunkcopied.emit(self.current_buffer)
		return fsrc.tell()

	def split(self):
		self.listWidget.clear()
		size = os.lstat(self.path).st_size
		num = self.pieces.value()
		offset = size//num
		ret = 0
		for i in range(num):
			with open(self.path, "rb") as fsrc:
				with open(f"{self.path}.part{i}", "wb") as fdst:
					if i == num-1:
						ret = self.copyfileobj(fsrc, fdst, ret, size, min(1024*1024,size))
						self.listWidget.addItem(os.path.basename(f"{self.path}.part{i}"))
					else:
						ret = self.copyfileobj(fsrc, fdst, ret, ret + offset, min(1024*1024,size))
						self.listWidget.addItem(os.path.basename(f"{self.path}.part{i}"))

	def combine(self):
		name = os.path.splitext(self.files[0])[0]
		with open(name,"wb") as core:
			for file in self.files:
				with open(file,'rb') as add:
					self.copyfileobj(add,core,0,os.lstat(file).st_size,1024*1024)
					self.listWidget.takeItem(0)
		self.listWidget.addItem(name)

	def setCombine(self):
		self.flag = 'c'

	def setSplit(self):
		self.flag = 's'

	def run(self):
		if self.flag=='c':
			self.combine()
		elif self.flag == 's':
			self.split()

class MainWindow(Ui_MainWindow,QMainWindow):

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.setupUi(self)
		self.centralWidget().setLayout(self.verticalLayout)
		self.pieces.hide()
		self.setWindowTitle("Splitter")
		self.groupBox.setLayout(self.fileinfoholder)

		self.rsplit.toggled.connect(lambda: self.pieces.setHidden(not self.rsplit.isChecked()))
		self.select.clicked.connect(self.get_path)
		self.go.clicked.connect(self.handle)
		self.pieces.valueChanged.connect(self.handle_pieces)

	def handle(self):
		self.process = Worker(self.path,self.listWidget,self.pieces,self.files)
		self.process.chunkcopied.connect(self.handle_progressbar)

		if self.rcombine.isChecked():
			self.process.setCombine()
		else:
			self.process.setSplit()
		self.process.start()
		# self.processes = QThreadPool(self)
		# self.processes.start(self.process)

	def handle_progressbar(self,val):
		self.progressBar.setValue(int(val/(1024*1024)))

	def get_path(self):
		if self.rcombine.isChecked():
			self.path = QFileDialog.getExistingDirectory(self,"Path to the parts...")
			if self.path:
				self.path_input.setText(self.path)
				self.files = [os.path.join(self.path,x) for x in os.listdir(self.path) 
								if '.part' in os.path.splitext(x)[1]]
				
				def get_num(s):
					s = os.path.splitext(s)[1]
					l = len(s)
					i = 0
					nums = []
					while i<l:
						num = ''
						symbol = s[i]
						while symbol.isdigit():
							num += symbol
							i +=1
							if i < l:
								symbol = s[i]
							else: break
						if num != '':
							nums.append(num)
						i += 1
					if nums:
						return int(nums[0])

				self.files.sort(key=get_num)
				#XXX wrong sorting '10'<'2'
				# self.files.sort()
				print(self.files)
				self.name_label.setText('No split files found!')
				
				if self.files:
					self.provider = QFileIconProvider()
					name = os.path.splitext(self.files[0])[0]
					self.icon = self.provider.icon(QFileInfo(name)).pixmap(QSize(50,50))
					self.fileicon.setPixmap(self.icon)
					size = os.lstat(self.files[0]).st_size
					wholesize = 0
					for i in self.files:
						wholesize += os.lstat(i).st_size
					self.progressBar.setRange(0,wholesize//(1024*1024))
					self.name_label.setText('Name: '+os.path.basename(name))
					self.size_label.setText('Size: '+str(wholesize//(1024*1024))+' MB')
					self.part_label.setText('Part Size: '+str(size//(1024*1024))+' MB')
					self.listWidget.clear()
					self.listWidget.addItems([os.path.basename(x) for x in self.files])
					self.setWindowTitle(os.path.splitext(os.path.basename(self.files[0]))[0])
		else:
			self.path = QFileDialog.getOpenFileName(self,"File to Split...")[0]
			self.files = []
			if self.path:
				self.provider = QFileIconProvider()
				self.icon = self.provider.icon(QFileInfo(self.path)).pixmap(QSize(50,50))
				self.fileicon.setPixmap(self.icon)
				self.name_label.setText('Name: '+os.path.basename(self.path))
				self.size_label.setText('Size: '+str(os.lstat(self.path).st_size//(1024*1024))+' MB')
				self.progressBar.setRange(0,os.lstat(self.path).st_size//(1024*1024))
				self.handle_pieces()
				self.path_input.setText(self.path)
				self.setWindowTitle(os.path.basename(self.path))

	def handle_pieces(self):
		size = os.lstat(self.path).st_size//self.pieces.value()
		self.part_label.setText('Part Size: '+str(size//(1024*1024))+' MB')

app = QApplication([])
window = MainWindow()
window.show()
app.exec_()