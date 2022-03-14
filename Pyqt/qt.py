__author__ = 'Ebrahim Khalili'
import sys, serial, serial.tools.list_ports, warnings #کتاب خانه های مربوط به پورت سریال 
from PyQt5.QtCore import QSize, QRect, QObject, pyqtSignal, QThread, pyqtSignal, pyqtSlot# ماژول های سیگنال گیری پای کیو تی
import pyqtgraph as pg # ماژول رسم گراف پای کیوتی
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication , QDialog
from PyQt5.QtCore import QCoreApplication
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, \
    QListView # ماژول های اصلی پا کیو تی - ویجت ها و با کس ها
from PyQt5.uic import loadUi # برای بار گزاری فایل کیوتی دیزاینر
import collections# ماژول جمع آوری داده
import joblib # ماژول پک مدلسازی 
import pickle
from Game import main# فراخوانی بازی پانگ
from sklearn.svm import SVC  #کتابخانه مربوط به یادگیری ماشین
import random 
import time
import math
import numpy
import os
import sys
####### شروع کد گرافیکی و مدلسازی و حمع آوری داده در محیط پای کیو تی با سیگنال های جمع آوری شده از طریق آردوینو#####
clf = SVC(kernel='linear') # svm فراخوانی مدل تشخیص جهت
ports = serial.tools.list_ports.comports()# تعریف پورت سریال
joblib_file = "joblib_model.pkl"#فراخوانی فایل مدلسازی
joblib_model = joblib.load(joblib_file)
if ports: # راه اندازی ماژول آردوینو به صورت مستقیم از طریق محیط پایتون
    #os.chdir('C:/')
    os.system('"arduino-cli compile --fqbn arduino:avr:uno --port COM3 Serial_qt"')# کامپایل و آپلود کد مربوط به پاکسازی بافر سریال
    time.sleep(0.4)
    os.system('"arduino-cli upload --fqbn arduino:avr:uno --port COM3 Serial_qt"')
    time.sleep(0.4)
    os.system('"arduino-cli compile --fqbn arduino:avr:uno --port COM3 Brain_qt"') #TGAM کامپایل و آپلود کد مربوط به راه اندازی ماژول 
    time.sleep(0.4)
    os.system('"arduino-cli upload --fqbn arduino:avr:uno --port COM3 Brain_qt"')
    #os.chdir('C:Users\EbrahimKhan\Desktop\pyQt\Serial_recive\Serial-Communication-GUI-Program-master') # مسیر دهی به فایل
    #os.chdir((os.path.dirname(os.path.realpath(__file__))))
# اطلاع رسانی از اتصال پورت سریال آردوینو و دریافت داده#
if not ports:print("!دستگاه سریال پیدا نشد")
if ports:
    warnings.warn('اتصال برقرار شد....')
    ser = serial.Serial('COM3',9600) # تعریف پورت سریال دریافتی 
# تعریف کلاس مربوط به دریافت سیگنال#
class Worker(QObject):
    finished = pyqtSignal() #سیگنال اتمام 
    intReady = pyqtSignal(str)# سیگنال شروع
    @pyqtSlot()
    def __init__(self): # تعریف اولیه کلاس
        super(Worker, self).__init__()
        self.working = True # شرط حلقه
        self.li=[]# لیست دریافت داده
    def work(self):# متد دریافت سیگنال از آردوینو
        while self.working:# شرط فراخوانی متد
            try:
                    line = ser.readline().decode('utf-8')# دریافت داده پورت سریال
                    self.li+=[list((line.split(',')))]# ذخیره سازی در لیست
                    time.sleep(0.5)#  توقف نیم ثانیه ای 
                    self.intReady.emit(line) # سیگنال شرط دریافت بسته ی سریالی بعدی          
            except Exception:
                pass
        self.finished.emit()# توقف حلقه
# کلاس اصلی پای کیوتی برای تعریف وظایف در محیط گرافیکی#
class qt(QMainWindow):
    def __init__(self):# تعریف اولیه کلاس
        QMainWindow.__init__(self)# پنجره اصلی
        sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        loadUi('qt.ui', self)# آپلود محیط کیوتی دیزاینر     
        self.thread = None# وظایف اولیه کلاس 
        self.worker = None# وظایف اولیه کلاس
        self.w_width = 1200# سایز صفحه اصلی
        self.w_height = 570
        self.data2=[]
        self.data1=[]
        self.showMaximized()
        self.setMaximumSize(QtCore.QSize(1500,1000 ))
        self.pushButton.clicked.connect(self.start_loop)# کلید دریافت سیگنال مغزی از پورت سریال       
        self.pushButton_8.clicked.connect(self.upload)# کلید برای کامپایل و دانلود آردوینو+ بارگزاری مدل تشخیص جهت 
        self.show_ch1.stateChanged.connect(lambda : self.hide1())# پنهان کردن نمودار سیگنال 
        self.show_ch1_2.stateChanged.connect(lambda : self.hide_sound())# پنهان کردن صدای بخش هدهد 
        self.show_ch1_3.stateChanged.connect(lambda : self.hide_image())# پنهان کردن تصویر بخش هدهد 
        self.show_ch1_4.stateChanged.connect(lambda : self.hide_word())# پنهان کردن کلمات بخش هدهد 
        self.pushButton_5.clicked.connect(self.save_sample )
        self.show_ch1_6.stateChanged.connect(lambda : self.color())
        self.pushButton_2.clicked.connect(self.stop_loop)  # stop the loop on the stop button click
        ###دانلود فایل های آردوینو <<توجه شود که اینترنت سرعت کافی داشته باشد و فیلتر شکن روشن نباشد####        
        self.action.triggered.connect(self.download_arduino)
        self.pushButton_6.clicked.connect(self.on_btn_human_click)# کلید بازی انسان در پانگ
        self.pushButton_7.clicked.connect(self.on_btn_AI_click)# کلید بازی ماشین در پانگ
        self.UiComponents()# css ایجاد
        self.show() 
        self.speed = 15 # سرعت حرکت ربات
        #رسم نمودار آنلاین-تکمیل نشده است#        
        sampleinterval=.1
        timewindow=10.
        size=(600,350)
        self.pen = pg.mkPen(color=(255, 0, 0))
        self._interval = int(sampleinterval*1000)
        self._bufsize = int(timewindow/sampleinterval)
        self.databuffer = collections.deque([0.0]*self._bufsize, self._bufsize)
        self.x = numpy.linspace( timewindow, 0.0, self._bufsize)
        self.y = numpy.zeros(self._bufsize, dtype=numpy.float)
        self.graphicsView.setLabel('left', self.comboBox_6.currentText(), '.')
        self.graphicsView.setLabel('bottom', 'time', 's')
        self.curve= self.graphicsView.plot(self.x, self.y, pen=self.pen)
        self._interval2 = int(sampleinterval*1000)
        self._bufsize2 = int(timewindow/sampleinterval)
        self.databuffer2 = collections.deque([0.0]*self._bufsize2, self._bufsize2)        
        self.x2 = numpy.linspace( timewindow, 0.0, self._bufsize2)
        self.y2 = numpy.zeros(self._bufsize2, dtype=numpy.float)
        self.graphicsView_2.setLabel('left', self.comboBox_7.currentText(), '.')
        self.graphicsView_2.setLabel('bottom', 'time', 's')
        self.curve2= self.graphicsView_2.plot(self.x2, self.y2, pen=self.pen)        
        self.timer = QtCore.QTimer(self.monit)
        self.timer.timeout.connect(self.updateplot)
        self.timer.start(1000)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.timer2 = QtCore.QTimer(self.monit)
        self.timer2.timeout.connect(self.updateplot2)
        self.timer2.start(1000)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        ########combo_box
        ##########clock
        # creating font object
        font = QFont('Arial', 16, QFont.Bold)
        # setting font to the label
        self.label_3.setFont(font)
        # adding label to the layout
        self.verticalLayout_2.addWidget(self.label_3)
        # setting the layout to main window
        self.setLayout(self.verticalLayout_2)
        # creating a timer object
        timer1 = QTimer(self.monit)
        # adding action to timer
        timer1.timeout.connect(self.showTime)
        # update the timer every second
        timer1.start(1000)  
        #creating SSVEP timer object
        self.flag8 = True #8Hz
        self.flag16 = True #16Hz
        self.flag24 = True #24Hz
        self.flag32 = True #32Hz
        timer_8hz = QTimer(self, interval=int(1000/2))# creating a timer object 8Hz
        timer_16hz = QTimer(self, interval=int(1000/8))# creating a timer object 16Hz
        timer_24hz = QTimer(self, interval=int(1000/12))# creating a timer object 24Hz
        timer_32hz = QTimer(self, interval=int(1000/24))# creating a timer object 32Hz
        timer_8hz.timeout.connect(self.freq8) # adding action to timer 8Hz
        timer_8hz.start() # update the timer 8 times every second
        timer_16hz.timeout.connect(self.freq16) # adding action to timer 16Hz
        timer_16hz.start() # update the timer 16 times every second
        timer_24hz.timeout.connect(self.freq24) # adding action to timer 24Hz
        timer_24hz.start() # update the timer 24 times every second
        timer_32hz.timeout.connect(self.freq32) # adding action to timer 32Hz
        timer_32hz.start() # update the timer 32 times every second      
    #methods of frequency timer    
    def freq8(self): #method for timer object 8Hz
        if (self.show_ch1_7.isChecked()) : #if color position is off
            if self.flag8:#blinking condition
                self.toolButton_2.setStyleSheet("background-color:red")#set as red
                self.toolButton_5.setStyleSheet("background-color:red")#set as red
            else:#blinking condition Off
                    self.toolButton_2.setStyleSheet("background-color: light gray")#set as gray    
                    self.toolButton_5.setStyleSheet("background-color: light gray")#set as gray
            self.flag8 = not self.flag8
        else:#blinking condition Off
            if (self.show_ch1_6.isChecked()) ==False:
                self.toolButton_2.setStyleSheet("background-color: light gray")#set as gray
                self.toolButton_5.setStyleSheet("background-color: light gray")#set as gray

    def freq16(self):#method for timer object 16Hz
        if (self.show_ch1_7.isChecked()) : #if color position is off
            if self.flag16:#blinking condition On
                self.toolButton_3.setStyleSheet("background-color : green")#set as red
                self.toolButton_8.setStyleSheet("background-color : green")#set as red
            else:#blinking condition Off
                    self.toolButton_3.setStyleSheet("background-color: light gray")#set as gray      
                    self.toolButton_8.setStyleSheet("background-color: light gray") #set as gray   
            self.flag16 = not self.flag16
        else:
            if (self.show_ch1_6.isChecked()) ==False:
                self.toolButton_3.setStyleSheet("background-color: light gray")#set as gray
                self.toolButton_8.setStyleSheet("background-color: light gray")#set as gray
    def freq24(self):#method for timer object 24Hz
        if (self.show_ch1_7.isChecked()) :#if color position is off
            if self.flag24:#blinking condition On
                self.toolButton_4.setStyleSheet("background-color : blue")#set as blue
                self.toolButton_7.setStyleSheet("background-color : blue")#set as blue
            else:#blinking condition Off
                    self.toolButton_4.setStyleSheet("background-color: light gray")#set as gray
                    self.toolButton_7.setStyleSheet("background-color: light gray")#set as gray
            self.flag24 = not self.flag24
        else:#blinking condition Off
            if (self.show_ch1_6.isChecked()) ==False:
                self.toolButton_4.setStyleSheet("background-color: light gray")#set as gray
                self.toolButton_7.setStyleSheet("background-color: light gray")#set as gray
    def freq32(self):#method for timer object 32Hz
        if (self.show_ch1_7.isChecked()) :#if color position is off
            if self.flag32: #blinking condition On
                self.toolButton.setStyleSheet("background-color : yellow")#set as yellow
                self.toolButton_6.setStyleSheet("background-color : yellow")#set as yellow
            else:#blinking condition Off
                    self.toolButton.setStyleSheet("background-color: light gray")#set as gray
                    self.toolButton_6.setStyleSheet("background-color: light gray")#set as gray
            self.flag32 = not self.flag32
        else:#blinking condition Off
            if (self.show_ch1_6.isChecked()) ==False:
                self.toolButton.setStyleSheet("background-color: light gray")#set as gray
                self.toolButton_6.setStyleSheet("background-color: light gray")#set as gray
    # method called by time
    def showTime(self):
        # getting current time
        current_time = QTime.currentTime()
        # converting QTime object to string
        label_time = current_time.toString('hh:mm:ss')
        # showing it to the label
        self.label_3.setText(label_time)
    def getdata(self):   # method called by get data
        frequency = 0.5 #frequency
        new = math.sin(time.time()*frequency*2*math.pi)
        self.graphicsView.setLabel('left', self.comboBox_6.currentText(), '.')#signal initialization function
        if len(self.data1)>7: #select EEG band
            new=self.data1[0]
            if self.comboBox_7.currentText()=='Delta (0.5-3 Hz)':
                    new=self.data1[0]
            if self.comboBox_7.currentText()=='Theta (4-7 Hz':
                    new=self.data1[1]
            if self.comboBox_7.currentText()=='Alpha (8-12 Hz)':
                    new=self.data1[2]
            if self.comboBox_7.currentText()=='Beta (13-25 Hz)':
                    new=self.data1[3]
            print(new)
        return new
    def updateplot(self):     # method called by plot
        self.databuffer.append( self.getdata()) #data buffer
        self.y = self.databuffer #y
        self.curve.setData(self.x, self.y) #plot data
    def getdata2(self):   # method called by get data
        frequency = 0.5 #frequency
        new = math.sin(time.time()*frequency*2*math.pi)  #signal initialization function
        self.graphicsView_2.setLabel('left', self.comboBox_7.currentText(), '.')
        if len(self.data2)>7: #select EEG band
            new=self.data2[4]
            if self.comboBox_7.currentText()=='Delta (0.5-3 Hz)':
                    new=self.data1[4]
            if self.comboBox_7.currentText()=='Theta (4-7 Hz':
                    new=self.data1[5]
            if self.comboBox_7.currentText()=='Alpha (8-12 Hz)':
                    new=self.data1[6]
            if self.comboBox_7.currentText()=='Beta (13-25 Hz)':
                    new=self.data1[7]
            print(new)
        return new
    def updateplot2(self):     # method called by plot
        self.databuffer2.append( self.getdata2()) #data buffer
        self.y2 = self.databuffer2 #y
        self.curve2.setData(self.x2, self.y2) #plot data
        #starts the game and wait until the user wants to exit
    def on_btn_human_click(self):
        self.setVisible(False)
        main.run_game(ai=1)
        #starts the game by AI and wait until the user wants to exit
    def on_btn_AI_click(self):
        self.setVisible(False)
        main.run_game(ai=None)
        self.setVisible(True)   
        #method for configurtion of mainwindow
    def UiComponents(self):
                # label height and width for robot
                self.l_width = 80
                self.l_height = 40    
                self.label_17.setGeometry(500, 500,  self.l_width, self.l_height)  #set Geometry for robot
                #set StyleSheet for robot
                self.label_17.setStyleSheet("QLabel"
        								"{"
        								"border : 1px solid darkgreen;"
        								"background : lightgreen;"
        								"}")  
                # label height and width for goal
                self.l_width_1 = 20
                self.l_height_1 = 20 
                #set random Geometry for goal
                my_number1 = numpy.random.uniform(0, 400)     
                my_number2 = numpy.random.uniform(0, 400)        
                self.label_18.setGeometry(int(my_number1), int(my_number2), self.l_width_1, self.l_height_1)   
                #set StyleSheet for goal
                self.label_18.setStyleSheet("QLabel"
        								"{"
        								"border : 4px solid darkgreen;"
        								"background : lightred;"
        								"}")
    # get the current co-ordinates of the robot
    def keyPressEvent(self, event):
            x = self.label_17.x()     		# X Co-ordinate robot
            y = self.label_17.y()     		# Y Co-ordinate robot
    		# condition if keys are pressed
            if (self.show_ch1_5.isChecked()) : #condition if model are tested or trained
                if event.key()==Qt.Key_0:
                        if self.label_14.text()=='راست': # right arrow pressed
                            if x < self.w_width - self.l_width:# if right end position is attained
                                self.label_17.move(x + self.speed, y)  
                        if self.label_14.text()=='چپ': #left arrow pressed
                            if x > 0:# if left end position is attained
                                self.label_17.move(x - self.speed, y)
                        if self.label_14.text()=='بالا': #right arrow pressed
                                                if y > 0:# if top end position is attained
                                                    self.label_17.move(x, y - self.speed)      
                        if self.label_14.text()=='پایین': # bottom arrow pressed
                            if y < self.w_height - self.l_height:# if bottom end position is attained
                                self.label_17.move(x, y + self.speed)
                        if self.label_14.text()=='جهت':# if non-action
                            print('waitting...')
            else:
               if event.key() == Qt.Key_8 or event.key() ==Qt.Key_Up or event.key() ==Qt.Key_W:
        			# if top position is attained by numeber 8 or W from keyboard
                    self.label_14.setText('بالا')# set top as label
                    # if bottom end position is attained
                    if y > 0:
                        self.label_17.move(x, y - self.speed)
        		# if down arrow key is pressed by numeber 2 or Z from keyboard
               elif event.key() == Qt.Key_2 or event.key() ==Qt.Key_Down or event.key() ==Qt.Key_Z:
                    self.label_14.setText('پایین')# set bottem as label
        			# if bottom position is attained
        			# for bottom point, bottom co-ordinate will be height of window - height of label
                    if y < self.w_height - self.l_height:
                        self.label_17.move(x, y + self.speed)
        		# if left arrow key is pressed by numeber 4 or A from keyboard
               elif event.key() == Qt.Key_4 or event.key() ==Qt.Key_Left or event.key() ==Qt.Key_A:
                    self.label_14.setText('چپ')# set left as label
        			# if left end position is attained
                    if x > 0:
                        self.label_17.move(x - self.speed, y)
        		# if down arrow key is pressed by numeber 6 or S from keyboard
               elif event.key() == Qt.Key_6 or event.key() ==Qt.Key_Right or event.key() ==Qt.Key_S:
                    self.label_14.setText('راست')# set right as label
                    #if right end position is attained
        			# for right end point, right co-ordinate will be width of window - width of label
                    if x < self.w_width - self.l_width:
                        self.label_17.move(x + self.speed, y)
               elif event.key() == Qt.Key_5:
                   self.label_14.setText('جهت')# set non-action as label
    def color(self):# Set color position 
        if (self.show_ch1_6.isChecked()) :
            self.toolButton_2.setStyleSheet("background-color : red")
            self.toolButton_5.setStyleSheet("background-color : red")
            self.toolButton_3.setStyleSheet("background-color : green")
            self.toolButton_8.setStyleSheet("background-color : green")
            self.toolButton_4.setStyleSheet("background-color : blue")
            self.toolButton_7.setStyleSheet("background-color : blue")
            self.toolButton.setStyleSheet("background-color : yellow")
            self.toolButton_6.setStyleSheet("background-color : yellow")
        else:
            self.toolButton_2.setStyleSheet("background-color: light gray")
            self.toolButton_5.setStyleSheet("background-color: light gray")
            self.toolButton_3.setStyleSheet("background-color: light gray")
            self.toolButton_8.setStyleSheet("background-color: light gray")
            self.toolButton_4.setStyleSheet("background-color: light gray")
            self.toolButton_7.setStyleSheet("background-color: light gray")
            self.toolButton.setStyleSheet("background-color: light gray")
            self.toolButton_6.setStyleSheet("background-color: light gray")
    def hide_word(self):# hide word of hodhod project
        print('hide word')
    def hide_sound(self):# hide sound of hodhod project
        if (self.show_ch1_2.isChecked()) :
            print('sound')
        else :
            print('sound')    
    def hide_image(self):# hide image of hodhod project
        if (self.show_ch1_3.isChecked()) :
            pixmap = QPixmap('Jungle.jpeg') #box for image showing
            self.label_16.setPixmap(pixmap)            
            self.label_16.show()            
        else :
            self.label_16.hide()            
    def download_arduino(self):#download arduino package
        toolbar_width = 40      # setup toolbar
        sys.stdout.write("[%s]" % (" " * toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['
        for i in range(toolbar_width):
            os.system('"arduino-cli core install arduino:avr"') # do real work here
            # update the bar
            sys.stdout.write("-")
            sys.stdout.flush()
        sys.stdout.write("]\n"+"---finish---")
    def hide1(self ) : #hide plot
        if (self.show_ch1.isChecked()) :
            self.graphicsView.hide()
        else :
            self.graphicsView.show()
    def loop_finished(self):#messege of finishing for data loop
        print('Looped Finished')
    def start_loop(self):# start data loop
    
        self.worker = Worker()  # a new worker class create to perform those tasks
        self.thread = QThread()  # a new thread class create to run our background tasks in
        self.worker.moveToThread(self.thread)  # move the worker into the thread, do this first before connecting the signals
        self.thread.started.connect(self.worker.work) # begin our worker object's loop when the thread starts running
        self.worker.intReady.connect(self.onIntReady)# pure data collection for prediction connected
        # self.worker.intReady.connect(self.get_sample)

        self.worker.finished.connect(self.loop_finished)  # do something in the gui when the worker loop ends
        self.worker.finished.connect(self.thread.quit)  # tell the thread it's time to stop running
        self.worker.finished.connect(self.worker.deleteLater)  # have worker mark itself for deletion
        self.thread.finished.connect(self.thread.deleteLater)  # have thread mark itself for deletion
        # make sure those last two are connected to themselves or you will get random crashes
        self.thread.start()
        print('data acquisition ...')
        self.textBrowser.setText('در حال دریافت داده...')
        self.label_5.setText("ارتباط برقرار شد!")
        self.label_5.setStyleSheet('color: green')
    def stop_loop(self):#stop data collection loop
        self.worker.working = False    
        self.textBrowser.setText('توقف! کلید "شروع" را برای اتصال دوباره کلیک کنید...')
        if not ports:
            self.textBrowser.setText('توقف! کلید "شروع" را برای اتصال دوباره کلیک کنید...')
    def onIntReady(self, i):# pure data collection for prediction
        # self.progressBar.setValue(int(1-int(self.worker.li[-1][0])/200)*100)
        #print(int(1-int(self.worker.li[-1][0])/200)*100)
        self.progressBar.setValue(int((1-int(self.worker.li[-1][0])/200)*100))
        print(((1-int(self.worker.li[-1][0])/200)*100))
        if (self.show_ch1_5.isChecked()) and len(self.worker.li[-1])>10 and len(self.worker.li[-3])>10 and len(self.worker.li[-2])>10:
            #collecte three step to predect
            data=[float(i) for i in self.worker.li[-1][3:11]]
            self.data1=[float(i) for i in self.worker.li[-2][3:11]]
            self.data2=[float(i) for i in self.worker.li[-3][3:11]]
            print(self.data2)
            data=[data]+[self.data1]+[self.data2]
            XX=numpy.array(data)
            Y_predict = joblib_model.predict(XX)#Data feed to model for prediction
            keyy=['Left','Right','Up','Down','non-action']# prediction label
            key=keyy[int(Y_predict[0])]#prediction 
            print('predicted label: '+ key)
            #set prediction label for txt file
            if keyy[int(Y_predict[0])]==keyy[0]:
                self.label_14.setText('چپ')
            if  keyy[int(Y_predict[0])]==keyy[1]:
                self.label_14.setText('راست')
            if  keyy[int(Y_predict[0])]==keyy[2]:
                self.label_14.setText('بالا')
            if  keyy[int(Y_predict[0])]==keyy[3]:
                self.label_14.setText('پایین')
            if  keyy[int(Y_predict[0])]==keyy[4]:
                self.label_14.setText('جهت')
        #set prediction label for showing in platform
        if self.label_14.text()=='جهت':
            self.textBrowser.append("{}".format(i)+str('جهت'))
        if self.label_14.text()=='راست':
            self.textBrowser.append("{}".format(i)+str('راست'))
        if self.label_14.text()=='چپ':
            self.textBrowser.append("{}".format(i)+str('چپ'))
        if self.label_14.text()=='بالا':
            self.textBrowser.append("{}".format(i)+str('بالا'))      
        if self.label_14.text()=='پایین':
            self.textBrowser.append("{}".format(i)+str('پایین'))   
        if self.label_14.text()=='جهت':
            self.textBrowser.append("{}".format(i)+str('جهت'))  
    #upload arduino code and prediction model        
    def upload(self):
        if ports:
            os.system('"arduino-cli compile --fqbn arduino:avr:uno --port COM3 Serial_qt"')
            time.sleep(0.4)
            os.system('"arduino-cli upload --fqbn arduino:avr:uno --port COM3 Serial_qt"')
            time.sleep(0.4)
            os.system('"arduino-cli compile --fqbn arduino:avr:uno --port COM3 Brain_qt"')
            time.sleep(0.4)
            os.system('"arduino-cli upload --fqbn arduino:avr:uno --port COM3 Brain_qt"')
            joblib_file = "joblib_model.pkl"
            joblib_model = joblib.load(joblib_file)
    def on_pushButton_4_clicked(self): #show seril messeage
        if self.x != 0:
            self.textBrowser.setText('تنظیمات ذخیره شد!')
        else:
            self.textBrowser.setText('لطفا پورت را وارد کنید!')
    # save collected data in txt file
    def save_sample(self):
            name = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", '/', '.txt')[0]# txt file save as
            with open(str(name), 'w',encoding = 'utf-8') as f:
                    f.write(self.textBrowser.toPlainText()+'.txt')
    # def on_pushButton_2_clicked(self):#show seril messeage
    #     self.textBrowser.setText('توقف! کلید "شروع" را برای اتصال دوباره کلیک کنید...')
    #     print('no porrrrrrrrrrrrrrrrt')
    #     if not ports:
    #         self.textBrowser.setText('توقف! کلید "شروع" را برای اتصال دوباره کلیک کنید...')
    def on_pushButton_clicked(self):#show seril messeage
        print('no porrrrrrrrrrrrrrrrt')
        self.completed = 0
        while self.completed < 100:
            self.completed += 1
            self.progressBar.setValue(self.completed)
        self.textBrowser.setText('در حال دریافت داده...')
        self.label_5.setText("ارتباط برقرار شد!")
        self.label_5.setStyleSheet('color: green')
        self.x = 1
    def on_pushButton_3_clicked(self):#write seril data
        mytext = self.textEdit_2.toPlainText()
        try:
            ser.write(mytext.encode("utf-8"))
        except:print("Sorry ! Serial is not defined")
def appExec(): #exit function
  app = QApplication(sys.argv)
  app.exec_()
  try:
      ser.close()
  except:print("Sorry ! Serial is not defined")
  print("Serial port closed")
# run pyqt plattform    
def run():
    app = QtCore.QCoreApplication.instance()# creat pyqt application class
    if app is None:#debugging 
        app = QtWidgets.QApplication(sys.argv)
    widget = qt()#apply created class
    widget.show() #showing of platforn
    sys.exit(appExec()) #exit
if __name__ == "__main__":
    run()