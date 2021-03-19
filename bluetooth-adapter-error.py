#!python
# ref:https://python-forum.io/Thread-bluetooth-adapter-error

# Start of GS_Timing

use_browser = "chrome"
# use_browser = "firefox"
# for_click_use = "click"
for_click_use = "send_keys"
for_upload_use = "browse"
# for_upload_use = "drag_and_drop"
tick_action = 0

from selenium import webdriver
from selenium.webdriver.common.by import By                             # For WebDriverWait.
from selenium.webdriver.support.ui import WebDriverWait                 # For WebDriverWait.
from selenium.webdriver.support import expected_conditions as EC        # For WebDriverWait.
from selenium.common.exceptions import NoAlertPresentException          # For WebDriverWait.
from selenium.common.exceptions import TimeoutException                 # For WebDriverWait.
from selenium.common.exceptions import StaleElementReferenceException   # For error on line 302.
from selenium.common.exceptions import NoSuchElementException           # For error on line 
from xml.etree import ElementTree as ET
from lxml import etree                      							# For validating XML files.
from lxml.etree import fromstring, tostring
from io import StringIO                    			 					# For passing strings as files to etree.
# from selenium import webdriver
import io                                                               # for io.open(... encoding="utf-8")
import sys                                  							# For handling input. Also for  version_info.
from selenium.webdriver.common.keys import Keys                         # For selecting iframes, and sending RETURN key.
from inspect import currentframe, getframeinfo, stack                   # For linenumber and filename in logmsg.
from queue import Queue                                                 # For whizzer
import logging                                                          # For threading.
import threading                                                        # Ditto
import time                                                             # Ditto
from threading import Thread                                            # Ditto
from queue import Queue                                                 # For messages between threads.
from selenium.webdriver.common.action_chains import ActionChains        # For clicking elements.
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement             # To test type for WebElement
import os.path                                                          # for drag_and_drop
    
"""
GS_timing.py
-create some low-level Arduino-like millis() (milliseconds) and micros() 
 (microseconds) timing functions for Python 
By Gabriel Staples
http://www.ElectricRCAircraftGuy.com 
-click "Contact me" at the top of my website to find my email address 
Started: 11 July 2016 
Updated: 13 Aug 2016 

History (newest on top): 
20160813 - v0.2.0 created - added Linux compatibility, using ctypes, so that it's compatible with pre-Python 3.3 (for Python 3.3 or later just use the built-in time functions for Linux, shown here: https://docs.python.org/3/library/time.html)
-ex: time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
20160711 - v0.1.0 created - functions work for Windows *only* (via the QPC timer)

References:
WINDOWS:
-personal (C++ code): GS_PCArduino.h
1) Acquiring high-resolution time stamps (Windows)
   -https://msdn.microsoft.com/en-us/library/windows/desktop/dn553408(v=vs.85).aspx
2) QueryPerformanceCounter function (Windows)
   -https://msdn.microsoft.com/en-us/library/windows/desktop/ms644904(v=vs.85).aspx
3) QueryPerformanceFrequency function (Windows)
   -https://msdn.microsoft.com/en-us/library/windows/desktop/ms644905(v=vs.85).aspx
4) LARGE_INTEGER union (Windows)
   -https://msdn.microsoft.com/en-us/library/windows/desktop/aa383713(v=vs.85).aspx

-*****https://stackoverflow.com/questions/4430227/python-on-win32-how-to-get-
absolute-timing-cpu-cycle-count
   
LINUX:
-https://stackoverflow.com/questions/1205722/how-do-i-get-monotonic-time-durations-in-python


"""

import ctypes, os 

#Constants:
VERSION = '0.2.0'

#-------------------------------------------------------------------
#FUNCTIONS:
#-------------------------------------------------------------------
#OS-specific low-level timing functions:
if (os.name=='nt'): #for Windows:
    def micros():
        "return a timestamp in microseconds (us)"
        tics = ctypes.c_int64()
        freq = ctypes.c_int64()

        #get ticks on the internal ~2MHz QPC clock
        ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
        #get the actual freq. of the internal ~2MHz QPC clock
        ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq))  
        
        t_us = tics.value*1e6/freq.value
        return t_us
        
    def millis():
        "return a timestamp in milliseconds (ms)"
        tics = ctypes.c_int64()
        freq = ctypes.c_int64()

        #get ticks on the internal ~2MHz QPC clock
        ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
        #get the actual freq. of the internal ~2MHz QPC clock 
        ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq)) 
        
        t_ms = tics.value*1e3/freq.value
        return t_ms

elif (os.name=='posix'): #for Linux:

    #Constants:
    CLOCK_MONOTONIC_RAW = 4 # see <linux/time.h> here: https://github.com/torvalds/linux/blob/master/include/uapi/linux/time.h
    
    #prepare ctype timespec structure of {long, long}
    class timespec(ctypes.Structure):
        _fields_ =\
        [
            ('tv_sec', ctypes.c_long),
            ('tv_nsec', ctypes.c_long)
        ]
        
    #Configure Python access to the clock_gettime C library, via ctypes:
    #Documentation:
    #-ctypes.CDLL: https://docs.python.org/3.2/library/ctypes.html
    #-librt.so.1 with clock_gettime: https://docs.oracle.com/cd/E36784_01/html/E36873/librt-3lib.html #-
    #-Linux clock_gettime(): http://linux.die.net/man/3/clock_gettime
    librt = ctypes.CDLL('librt.so.1', use_errno=True)
    clock_gettime = librt.clock_gettime
    #specify input arguments and types to the C clock_gettime() function
    # (int clock_ID, timespec* t)
    clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

    def monotonic_time():
        "return a timestamp in seconds (sec)"
        t = timespec()
        #(Note that clock_gettime() returns 0 for success, or -1 for failure, in
        # which case errno is set appropriately)
        #-see here: http://linux.die.net/man/3/clock_gettime
        if clock_gettime(CLOCK_MONOTONIC_RAW , ctypes.pointer(t)) != 0:
            #if clock_gettime() returns an error
            errno_ = ctypes.get_errno()
            raise OSError(errno_, os.strerror(errno_))
        return t.tv_sec + t.tv_nsec*1e-9 #sec 
    
    def micros():
        "return a timestamp in microseconds (us)"
        return monotonic_time()*1e6 #us 
        
    def millis():
        "return a timestamp in milliseconds (ms)"
        return monotonic_time()*1e3 #ms 

#Other timing functions:
def delay(delay_ms):
    "delay for delay_ms milliseconds (ms)"
    t_start = millis()
    while (millis() - t_start < delay_ms):
      pass #do nothing 
    return

def delayMicroseconds(delay_us):
    "delay for delay_us microseconds (us)"
    t_start = micros()
    while (micros() - t_start < delay_us):
      pass #do nothing 
    return 

# The following section copied from https://gist.github.com/florentbr/349b1ab024ca9f3de56e6bf8af2ac69e
# from selenium import webdriver
# from selenium.webdriver.remote.webelement import WebElement
import os.path

# JavaScript: HTML5 File drop
# source            : https://gist.github.com/florentbr/0eff8b785e85e93ecc3ce500169bd676
# param1 WebElement : Drop area element
# param2 Double     : Optional - Drop offset x relative to the top/left corner of the drop area. Center if 0.
# param3 Double     : Optional - Drop offset y relative to the top/left corner of the drop area. Center if 0.
# return WebElement : File input
JS_DROP_FILES = "var c=arguments,b=c[0],k=c[1];c=c[2];for(var d=b.ownerDocument||document,l=0;;){var e=b.getBoundingClientRect(),g=e.left+(k||e.width/2),h=e.top+(c||e.height/2),f=d.elementFromPoint(g,h);if(f&&b.contains(f))break;if(1<++l)throw b=Error('Element not interactable'),b.code=15,b;b.scrollIntoView({behavior:'instant',block:'center',inline:'center'})}var a=d.createElement('INPUT');a.setAttribute('type','file');a.setAttribute('multiple','');a.setAttribute('style','position:fixed;z-index:2147483647;left:0;top:0;');a.onchange=function(b){a.parentElement.removeChild(a);b.stopPropagation();var c={constructor:DataTransfer,effectAllowed:'all',dropEffect:'none',types:['Files'],files:a.files,setData:function(){},getData:function(){},clearData:function(){},setDragImage:function(){}};window.DataTransferItemList&&(c.items=Object.setPrototypeOf(Array.prototype.map.call(a.files,function(a){return{constructor:DataTransferItem,kind:'file',type:a.type,getAsFile:function(){return a},getAsString:function(b){var c=new FileReader;c.onload=function(a){b(a.target.result)};c.readAsText(a)}}}),{constructor:DataTransferItemList,add:function(){},clear:function(){},remove:function(){}}));['dragenter','dragover','drop'].forEach(function(a){var b=d.createEvent('DragEvent');b.initMouseEvent(a,!0,!0,d.defaultView,0,0,0,g,h,!1,!1,!1,!1,0,null);Object.setPrototypeOf(b,null);b.dataTransfer=c;Object.setPrototypeOf(b,DragEvent.prototype);f.dispatchEvent(b)})};d.documentElement.appendChild(a);a.getBoundingClientRect();return a;"

def drop_files(element, files, offsetX=0, offsetY=0):
    driver = element.parent
    isLocal = not driver._is_remote or '127.0.0.1' in driver.command_executor._url
    paths = []
    
    # ensure files are present, and upload to the remote server if session is remote
    for file in (files if isinstance(files, list) else [files]) :
        if not os.path.isfile(file) :
            raise FileNotFoundError(file)
        paths.append(file if isLocal else element._upload(file))
    
    value = '\n'.join(paths)
    elm_input = driver.execute_script(JS_DROP_FILES, element, offsetX, offsetY)
    elm_input._execute('sendKeysToElement', {'value': [value], 'text': value})

WebElement.drop_files = drop_files


############################# USAGE EXAMPLE #############################
'''
driver = webdriver.Chrome()

driver.get("https://react-dropzone.js.org/")
dropzone = driver.find_element_by_css_selector("[data-preview='Basic example'] [style]")

# drop a single file
dropzone.drop_files("C:\\temp\\image1.png")

# drop two files
dropzone.drop_files(["C:\\temp\\image1.png", "C:\\temp\\image2.png"])

# drop a file by offset
dropzone.drop_files("C:\\temp\\image1.png", offsetX=25, offsetY=25)
'''
# End of copied section

# The following section was copied from https://sqa.stackexchange.com/questions/22191/is-it-possible-to-automate-drag-and-drop-from-a-file-in-system-to-a-website-in-s
def DropFile(target, filepath, offsetX, offsetY):
    if not filepath.exists():
        logmsg(L_ERROR, "File " + filepath + " does not exist")
    driver = target.getWrappedDriver()
    jse = driver
    wait = WebDriverWait(driver, 30)

    JS_DROP_FILE = """
        var target = arguments[0],
            offsetX = arguments[1],
            offsetY = arguments[2],
            document = target.ownerDocument || document,
            window = document.defaultView || window;
        
        var input = document.createElement('INPUT');
        input.type = 'file';
        input.style.display = 'none';
        input.onchange = function () {
          var rect = target.getBoundingClientRect(),
              x = rect.left + (offsetX || (rect.width >> 1)),
              y = rect.top + (offsetY || (rect.height >> 1)),
              dataTransfer = { files: this.files };
        
          ['dragenter', 'dragover', 'drop'].forEach(function (name) {
            var evt = document.createEvent('MouseEvent');
            evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
            evt.dataTransfer = dataTransfer;
            target.dispatchEvent(evt);
          });
        
          setTimeout(function () { document.body.removeChild(input); }, 25);
        };
        document.body.appendChild(input);
        return input;";
        """

    input = jse.execute_script(JS_DROP_FILE, target, offsetX, offsetY)
    input.sendKeys(filepath.getAbsoluteFile().toString())
    wait.until(EC.stalenessOf(input))
# End of copied section.

# The following section copied from https://stackoverflow.com/questions/43382447/python-with-selenium-drag-and-drop-from-file-system-to-webdriver
JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
      var rect = target.getBoundingClientRect(),
          x = rect.left + (offsetX || (rect.width >> 1)),
          y = rect.top + (offsetY || (rect.height >> 1)),
          dataTransfer = { files: this.files };

      ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
      });

      setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
"""

def drag_and_drop_file(drop_target, path):
    driver = drop_target.parent
    file_input = driver.execute_script(JS_DROP_FILE, drop_target, 0, 0)
    file_input.send_keys(path)  
# End of copied section.
    
#-------------------------------------------------------------------
#EXAMPLES:
#-------------------------------------------------------------------
#Only executute this block of code if running this module directly,
#*not* if importing it
#-see here: http://effbot.org/pyfaq/tutor-what-is-if-name-main-for.htm
# if __name__ == "__main__": #if running this module as a stand-alone program
if False:

    #print loop execution time 100 times, using micros()
    tStart = micros() #us
    for x in range(0, 100):
        tNow = micros() #us
        dt = tNow - tStart #us; delta time 
        tStart = tNow #us; update 
        print("dt(us) = " + str(dt))

    #print loop execution time 100 times, using millis()
    print("\n")
    tStart = millis() #ms
    for x in range(0, 100):
        tNow = millis() #ms
        dt = tNow - tStart #ms; delta time 
        tStart = tNow #ms; update 
        print("dt(ms) = " + str(dt))
        
    #print a counter once per second, for 5 seconds, using delay 
    print("\nstart")
    for i in range(1,6):
        delay(1000)
        print(i)

    #print a counter once per second, for 5 seconds, using delayMicroseconds
    print("\nstart")
    for i in range(1,6):
        delayMicroseconds(1000000)
        print(i)
# End of GS_timing

timenow = micros()/1000000.
import time
# import GS_timing                                                        # For microsecond timestamps.
if use_browser == "chrome":
    from webdriver_manager.chrome import ChromeDriverManager
elif use_browser == "firefox":
    from webdriver_manager.firefox import GeckoDriverManager
else:
    logmsg(L_ERROR, "Browser " + use_browser + " is not supported")

email = ""
password = ""
# image_path = "C:/Users/RowanB/Documents/My_Scripts NEW/Mock Exams/Exam Pictures/"
image_path = "D:/XPS_8700 Extended Files/Users/RowanB/Documents/My_Scripts NEW/Mock Exams/Exam Pictures/"
discipline = "hang-gliding"
level = "club-pilot"
topics = ["airmanship", "air-law", "principles of flight", "meteorology"]
from datetime import datetime
now = datetime.now()
year = now.year % 100
month = now.month
day = now.day
logfile = "logs/exam_log" + format('{:02}{:02}{:02}'.format(year, month, day)) + '.log'
L_TRACE = 1				        # Trace information to allow the developer to see exactly what's going on. Not for normal use.
L_DEBUG = 2				        # Logs included by the developer to give him information to help debug a problem. Disabled in a full debugged system.
L_VERBOSE = 3				    # More verbose information, which will normally _not_ be logged in a fully released system.
L_INFO = 4				        # Useful information on what happened. This should not be too verbose, because it will be logged in the log file.
L_USER_WARNING = 5				# A warning to the user, who may have made an error, but could continue if he's sure he's right.
L_USER_ERROR = 6                # The user made an error (e.g. entered invalid data) or did something unexpected and should be asked to try again.
L_WARNING = 7				    # A system warning for the developer to investigate. The application can continue.
L_ERROR = 8                     # A recoverable system/software error, for the developer to investigate. These should never occur in a fully debugged system.
L_FATAL = 9				        # The application cannot continue, and will be forced to quit.
L_NONE = 10				        # Do not log any errors. There should be no logmsg() calls with severity set >= this.

def logmsg(sev, msg):
    if not ('logf' in vars() or 'logf' in globals()):
        logf = open(logfile, "a")
    now = datetime.now()
    caller = getframeinfo(stack()[1][0])
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:02}.{:02.3f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.second, now.microsecond/1000, sev, msg))
    # logf.write('{} {} {}'.format(now.strftime("%y-%m-%d %H:%M:%S.%03f"), sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:02.3f} {} {}\n'.format(year, month, day, now.hour, now.minute, float(now.second), sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:02}.{:.3f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.second, now.microsecond/1000, sev, msg))
    # logf.write("Time is " + str(now) + "\n")
    logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:02}.{:3.0f} line: {:5} file: {:15s} {} {}\n'.format(year, month, day, now.hour, now.minute, now.second, now.microsecond/1000, caller.lineno, caller.filename, sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:02} {} {}\n'.format(year, month, day, now.hour, now.minute, now.second, sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:03f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.microsecond/1000, sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:.3f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.microsecond/1000, sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:.0f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.microsecond/1000, sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:.0f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.second, now.microsecond/1000, sev, msg))
    # logf.write('{:02}-{:02}-{:02} {:02}:{:02}:{:.0f} {} {}\n'.format(year, month, day, now.hour, now.minute, now.second, now.microsecond/1000, sev, msg))
    if sev >= L_ERROR:
        print("Fatal error at line " + str(caller.lineno) + ": " + msg)

def stringify(element):
    if element == None:
        return "No such element"
    # if isinstance(element, selenium.webdriver.remote.webelement.WebElement):
    if True:
        logmsg(L_TRACE, "WebElement found: " + element.get_attribute("outerHTML"))
        try:
            msg = "tag: " + str(element.tag_name)
            # msg = "tag: " + str(element.tag)
            # msg += ", xpath: " + getAbsXpath(element)
            # msg += ", name: " + str(element.get_attribute('name'))
            msg += ", name: " + str(element.get_attribute('name'))
            msg += ", id: " + str(element.get_attribute('id'))
            msg += ", href: " + str(element.get_attribute('href'))
            msg += ", src: " + str(element.get_attribute('src'))
            msg += ", class: " + str(element.get_attribute('class'))
            msg += ", style: " + str(element.get_attribute('style'))
            return msg
        except StaleElementReferenceException:
            logmsg(L_ERROR, "Stale element reference")
            return "Stale element"
    else:
        logmsg(L_ERROR, str(type(element)) + " not supported")
        return "Unsupported type"

# image = question.find('image')
# add_image_xpath = "//div[@id='card-" + str(q_index) + "']/div[@class='cloudinary-widget-container']/a[@class='upload-widget-opener']"
# upload(image, add_image_xpath)
# @param lxml.etree.Element image 
#   the XML element from the XML file that contains (as its text) file name of the file to be uploaded.
# @param str add_image_xpath 
#   the XPATH that will uniquely find the web element which needs to be clicked to start the file upload sequence.
def upload(image, add_image_xpath):
    # Upload file using Cloudinary widget.
    # If there is a file, add it.
    # Click where it says "Click to add image".
    if image != None:
        image_text = image.text
        if len(image_text) > 0:
            if (True):
                logmsg(L_TRACE, "Locating Add Image button")
                driver.switch_to.parent_frame()
                add_image_button = driver.find_element_by_xpath("//a[contains(text(),'Click to add image')]")
                logmsg(L_TRACE, "Clicking Add Image button")
                # add_image_button.click()
                add_image_button.send_keys(Keys.RETURN)
                logmsg(L_TRACE, "Locating Browse button")
                # Switch to the frame containing the Browse button.
                logmsg(L_TRACE, "Switching to frame 10")
                driver.switch_to.frame(10)
                # time.sleep(2)
                browse_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='cloudinary_fileupload']")))
                # browse_button = driver.find_element_by_xpath("//input[@class='cloudinary_fileupload']")
                logmsg(L_TRACE, "Clicking Browse button")
                browse_button.click()
                logmsg(L_TRACE, "Uploading image file")
                logmsg(L_TRACE, "Sending file path " + image_path + image_text + " to Browse button")
                '''
                if (len(buttons)<=0):
                    try:
                        button = driver.find_element(By.NAME, "file")
                    except NoSuchElementException:
                        logmsg(L_ERROR, "Failed to find Browse button")
                    button.send_keys(image_path + image_text)
                    logmsg(L_TRACE, "Sending image path to " + stringify(button))
                    button.send_keys(image_path + image_text)
                else:
                '''
                # buttons[0].click()
                logmsg(L_TRACE, "Sending image path to " + stringify(browse_button))
                browse_button.send_keys(image_path + image_text)
                logmsg(L_TRACE, "Locating the Skip button")
                # Get all the elements in the frame.
                elements = driver.find_elements_by_xpath('//*')
                num_elems = len(elements)
                # Find the skip button.
                for index in range(num_elems):
                    element = elements[index]
                    if element.get_attribute('data-test') == 'skip-button':
                        break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", data-test: " + str(element.get_attribute('data-test'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the skip button.
                logmsg(L_TRACE, "Clicking skip button ")
                element.click()
                driver.switch_to.default_content()
            else:
                logmsg(L_TRACE, "Looking for Add Image button via XPATH '" + add_image_xpath + "'")
                # log_elements()
                add_image = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, add_image_xpath)))
                logmsg(L_TRACE, "Clicking Add Image button")
                # add_image.click()
                add_image.send_keys(Keys.RETURN)
                # time.sleep(5)
                max_tries = 5
                trynum = 0
                for trynum in range (max_tries):
                    try:
                        # Find the frame containing the Browse button.
                        frameList = driver.find_elements_by_xpath("//iframe")
                        numOfFrames = len(frameList)
                        logmsg(L_TRACE, "Page has " + str(numOfFrames) + " frames")
                        frameNum = -1
                        for index in range(numOfFrames):
                            logmsg(L_TRACE, "Frame " + str(index) + " id= " + frameList[index].get_attribute('id') + ", src= " + frameList[index].get_attribute('src') + ", name= " + frameList[index].get_attribute('name'))
                            if (frameList[index].get_attribute('src')[0:30] == "https://widget.cloudinary.com/"):
                                frameNum = index
                        if (frameNum < 0):
                            logmsg(L_ERROR, "No frames found")
                            raise FrameNotFound("A frame with src starting 'https://widget.cloudinary.com/' was not found")
                        else:
                            break
                    except FrameNotFound:
                        logmsg(L_TRACE, "FrameNotFound exception raised")
                if frameNum < 0:
                    logmsg(L_ERROR, "Frame with src starting 'https://widget.cloudinary.com/' not found after " + str(max_tries) + " tries")
                # Switch to the frame containing the Browse button.
                logmsg(L_TRACE, "Switching to frame " + str(frameNum))
                driver.switch_to.frame(frameNum)
                # time.sleep(2)
                # Find all elements in this frame.
                elementList = driver.find_elements_by_xpath("//*")
                logmsg(L_TRACE, "str is " + str(type(str)) + ", str() is " + str(type(str())))
                logmsg(L_TRACE, str(len(elementList)) + " elements found")
                for index in range(len(elementList)):
                    # List properties of each element (for debugging).
                    elementList = driver.find_elements_by_xpath("//*")
                    logmsg(L_TRACE, "index = " + str(index) + ", " + str(len(elementList)) + " elements found")
                    if index >= len(elementList):
                        # The element we are trying to access no longer exists.
                        break
                    str_index = str(index);
                    try:
                        msg = "Index: " + str_index + ", tag: " + str(elementList[index].tag_name)
                        msg += ", name: " + str(elementList[index].get_attribute('name'))
                        msg += ", id: " + elementList[index].get_attribute('id')
                        msg += ", href: " + str(elementList[index].get_attribute('href'))
                        msg += ", src: " + str(elementList[index].get_attribute('src'))
                        msg += ", class: " + str(elementList[index].get_attribute('class'))
                        msg += ", style: " + str(elementList[index].get_attribute('style'))
                        logmsg(L_TRACE, msg)
                    except StaleElementReferenceException:
                        logmsg(L_TRACE, "StaleElementReferenceException raised")
                        continue
                # Find the Browse button.
                buttons = driver.find_elements_by_class_name('cloudinary_fileupload')
                logmsg(L_TRACE, "There are " + str(len(buttons)) + " buttons")
                # There should be only one button. List all buttons found (for debugging).
                for index in range(len(buttons)):
                    str_index = str(index);
                    msg = "Index: " + str_index + ", tag: " + str(buttons[index].tag_name)
                    msg += ", name: " + str(buttons[index].get_attribute('name'))
                    msg += ", id: " + buttons[index].get_attribute('id')
                    msg += ", href: " + str(buttons[index].get_attribute('href'))
                    msg += ", src: " + str(buttons[index].get_attribute('src'))
                    msg += ", class: " + str(buttons[index].get_attribute('class'))
                    msg += ", style: " + str(buttons[index].get_attribute('style'))
                    logmsg(L_TRACE, msg)
                '''
                # Get the list of iframes present in the current frame using tag "iframe".
                seq = driver.find_elements_by_tag_name('iframe')
                logmsg(L_TRACE, "No of iframes present in the current frame are: " + str(len(seq)))
                # Try each frame in turn
                for index in range(len(seq)):
                    driver.switch_to.default_content()
                    iframe = driver.find_elements_by_tag_name('iframe')[index]
                    driver.switch_to.frame(iframe)
                    driver.implicitly_wait(30)
                    #highlight the contents of the selected iframe
                    driver.find_element_by_tag_name('a').send_keys(Keys.CONTROL, 'a')
                    time.sleep(2)
                    # undo the selection within the iframe
                    driver.find_element_by_tag_name('p').click()
                    driver.implicitly_wait(30)
                # sample_image = "D:/XPS_8700 Extended Files/Users/RowanB/Documents/Dropbox/Dropbox/My_Scripts/Mock Exams/Exam Pictures/chart2.jpg"
                # input("1. Press Enter to continue...")
                frameinfo = getframeinfo(currentframe())
                print('\aLine: ' + str(frameinfo.lineno))
                time.sleep(5)
                '''
                # Send file path to Browse button.
                logmsg(L_TRACE, "Frame source is: " + driver.page_source)
                logmsg(L_TRACE, "Sending file path " + image_path + image_text + " to Browse button")
                if (len(buttons)<=0):
                    try:
                        button = driver.find_element(By.NAME, "file")
                    except NoSuchElementException:
                        logmsg(L_ERROR, "Failed to find Browse button")
                    button.send_keys(image_path + image_text)
                    logmsg(L_TRACE, "Sending image path to " + stringify(button))
                    button.send_keys(image_path + image_text)
                else:
                    # buttons[0].click()
                    logmsg(L_TRACE, "Sending image path to " + stringify(buttons[0]))
                    buttons[0].send_keys(image_path + image_text)
                # Get all the elements in the frame.
                elements = driver.find_elements_by_xpath('//*')
                num_elems = len(elements)
                # Find the skip button.
                for index in range(num_elems):
                    element = elements[index]
                    if element.get_attribute('data-test') == 'skip-button':
                        break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", data-test: " + str(element.get_attribute('data-test'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the skip button.
                logmsg(L_TRACE, "Clicking skip button ")
                element.click()
                driver.switch_to.default_content()
        else:
            logmsg(L_ERROR, "image_text length must be > 0, was " + str(len(image_text)))
    else:
        logmsg(L_TRACE, "There was no image element in the XML file")
'''
    @function upload2
    uploads an image whose name and path relative to the images_path are in the XML element 'image'
    using the Add Image button with xpath add_image_xpath
'''        
def upload2(image, add_image_xpath, upload_xpath):
    # Upload file using Cloudinary widget.
    # If there is a file, add it.
    # Click where it says "Click to add image".
    if image != None:
        image_text = image.text
        if len(image_text) > 0:
            if (True):
                framenum = 0
                logmsg(L_TRACE, "Locating 'Add Image' button")
                driver.switch_to.parent_frame()
                # add_image_button = driver.find_element_by_xpath("//a[contains(text(),'Click to add image')]")
                add_image_button = None
                try:
                    # add_image_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Click to add image')]")))
                    add_image_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, add_image_xpath)))
                except TimeoutException:
                    logmsg(L_TRACE, "Timeout exception occurred, continuing")
                if add_image_button == None:
                    add_image_button = driver.find_element_by_xpath("//a[@class='upload-widget-opener']")
                    add_image_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='upload-widget-opener']")))
                logmsg(L_TRACE, "Add Image button is: " + add_image_button.get_attribute("outerHTML"))
                logmsg(L_TRACE, "Clicking 'Add Image' button")
                # add_image_button.click()
                # add_image_button.send_keys(Keys.RETURN)
                driver.execute_script("arguments[0].click();", add_image_button)
                driver.switch_to.default_content()
                drag_heres = driver.find_elements_by_xpath('//div[@data-test="drag-area"]')
                if len(drag_heres) > 0:
                    if len(drag_heres) > 1:
                        logmsg(L_ERROR, "Expecting only one drag-here element, " + str(len(drag_heres)) + " found")
                    drag_here = drag_heres[0]
                    found = 1
                else:
                    found = 0
                if found == 0:
                    logmsg(L_TRACE, "No drag-here elements found in master frame, looking in sub-frames")
                    frames = driver.find_elements_by_xpath("//iframe")
                    logmsg(L_TRACE, "Found " + str(len(frames)) + " subframes in parent frame number " + str(framenum))
                    for framenum in range(len(frames)):
                        logmsg(L_TRACE, "Trying subframe number " + str(framenum))
                        driver.switch_to.frame(framenum)
                        drag_heres = driver.find_elements_by_xpath('//div[@data-test="drag-area"]')
                        if len(drag_heres) > 0:
                            if len(drag_heres) > 1:
                                logmsg(L_ERROR, "Expecting only one drag-here element, " + str(len(drag_heres)) + " found in subframe " + str(framenum))
                                found = 1
                                break
                            logmsg(L_TRACE, "One drag-here element found in subframe number " + str(framenum))
                            drag_here = drag_heres[0]
                            found = 1
                            break
                        else:
                            logmsg(L_TRACE, "No drag-here elements found in subframe " + str(framenum))
                            found = 0
                        if found == 1:
                            break
                        else:
                            driver.switch_to.parent_frame()
                            continue
                    if found == 0:
                        logmsg(L_ERROR, "Failed to find drag-here element in any top level frame")
                    else:
                        logmsg(L_TRACE, "Found drag-here element in subframe " + str(framenum))
                '''
                driver.switchTo().frame(driver.findElement(By.id("f2")).findElement(By.id("f2.1")).findElement(By.id("f2.2")));
                wait = WebDriverWait(driver, 10)
                driver.find_element_by_link_text("http://link.com'").click()
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.dismiss()
                driver.switch_to.default_content()
                driver.switchTo().frame(driver.findElement(By.id("f2")).findElement(By.id("f2.1")));
                String text=driver.findElement(By.id("ac")).getText();
                System.out.println(text);
                driver.switch_to.default_content()
                '''
                # drag_heres = driver.find_elements_by_xpath('//div[@data-test="drag-area"]')
                # num = len(drag_heres)
                # if num != 1:
                #    logmsg(L_ERROR, "Expecting only one drag-area element, " + str(num) + " found ")
                #drag_here = drag_heres[0]
                logmsg(L_TRACE, "Dropping file " + image_path + image_text + " on element " + drag_here.get_attribute('outerHTML'))
                # drag_and_drop_file(drag_here, image_path + image_text)
                driver.execute_script("arguments[0].scrollIntoView();", drag_here)
                # drag_here = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//div[@data-test="drag-area"]')))
                # drag_here = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, upload_xpath)))
                drag_here = driver.find_element_by_xpath(upload_xpath)
                driver.execute_script("arguments[0].click();", drag_here)
                drop_files(drag_here, image_path + image_text)
                time.sleep(5)
                logmsg(L_TRACE, "Locating the Skip button")
                # Get all the elements in the frame.
                elements = driver.find_elements_by_xpath('//*')
                num_elems = len(elements)
                # Find the skip button.
                for index in range(num_elems):
                    element = elements[index]
                    if element.get_attribute('data-test') == 'skip-button':
                        break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", data-test: " + str(element.get_attribute('data-test'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the skip button.
                logmsg(L_TRACE, "Clicking skip button ")
                # element.click()
                driver.execute_script("arguments[0].click();", element)
                driver.switch_to.default_content()
            else:
                logmsg(L_TRACE, "Looking for Add Image button via XPATH '" + add_image_xpath + "'")
                # log_elements()
                add_image = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, add_image_xpath)))
                logmsg(L_TRACE, "Clicking Add Image button")
                # add_image.click()
                add_image.send_keys(Keys.RETURN)
                # time.sleep(5)
                max_tries = 5
                trynum = 0
                for trynum in range (max_tries):
                    try:
                        # Find the frame containing the Browse button.
                        frameList = driver.find_elements_by_xpath("//iframe")
                        numOfFrames = len(frameList)
                        logmsg(L_TRACE, "Page has " + str(numOfFrames) + " frames")
                        frameNum = -1
                        for index in range(numOfFrames):
                            logmsg(L_TRACE, "Frame " + str(index) + " id= " + frameList[index].get_attribute('id') + ", src= " + frameList[index].get_attribute('src') + ", name= " + frameList[index].get_attribute('name'))
                            if (frameList[index].get_attribute('src')[0:30] == "https://widget.cloudinary.com/"):
                                frameNum = index
                        if (frameNum < 0):
                            logmsg(L_ERROR, "No frames found")
                            raise FrameNotFound("A frame with src starting 'https://widget.cloudinary.com/' was not found")
                        else:
                            break
                    except FrameNotFound:
                        logmsg(L_TRACE, "FrameNotFound exception raised")
                if frameNum < 0:
                    logmsg(L_ERROR, "Frame with src starting 'https://widget.cloudinary.com/' not found after " + str(max_tries) + " tries")
                # Switch to the frame containing the Browse button.
                logmsg(L_TRACE, "Switching to frame " + str(frameNum))
                driver.switch_to.frame(frameNum)
                # time.sleep(2)
                # Find all elements in this frame.
                elementList = driver.find_elements_by_xpath("//*")
                logmsg(L_TRACE, "str is " + str(type(str)) + ", str() is " + str(type(str())))
                logmsg(L_TRACE, str(len(elementList)) + " elements found")
                for index in range(len(elementList)):
                    # List properties of each element (for debugging).
                    elementList = driver.find_elements_by_xpath("//*")
                    logmsg(L_TRACE, "index = " + str(index) + ", " + str(len(elementList)) + " elements found")
                    if index >= len(elementList):
                        # The element we are trying to access no longer exists.
                        break
                    str_index = str(index);
                    try:
                        msg = "Index: " + str_index + ", tag: " + str(elementList[index].tag_name)
                        msg += ", name: " + str(elementList[index].get_attribute('name'))
                        msg += ", id: " + elementList[index].get_attribute('id')
                        msg += ", href: " + str(elementList[index].get_attribute('href'))
                        msg += ", src: " + str(elementList[index].get_attribute('src'))
                        msg += ", class: " + str(elementList[index].get_attribute('class'))
                        msg += ", style: " + str(elementList[index].get_attribute('style'))
                        logmsg(L_TRACE, msg)
                    except StaleElementReferenceException:
                        logmsg(L_TRACE, "StaleElementReferenceException raised")
                        continue
                # Find the Browse button.
                buttons = driver.find_elements_by_class_name('cloudinary_fileupload')
                logmsg(L_TRACE, "There are " + str(len(buttons)) + " buttons")
                # There should be only one button. List all buttons found (for debugging).
                for index in range(len(buttons)):
                    str_index = str(index);
                    msg = "Index: " + str_index + ", tag: " + str(buttons[index].tag_name)
                    msg += ", name: " + str(buttons[index].get_attribute('name'))
                    msg += ", id: " + buttons[index].get_attribute('id')
                    msg += ", href: " + str(buttons[index].get_attribute('href'))
                    msg += ", src: " + str(buttons[index].get_attribute('src'))
                    msg += ", class: " + str(buttons[index].get_attribute('class'))
                    msg += ", style: " + str(buttons[index].get_attribute('style'))
                    logmsg(L_TRACE, msg)
                '''
                # Get the list of iframes present in the current frame using tag "iframe".
                seq = driver.find_elements_by_tag_name('iframe')
                logmsg(L_TRACE, "No of iframes present in the current frame are: " + str(len(seq)))
                # Try each frame in turn
                for index in range(len(seq)):
                    driver.switch_to.default_content()
                    iframe = driver.find_elements_by_tag_name('iframe')[index]
                    driver.switch_to.frame(iframe)
                    driver.implicitly_wait(30)
                    #highlight the contents of the selected iframe
                    driver.find_element_by_tag_name('a').send_keys(Keys.CONTROL, 'a')
                    time.sleep(2)
                    # undo the selection within the iframe
                    driver.find_element_by_tag_name('p').click()
                    driver.implicitly_wait(30)
                # sample_image = "D:/XPS_8700 Extended Files/Users/RowanB/Documents/Dropbox/Dropbox/My_Scripts/Mock Exams/Exam Pictures/chart2.jpg"
                # input("1. Press Enter to continue...")
                frameinfo = getframeinfo(currentframe())
                print('\aLine: ' + str(frameinfo.lineno))
                time.sleep(5)
                '''
                # Send file path to Browse button.
                logmsg(L_TRACE, "Frame source is: " + driver.page_source)
                logmsg(L_TRACE, "Sending file path " + image_path + image_text + " to Browse button")
                if (len(buttons)<=0):
                    try:
                        button = driver.find_element(By.NAME, "file")
                    except NoSuchElementException:
                        logmsg(L_ERROR, "Failed to find Browse button")
                    button.send_keys(image_path + image_text)
                    logmsg(L_TRACE, "Sending image path to " + stringify(button))
                    button.send_keys(image_path + image_text)
                else:
                    # buttons[0].click()
                    logmsg(L_TRACE, "Sending image path to " + stringify(buttons[0]))
                    buttons[0].send_keys(image_path + image_text)
                # Get all the elements in the frame.
                elements = driver.find_elements_by_xpath('//*')
                num_elems = len(elements)
                # Find the skip button.
                for index in range(num_elems):
                    element = elements[index]
                    if element.get_attribute('data-test') == 'skip-button':
                        break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", data-test: " + str(element.get_attribute('data-test'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the skip button.
                logmsg(L_TRACE, "Clicking skip button ")
                element.click()
                driver.switch_to.default_content()
        else:
            logmsg(L_ERROR, "image_text length must be > 0, was " + str(len(image_text)))
    else:
        logmsg(L_TRACE, "There was no image element in the XML file")

def upload3(image, add_image_xpath):
    # Upload file using Cloudinary widget.
    # If there is a file, add it.
    # Click where it says "Click to add image".
    if image != None:
        image_text = image.text
        if len(image_text) > 0:
            if (True):
                logmsg(L_TRACE, "Locating 'Click to add Image' button")
                driver.switch_to.parent_frame()
                add_image_button = driver.find_element_by_xpath("//a[contains(text(),'Click to add image')]")
                logmsg(L_TRACE, "Clicking 'Click to add Image' button")
               # add_image_button.click()
                add_image_button.send_keys(Keys.RETURN)
                DropFile(add_image_button, image_path + image_text, 0, 0)               
                logmsg(L_TRACE, "Locating the Skip button")
                # Get all the elements in the frame.
                # elements = driver.find_elements_by_xpath('//*')
                # num_elems = len(elements)
                # Find the skip button.
                element = driver.find_element_by_xpath('//button[@data-test="skip-button"]')
                # for index in range(num_elems):
                #     element = elements[index]
                #     if element.get_attribute('data-test') == 'skip-button':
                #         break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", data-test: " + str(element.get_attribute('data-test'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the skip button.
                logmsg(L_TRACE, "Clicking skip button")
                # element.click()
                driver.execute_script("arguments[0].click();", element)
                driver.switch_to.default_content()
            else:
                logmsg(L_TRACE, "Looking for Add Image button via XPATH '" + add_image_xpath + "'")
                # log_elements()
                add_image = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, add_image_xpath)))
                logmsg(L_TRACE, "Clicking Add Image button")
                # add_image.click()
                add_image.send_keys(Keys.RETURN)
                # time.sleep(5)
                max_tries = 5
                trynum = 0
                for trynum in range (max_tries):
                    try:
                        # Find the frame containing the Browse button.
                        frameList = driver.find_elements_by_xpath("//iframe")
                        numOfFrames = len(frameList)
                        logmsg(L_TRACE, "Page has " + str(numOfFrames) + " frames")
                        frameNum = -1
                        for index in range(numOfFrames):
                            logmsg(L_TRACE, "Frame " + str(index) + " id= " + frameList[index].get_attribute('id') + ", src= " + frameList[index].get_attribute('src') + ", name= " + frameList[index].get_attribute('name'))
                            if (frameList[index].get_attribute('src')[0:30] == "https://widget.cloudinary.com/"):
                                frameNum = index
                        if (frameNum < 0):
                            logmsg(L_ERROR, "No frames found")
                            raise FrameNotFound("A frame with src starting 'https://widget.cloudinary.com/' was not found")
                        else:
                            break
                    except FrameNotFound:
                        logmsg(L_TRACE, "FrameNotFound exception raised")
                if frameNum < 0:
                    logmsg(L_ERROR, "Frame with src starting 'https://widget.cloudinary.com/' not found after " + str(max_tries) + " tries")
                # Switch to the frame containing the Browse button.
                logmsg(L_TRACE, "Switching to frame " + str(frameNum))
                driver.switch_to.frame(frameNum)
                # time.sleep(2)
                # Find all elements in this frame.
                elementList = driver.find_elements_by_xpath("//*")
                logmsg(L_TRACE, "str is " + str(type(str)) + ", str() is " + str(type(str())))
                logmsg(L_TRACE, str(len(elementList)) + " elements found")
                for index in range(len(elementList)):
                    # List properties of each element (for debugging).
                    elementList = driver.find_elements_by_xpath("//*")
                    logmsg(L_TRACE, "index = " + str(index) + ", " + str(len(elementList)) + " elements found")
                    if index >= len(elementList):
                        # The element we are trying to access no longer exists.
                        break
                    str_index = str(index);
                    try:
                        msg = "Index: " + str_index + ", tag: " + str(elementList[index].tag_name)
                        msg += ", name: " + str(elementList[index].get_attribute('name'))
                        msg += ", id: " + elementList[index].get_attribute('id')
                        msg += ", href: " + str(elementList[index].get_attribute('href'))
                        msg += ", src: " + str(elementList[index].get_attribute('src'))
                        msg += ", class: " + str(elementList[index].get_attribute('class'))
                        msg += ", style: " + str(elementList[index].get_attribute('style'))
                        logmsg(L_TRACE, msg)
                    except StaleElementReferenceException:
                        logmsg(L_TRACE, "StaleElementReferenceException raised")
                        continue
                # Find the Browse button.
                buttons = driver.find_elements_by_class_name('cloudinary_fileupload')
                logmsg(L_TRACE, "There are " + str(len(buttons)) + " buttons")
                # There should be only one button. List all buttons found (for debugging).
                for index in range(len(buttons)):
                    str_index = str(index);
                    msg = "Index: " + str_index + ", tag: " + str(buttons[index].tag_name)
                    msg += ", name: " + str(buttons[index].get_attribute('name'))
                    msg += ", id: " + buttons[index].get_attribute('id')
                    msg += ", href: " + str(buttons[index].get_attribute('href'))
                    msg += ", src: " + str(buttons[index].get_attribute('src'))
                    msg += ", class: " + str(buttons[index].get_attribute('class'))
                    msg += ", style: " + str(buttons[index].get_attribute('style'))
                    logmsg(L_TRACE, msg)
                '''
                # Get the list of iframes present in the current frame using tag "iframe".
                seq = driver.find_elements_by_tag_name('iframe')
                logmsg(L_TRACE, "No of iframes present in the current frame are: " + str(len(seq)))
                # Try each frame in turn
                for index in range(len(seq)):
                    driver.switch_to.default_content()
                    iframe = driver.find_elements_by_tag_name('iframe')[index]
                    driver.switch_to.frame(iframe)
                    driver.implicitly_wait(30)
                    #highlight the contents of the selected iframe
                    driver.find_element_by_tag_name('a').send_keys(Keys.CONTROL, 'a')
                    time.sleep(2)
                    # undo the selection within the iframe
                    driver.find_element_by_tag_name('p').click()
                    driver.implicitly_wait(30)
                # sample_image = "D:/XPS_8700 Extended Files/Users/RowanB/Documents/Dropbox/Dropbox/My_Scripts/Mock Exams/Exam Pictures/chart2.jpg"
                # input("1. Press Enter to continue...")
                frameinfo = getframeinfo(currentframe())
                print('\aLine: ' + str(frameinfo.lineno))
                time.sleep(5)
                '''
                # Send file path to Browse button.
                # logmsg(L_TRACE, "Frame source is: " + driver.page_source)
                source = driver.page_source
                logmsg(L_TRACE, "driver.page_source is type: " + str(type(source)))
                while True:
                    try:
                        logmsg(L_TRACE, "Frame source is: " + source)
                        success = True
                        break
                    except UnicodeEncodeError:
                        success = False
                        source = source[0:int(len(source)/2)]
                logmsg(L_TRACE, "Sending file path " + image_path + image_text + " to Browse button")
                if (len(buttons)<=0):
                    try:
                        button = driver.find_element(By.NAME, "file")
                    except NoSuchElementException:
                        logmsg(L_ERROR, "Failed to find Browse button")
                    button.send_keys(image_path + image_text)
                    logmsg(L_TRACE, "Sending image path to " + stringify(button))
                    button.send_keys(image_path + image_text)
                else:
                    # buttons[0].click()
                    logmsg(L_TRACE, "Sending image path to " + stringify(buttons[0]))
                    buttons[0].send_keys(image_path + image_text)
                # Get all the elements in the frame.
                elements = driver.find_elements_by_xpath('//*')
                num_elems = len(elements)
                # Find the skip button.
                for index in range(num_elems):
                    element = elements[index]
                    if element.get_attribute('data-test') == 'skip-button':
                        break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", data-test: " + str(element.get_attribute('data-test'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the skip button.
                logmsg(L_TRACE, "Clicking skip button ")
                element.click()
                driver.switch_to.default_content()
        else:
            logmsg(L_ERROR, "image_text length must be > 0, was " + str(len(image_text)))
    else:
        logmsg(L_TRACE, "There was no image element in the XML file")

def upload4(image_text, add_image_xpath, upload_xpath):
    """
    Uploads an image using the Cloudinary upload widget.

    Parameters
    ----------
    image : str
        The path of the image file to upload, rerlative to image_path
    add_image_xpath : str
        The xpath of the "Add Image" element on the web page
    upload_xpath : str
        The xpath of the file drop area on the web page

    Returns
    -------
    int
        0       Success
        non-0   Failure
    """
    # Click where it says "Click to add image".
    if image_text != None:
        if len(image_text) > 0:
            framenum = 0
            logmsg(L_TRACE, "Locating 'Add Image' button")
            driver.switch_to.parent_frame()
            # add_image_button = driver.find_element_by_xpath("//a[contains(text(),'Click to add image')]")
            add_image_button = None
            try:
                # add_image_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Click to add image')]")))
                add_image_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, add_image_xpath)))
            except TimeoutException:
                logmsg(L_TRACE, "Timeout exception occurred, continuing")
            if add_image_button == None:
                # add_image_button = driver.find_element_by_xpath(add_image_xpath)
                # add_image_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, add_image_xpath)))
                add_image_button = driver.find_element_by_xpath(add_image_xpath)
            logmsg(L_TRACE, "Add Image button is: " + add_image_button.get_attribute("outerHTML"))
            logmsg(L_TRACE, "Clicking 'Add Image' button")
            driver.execute_script("arguments[0].click();", add_image_button)
            driver.switch_to.default_content()
            # driver.switch_to.frame(9)
            time.sleep(5)
            if for_upload_use == "browse":
                logmsg(L_TRACE, "Looking for Browse button")
                browse_xpath = "//input[@type='file' and @name='file' and @class='cloudinary_fileupload']"
                logmsg(L_TRACE, "Looking for browse button, xpath = " + browse_xpath)
                browses = driver.find_elements_by_xpath(browse_xpath)
                browse = None
                if len(browses) > 0:
                    if len(browses) > 1:
                        logmsg(L_ERROR, "Expecting only one browse button, " + str(len(drag_heres)) + " found")
                    else:
                        logmsg(L_TRACE, "One browse button found")
                    browse = browses[0]
                    found = 1
                else:
                    found = 0
                if found == 0:
                    logmsg(L_TRACE, "No browse buttons found in master frame, looking in sub-frames")
                    frames = driver.find_elements_by_xpath("//iframe")
                    logmsg(L_TRACE, "Found " + str(len(frames)) + " subframes in parent frame number " + str(framenum))
                    for i in range(10):
                        found = 0
                        for framenum in range(len(frames)):
                            if framenum > 0 or i > 0:
                                driver.switch_to.parent_frame()
                            logmsg(L_TRACE, "Try " + str(i) + ", trying subframe number " + str(framenum))
                            frame = frames[framenum]
                            logmsg(L_TRACE, "Frame " + str(framenum) + ": " + frame.get_attribute('outerHTML')[:64])
                            driver.switch_to.frame(framenum)
                            browses = driver.find_elements_by_xpath(browse_xpath)
                            if len(browses) > 0:
                                if len(browses) > 1:
                                    logmsg(L_ERROR, "Expecting only one browse button, " + str(len(drag_heres)) + " found in subframe " + str(framenum))
                                else:
                                    logmsg(L_TRACE, "One browse button found in subframe number " + str(framenum))
                                browse = browses[0]
                                found += 1
                            else:
                                logmsg(L_TRACE, "No browse buttons found in subframe " + str(framenum))
                            continue
                        if found > 0:
                            break
                    if found > 1:
                        logmsg(L_TRACE, str(found) + " browse buttons found in subframes, using the most recent subframe")
                if found <= 0:
                    logmsg(L_ERROR, "No browse button found anywhere")
                if browse == None:
                    logmsg(L_ERROR, "Browse button is None")
                attempts = 0
                result = False;
                while attempts < 5:
                    try:
                        logmsg(L_TRACE, "Try " + str(attempts) + ". Browsing to file " + image_path + image_text + " using element " + browse.get_attribute('outerHTML'))
                        driver.execute_script("arguments[0].scrollIntoView();", browse)
                        browse.send_keys(image_path + image_text)
                        result = True
                        break;
                    except StaleElementReferenceException:
                        attempts += 1
                if not result:
                    logmsg(L_ERROR, "browse element is stale")
                time.sleep(5)
            elif method == "drag":
                logmsg(L_TRACE, "Looking for drag here element, xpath = " + upload_xpath)
                drag_heres = driver.find_elements_by_xpath(upload_xpath)
                if len(drag_heres) > 0:
                    if len(drag_heres) > 1:
                        logmsg(L_ERROR, "Expecting only one drag-here element, " + str(len(drag_heres)) + " found")
                    drag_here = drag_heres[0]
                    found = 1
                else:
                    found = 0
                if found == 0:
                    logmsg(L_TRACE, "No drag-here elements found in master frame, looking in sub-frames")
                    frames = driver.find_elements_by_xpath("//iframe")
                    logmsg(L_TRACE, "Found " + str(len(frames)) + " subframes in parent frame number " + str(framenum))
                    for framenum in range(len(frames)):
                        logmsg(L_TRACE, "Trying subframe number " + str(framenum))
                        driver.switch_to.frame(framenum)
                        elements = driver.find_elements_by_xpath("//*")
                        for i in range(len(elements)):
                            element = elements[i]
                            msg = "Element " + str(i) + " in frame: "
                            msg += str(element.tag_name)
                            msg += ", name: " + str(element.get_attribute('name'))
                            msg += ", data-test: " + str(element.get_attribute('data-test'))
                            msg += ", id: " + element.get_attribute('id')
                            msg += ", href: " + str(element.get_attribute('href'))
                            msg += ", src: " + str(element.get_attribute('src'))
                            msg += ", class: " + str(element.get_attribute('class'))
                            msg += ", style: " + str(element.get_attribute('style'))
                            logmsg(L_DETAIL, msg)
                        drag_heres = driver.find_elements_by_xpath(upload_xpath)
                        if len(drag_heres) > 0:
                            if len(drag_heres) > 1:
                                logmsg(L_ERROR, "Expecting only one drag-here element, " + str(len(drag_heres)) + " found in subframe " + str(framenum))
                                found = 1
                                break
                            logmsg(L_TRACE, "One drag-here element found in subframe number " + str(framenum))
                            drag_here = drag_heres[0]
                            found = 1
                            break
                        else:
                            logmsg(L_TRACE, "No drag-here elements found in subframe " + str(framenum))
                            found = 0
                        if found == 1:
                            break
                        else:
                            driver.switch_to.parent_frame()
                            continue
                    if found == 0:
                        logmsg(L_ERROR, "Failed to find drag-here element in any top level frame")
                    else:
                        logmsg(L_TRACE, "Found drag-here element in subframe " + str(framenum))
                logmsg(L_TRACE, "Dropping file " + image_path + image_text + " on element " + drag_here.get_attribute('outerHTML'))
                driver.execute_script("arguments[0].scrollIntoView();", drag_here)
                # driver.execute_script("arguments[0].click();", drag_here)
                drop_files(drag_here, image_path + image_text)
                time.sleep(5)
            else:
                logmsg(L_FATAL, "Method " + method + " not supported")
            logmsg(L_TRACE, "Locating the Skip button")
            # Get all the elements in the frame.
            elements = driver.find_elements_by_xpath('//*')
            num_elems = len(elements)
            # Find the skip button.
            for index in range(num_elems):
                element = elements[index]
                if element.get_attribute('data-test') == 'skip-button':
                    break
            # Log properties of skip button (for debugging).
            msg = "Button is tag: " + str(element.tag_name)
            msg += ", name: " + str(element.get_attribute('name'))
            msg += ", data-test: " + str(element.get_attribute('data-test'))
            msg += ", id: " + element.get_attribute('id')
            msg += ", href: " + str(element.get_attribute('href'))
            msg += ", src: " + str(element.get_attribute('src'))
            msg += ", class: " + str(element.get_attribute('class'))
            msg += ", style: " + str(element.get_attribute('style'))
            logmsg(L_TRACE, msg)
            # Click the skip button.
            logmsg(L_TRACE, "Clicking skip button ")
            driver.execute_script("arguments[0].click();", element)
            driver.switch_to.default_content()
        else:
            logmsg(L_ERROR, "image_text length must be > 0, was " + str(len(image_text)))
    else:
        logmsg(L_TRACE, "There was no image element in the XML file")

        
def log_elements():
    """
    Logs all the elements present in the current frame.
    """
    elements = driver.find_elements_by_xpath('//*')
    num_elems = len(elements)
    logmsg(L_TRACE, str(num_elems) + " elements found")
    print(str(num_elems) + " iterations")
    for index in range(num_elems):
        if index % 50 == 0:
            print(str(index))
        try:
            element = elements[index]
            msg = "Element " + str(index) + " is tag: " + str(element.tag_name)
            msg += ", name: " + str(element.get_attribute('name'))
            msg += ", id: " + element.get_attribute('id')
            msg += ", href: " + str(element.get_attribute('href'))
            msg += ", src: " + str(element.get_attribute('src'))
            msg += ", class: " + str(element.get_attribute('class'))
            msg += ", style: " + str(element.get_attribute('style'))
            logmsg(L_TRACE, msg)
        except StaleElementReferenceException:
            logmsg(L_ERROR, "Element " + str(index) + " is stale")

def webroot(webelement):
    try:
        parent = webelement.find_element_by_xpath("/..")
    except MyException:
        return webelement
    return webroot(parent)

'''    
generateXPATH(WebElement childElement, String current) {
    String childTag = childElement.getTagName();
    if(childTag.equals("html")) {
        return "/html[1]"+current;
    }
    WebElement parentElement = childElement.findElement(By.xpath("..")); 
    List<WebElement> childrenElements = parentElement.findElements(By.xpath("*"));
    int count = 0;
    for(int i=0;i<childrenElements.size(); i++) {
        WebElement childrenElement = childrenElements.get(i);
        String childrenElementTag = childrenElement.getTagName();
        if(childTag.equals(childrenElementTag)) {
            count++;
        }
        if(childElement.equals(childrenElement)) {
            return generateXPATH(parentElement, "/" + childTag + "[" + count + "]"+current);
        }
    }
    return null;
}
'''

def getRelXpath(self, ancestor):
    num_anc = len(ancestor.find_elements(By.XPATH, "./ancestor::*"))
    num_self = len(self.find_elements(By.XPATH, "./ancestor::*"))
    path = ""
    current = self
    for index in range(num_self - num_anc):
        tag = str(current.get_tag())
        lvl = len(current.find_elements(By.XPATH, "./preceding-sibling::" + tag)) + 1
        path = "/{}[{:d}]{}".format(tag, lvl, path)
        current = current.find_element(By.XPATH, "./parent::*")
    return path;

def getAbsXpath(element):
    logmsg(L_TRACE, "Element is type: " + str(type(element)))
    elements = driver.find_elements(By.XPATH, "./ancestor::*")
    logmsg(L_TRACE, "Found " + str(len(elements)) + " elements")
    elements = element.find_elements(By.XPATH, "./ancestor::*")
    n = len(elements)
    logmsg(L_TRACE, "Found " + str(n) + " elements")
    path = ""
    current = element
    for index in range(n):
        tag = current.tag_name
        logmsg(L_TRACE, " Tag is: " + tag)
        lvl = len(current.find_elements(By.XPATH, "./preceding-sibling::" + tag)) + 1
        path = "/{}[{:d}]{}".format(tag, lvl, path)
        current = current.find_element(By.XPATH, "./parent::*")
    return "/" + current.tag_name + path

def do_answer(a_index):
    global answers, q_index, question_num
    # Do answer.
    answer = answers[a_index]
    if answer.text == None:
        logmsg(L_WARNING, "Question no. " + str(q_index) + " answer no. " + str(a_index) + " has no text")
    else:
        if (a_index > 1):
            # Add another answer field.
            path = "//div[@class='card f-subsection layout-list'][@data-id='" + str(question_num) + "']/div[@class='f-row add-option-row']/div[@class='link-box add-quiz-option']/button"
            logmsg(L_TRACE, "Finding element by xpath " + path)
            add_more = driver.find_element_by_xpath(path)
            driver.execute_script("arguments[0].click();", add_more)
        logmsg(L_TRACE, "Processing question no. " + str(q_index) + ", answer no. " + str(a_index) + ", sending text: " + answer.text)
        print("Processing answer no. " + str(a_index))
        # answer_control = driver.find_element_by_id('widget_cards_attributes_0_options_attributes_0_title')
        answer_control = driver.find_element_by_id('widget_cards_attributes_' + str(question_num) + '_options_attributes_' + str(a_index) + '_title')
        i = 0
        i_max = 100
        while not(answer_control.is_enabled()) and (i < i_max):
            time.sleep(0.1)
            i += 1
        if (i >= i_max):
            logmsg(L_ERROR, "Timeout waiting for answer control")
        driver.execute_script("arguments[0].scrollIntoView();", answer_control)
        answer_control.send_keys(answer.text)
        timenow = micros()
        # input("2. Press Enter to continue...")
        frameinfo = getframeinfo(currentframe())
        # print('\aLine: ' + str(frameinfo.lineno))
        # time.sleep(5)
        correct = False
        if answer.get('correct') != None:
            if answer.get('correct') == 'true':
                logmsg(L_TRACE, "Answer " + str(a_index) + " is correct")
                correct = True
            else:
                logmsg(L_TRACE, "Answer " + str(a_index) + " is wrong")
        # tick_control = driver.find_element_by_xpath("(//div[@id='widget_cards_attributes_0_options_attributes_0_is_correct']/div)[0]/a")
        # tick_control = driver.find_element_by_xpath("//div[@id='card-options-" + str(q_index) + "']/div[@data-id='" + str(a_index) + "']/div[@class='cell check']/div[@class='left']/a")
        # tick_control = driver.find_element_by_xpath("//div[@id='card-options-" + str(q_index) + "']/div[@data-id='" + str(a_index) + "']/div[@class='cell check']/div[@class='left']/a")
        # tick_control = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[@id='card-options-" + str(q_index) + "']/div[@data-id='" + str(a_index) + "']/div[@class='cell check']/div[@class='left']/a")))
        # tick_control = driver.find_element_by_xpath("//div[@id='card-options-" + str(q_index) + "']/div[@data-id='" + str(a_index) + "']/div[@class='cell check']/div[@class='left']/a")
        # tick_control = driver.find_element_by_xpath("//div[@id='card-options-0']/div[@data-id='" + str(a_index) + "']/div[@class='cell check']/div[@class='left']/a")
        # tick_control = driver.find_element_by_xpath("//div[@class='cell check']/input[@id='widget_cards_attributes_" + str(question_num) + "_options_attributes_" + str(a_index) + "_is_correct']/../div[@class='left']/a")
        # tick_control = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "myDynamicElement")))
        tick_control = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='cell check']/input[@id='widget_cards_attributes_" + str(question_num) + "_options_attributes_" + str(a_index) + "_is_correct']/../div[@class='left']/a")))
        logmsg(L_TRACE, "Tick control is: " + stringify(tick_control))
        if tick_action == 0:
            action = ActionChains(driver) 
            action.move_to_element(tick_control).click().perform()
        elif tick_action == 1:
            script = "arguments[0].scrollIntoView();"
            driver.execute_script(script, tick_control)
        elif tick_action == 2:
            # JavascriptExecutor jse = (JavascriptExecutor)driver
            driver.execute_script("arguments[0].scrollIntoView()", tick_control)
        elif tick_action == 3:
            # IJavaScriptExecutor ijse = (IJavaScriptExecutor)driver
            # ijse.execute_script("arguments[0].click();", tick_control)
            driver.execute_script("arguments[0].click();", tick_control)
        '''
        i = 0
        i_max = 100
        # print(str(i_max) + " iterations")
        while not(tick_control.is_enabled()) and (i < i_max):
            if i % 50 == 0:
                print(i)
            time.sleep(0.1)
            i += 1
        if (i >= i_max):
            logmsg(L_ERROR, "Timeout waiting for tick control")
        # time.sleep(10)
        # input("3. Press Enter to continue...")
        '''
        frameinfo = getframeinfo(currentframe())
        # print('\aLine: ' + str(frameinfo.lineno))
        # time.sleep(5)
        logmsg(L_TRACE, "Elapsed time: " + str((micros() - timenow)/1000000.))
        '''
        source = driver.page_source
        logmsg(L_TRACE, "driver.page_source is type: " + str(type(source)))
        while True:
            try:
                logmsg(L_TRACE, "Frame source is: " + source)
                success = True
                break
            except UnicodeEncodeError:
                success = False
                logmsg(L_TRACE, "Truncating source to " + str(int(len(source)/2)) + " chars")
                source = source[0:int(len(source)/2)]
        '''
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except NoAlertPresentException:
            pass
        my_element_id = 'something123'
        ignored_exceptions = (NoSuchElementException,StaleElementReferenceException,)
        tick_control = WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions).\
            until(EC.element_to_be_clickable((By.XPATH, "//div[@class='cell check']/input[@id='widget_cards_attributes_" \
            + str(question_num) + "_options_attributes_" + str(a_index) + "_is_correct']/../div[@class='left']/a")))
        '''
        class FrameNotFound(Exception):
        # Raised when the frame we are looking for was not found in the web page.
        pass
        '''
        if 'icon-os-form-check' in tick_control.get_attribute('class'):
            if not correct:
                # tick_control.click()
                driver.execute_script("arguments[0].click();", tick_control)
        else:
            if correct:
                # tick-control.click()
                driver.execute_script("arguments[0].click();", tick_control)

'''
and for relative xpath (this was first :) ):

function WebElement_XPath(element) {
    if (element.tagName == 'HTML')    return '/html';
    if (element===document.body)      return '/html/body';

    // calculate position among siblings
    var position = 0;
    // Gets all siblings of that element.
    var siblings = element.parentNode.childNodes;
    for (var i = 0; i < siblings.length; i++) {
        var sibling = siblings[i];
        // Check Siblink with our element if match then recursively call for its parent element.
        if (sibling === element)  return WebElement_XPath(element.parentNode)+'/'+element.tagName+'['+(position+1)+']';

       // if it is a siblink & element-node then only increments position. 
        var type = sibling.nodeType;
        if (type === 1 && sibling.tagName === element.tagName)            position++;
    }
}
'''

'''
def thread_function(name):
    logging.info("Thread %s: starting", name)
    time.sleep(2)
    logging.info("Thread %s: finishing", name)

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    logging.info("Main    : before creating thread")
    x = threading.Thread(target=thread_function, args=(1,))
    logging.info("Main    : before running thread")
    x.start()
    logging.info("Main    : wait for the thread to finish")
    # x.join()
    logging.info("Main    : all done")
'''

logmsg(L_TRACE, "##################### Starting Program #####################")
logmsg(L_INFO, "Using Python version " + str(sys.version_info[0]) + "." + str(sys.version_info[1]))

# Object that signals task finished 
_finished = object() 
_interrupted = object()
  
whizzer = ["|", "/", "\u2014", "\\"] 
# whizzer = ["\u2191", "\u2197", "\u2192", "\u2198", "\u2193", "\u2199", "\u2190", "\u2196"] 

messages = Queue()
sleeptime = 0.15

def waiting(message_queue, text, timeout):
    sys.stdout.write(text + "    ")
    sys.stdout.flush()
    i = timeout
    while True:
        # sys.stdout.write("\b" + whizzer[i % len(whizzer)])
        sys.stdout.write("\b\b\b\b" + str(i).rjust(4))
        sys.stdout.flush()
        # time.sleep(sleeptime)
        time.sleep(1)
        i = i - 1
        if i <= 0:
            print()
            print("Timeout. Task took longer than " + str(timeout) + " seconds.")
            break
        if message_queue.empty():
            continue
        else:
            flag = message_queue.get(block = False)
        if flag is _finished:
            sys.stdout.write("\r")
            sys.stdout.flush()
            print ()
            print("Task is complete. Took " + str(timeout - i) + " seconds")
            # for i in range(len(text) + 3):
            #     sys.stdout.write(" ")
            #     sys.stdout.flush()
            break
        if flag is _interrupted:
            break
        
'''
print("Downloading web page ")
message = "Waiting for browser to open and web page to download   "
# print(message)
# print(message, end='')
sys.stdout.write(message)
sys.stdout.flush()
#print("  ", end='')
for i in range(1000):
    # print("\b" + whizzer[i % 4], end='')
    # print("\b" + whizzer[i % 4],)
    sys.stdout.write("\b" + whizzer[i % 4])
    sys.stdout.flush()
    time.sleep(0.15)
print ("\r", end='')
sys.stdout.write("\r")
sys.stdout.flush()
for i in range(len(message)):
    # print(" ", end='')
    sys.stdout.write(" ")
    sys.stdout.flush()
#print ("\r", end='')
'''

# driver = webdriver.Chrome('C:\Program Files (x86)\Python38-32\Selenium\chromedriver.exe')
if use_browser == "chrome":
    driver = webdriver.Chrome(ChromeDriverManager().install())
elif use_browser == "firefox":
    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
else:
    logmsg(L_ERROR, "Browser " + use_browser + " is not supported")

def main():
    global answers, q_index, a_index, question_num
    
    #Parse and validate XML file.
    filename_xml = 'MockExam5.xml'
    # filename_xml = 'new6.xml'
    filename_xsd = 'MockExam.xsd'

    # open and read schema file
    with io.open(filename_xsd, mode="r", encoding="utf-8") as schema_file:
        schema_to_check = schema_file.read()

    # open and read xml file
    with io.open(filename_xml, mode="r", encoding="utf-8") as xml_file:
        xml_to_check = xml_file.read()
        
    xmlschema_doc = etree.parse(StringIO(schema_to_check))
    xmlschema = etree.XMLSchema(xmlschema_doc)

    # parse xml
    try:
        doc = etree.parse(StringIO(xml_to_check))
        logmsg(L_INFO, 'XML well formed, syntax OK')

    # check for file IO error
    except IOError:
        logmsg(L_ERROR, 'Invalid XML file, IO error')

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        logmsg(L_ERROR, 'XML Syntax Error: ' + str(err.error_log))
        quit()

    except:
        logmsg(L_ERROR, "Unknown error parsing file " + filename_xml + ", exiting")
        quit()

    if True:
        # validate against schema
        try:
            xmlschema.assertValid(doc)
            logmsg(L_INFO, 'XML file ' + filename_xml + ' validated against schema ' + filename_xsd + ', as OK')

        except etree.DocumentInvalid as err:
            logmsg(L_ERROR, 'Schema validation error: ' + str(err.error_log))
            quit()

        except:
            logmsg(L_ERROR, "Unknown error validating file " + filename_xml + " against schema " + filename_xsd + ", exiting")
            quit()

    '''
    ######## Another try
    def validate_with_lxml(xsd_tree, xml_tree):
        schema = lxml.etree.XMLSchema(xsd_tree)
        try:
            schema.assertValid(xml_tree)
        except lxml.etree.DocumentInvalid:
            print("Validation error(s):")
            for error in schema.error_log:
                print("  Line {}: {}".format(error.line, error.message))
                
    try:
       xmlschema_doc = lxml.etree.parse(filename)
       xmlschema = lxml.etree.XMLSchema(xmlschema_doc)
       xmlschema.assertValid(elem_tree)
    except lxml.etree.ParseError as e:
       raise lxml.etree.ParserError(str(e))
    except lxml.etree.DocumentInvalid as e:
       if ignore_errors:
        raise lxml.etree.ValidationError("The Config tree is invalid with error 
           message:\n\n" + str(e)) 
    ######## End of try
    '''

    '''
    # open and read schema file
    with open(filename_xsd, 'r') as schema_file:
        schema_to_check = schema_file.read()

    # open and read xml file
    with open(filename_xml, 'r') as xml_file:
        xml_to_check = xml_file.read()
        
    xmlschema_doc = etree.parse(StringIO(schema_to_check))
    xmlschema = etree.XMLSchema(xmlschema_doc)

    # parse xml
    try:
        doc = etree.parse(StringIO(xml_to_check))
        logmsg(L_TRACE, 'XML file well formed, syntax OK')

    # check for file IO error
    except IOError:
        logmsg(L_ERROR, 'Invalid XML file')

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        logmsg(L_ERROR, "XML Syntax Error, '" + str(err.error_log) + "'")
        quit()

    except:
        logmsg(L_ERROR, 'Unknown error parsing XML file, exiting.')
        quit()

    # validate against schema
    try:
        xmlschema.assertValid(doc)
        logmsg(L_TRACE, 'XML valid, schema validation OK')

    except etree.DocumentInvalid as err:
        logmsg(L_ERROR, "Schema validation error '" + str(err.error_log) + "'")
        quit()

    except:
        logmsg(L_ERROR, "Unknown error validating " + filename_xml + " against " + filename_xsd + ", exiting")
        quit()
    '''

    '''
        root = ET.parse('MockExam.xml').getroot()
        if root.tag != 'exam':
            logmsg(L_ERROR, "XML file root element must be 'exam', was '" + root.tag + "'")
        else:
            if len(root.iter('name')) != 1:
                logmsg(L_ERROR, "the XML file must contain one and only one name element. This one contains " + len(root.iter('name')))
            else:
                logmsg(L_INFO, "This is where the rest of the code goes")
    '''

    driver.implicitly_wait(5)
      # Optional argument, if not specified will search path.
    # Open login page, and log in.
    logmsg(L_TRACE, "Fetching page opinionstage.com")
    wait = Thread(target = waiting, args = (messages, "Waiting for browser to open and web page to download", 20))
    wait.start()
    driver.get('https://www.opinionstage.com/registrations/login')
    messages.put(_finished)
    # time.sleep(5) # Let the user actually see something!
    # email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "element_css"))).get_attribute("value")
    # WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".reply-button"))).click()
    # element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "myDynamicElement"))
    # ui.WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@id='billFirstName']")))
    # browser.find_element_by_xpath("//input[@id='billFirstName']").click()
    # browser.find_element_by_xpath("//input[@id='billFirstName']").clear()
    # browser.find_element_by_xpath("//input[@id='billFirstName']").send_keys("user_first_name")
    logmsg(L_TRACE, "Logging into OpionionStage")
    input_email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "client_session_email")))
    input_email.click()
    input_email.clear()
    input_email.send_keys(email)
    # input_password = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "client_session_password")))
    input_password = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "client_session_password")))
    input_password.click()
    input_password.clear()
    input_password.send_keys(password)
    # for topic in topics:
    #     logmsg(L_TRACE, "Processing topic " + topic)
    # input_login = driver.find_element_by_xpath("//form[@id='new_client_session']/")
    input_login = driver.find_element_by_xpath("//form[@id='new_client_session']")
    login_form = driver.find_element_by_xpath("//form[@id='new_client_session']")
    login_form.submit()
    # = driver.find_element_by_id('client_session_email')
    # Get exam attributes.
    logmsg(L_TRACE, "Getting exam info from XML file")
    root = doc.getroot()
    logmsg(L_TRACE, "Root = " + str(root.tag))
    # logmsg(L_TRACE, "root = " + stringify(root))
    # exams = root.find("exams")
    if str(root.tag) != "exams":
        logmsg(L_ERROR, "Root of XML file must be 'exams', was " + str(root.tag))
    else:
        logmsg(L_TRACE, "Root of XML file is 'exams' (correct)")
        exams = root
    if exams == None:
        logmsg(L_ERROR, "XML file must include exams element, not found")
    elements = exams.findall("*")
    msg = ""
    for element in elements:
        msg = msg + "\n\t" + element.tag
    logmsg(L_TRACE, "Children of <exams> are:" + msg)
    exam_list = exams.findall("exam")
    if len(exam_list) <= 0:
        logmsg(L_ERROR, "XML file must include at least one exam, none found")
    for examnum in range(len(exam_list)):
        logmsg(L_TRACE, "Processing exam number " + str(examnum))
        exam = exam_list[examnum]
        this_topic = exam.find('topic').text
        print("Processing exam number " + str(examnum) + " (topic: " + this_topic+ ")")
        '''
        if (root.tag != 'exams'):
            logmsg(L_ERROR, "XML file root element must be 'exams', was '" + root.tag + "'")
        for exam in root:
            if (section.tag != 'exam'):
                logmsg(L_ERROR, "XML file - all children of 'exam' must be 'section'. Was '" + section.tag + "'")
        '''
        exam_name = exam.find('name')
        if exam_name == None:
            logmsg(L_ERROR, "XML file: exam must contain a name element")
        exam_name_date = exam_name.text + "  " + datetime.now().strftime('(%d-%b-%y %H:%M:%S)')
        logmsg(L_TRACE, "Exam name is " + exam_name_date)
        exam_cover = exam.find('cover')
        if exam_cover == None:
            logmsg(L_ERROR, "XML file: exam must contain a cover element")
        cover_title = exam_cover.find('title')
        if cover_title == None:
            logmsg(L_ERROR, "XML file: exam.cover must contain a title element")
        cover_title_text = cover_title.text
        logmsg(L_TRACE, "Exam cover title is " + cover_title_text)
        cover_text = exam_cover.find('text')
        if cover_text == None:
            cover_text_text = ""
        else:
            cover_text_text = cover_text.text
        logmsg(L_TRACE, "Exam cover text is " + cover_text_text)
        cover_image = exam_cover.find('image')
        if cover_image == None:
            cover_image_text = ""
        else:
            cover_image_text = cover_image.text
        logmsg(L_TRACE, "Exam cover image is " + cover_image_text)
        # Create new trivia quiz.
        # new_quiz = driver.find_element_by_xpath('//a[@href="/dashboard/quizzes/new"]')
        # new_quiz = driver.find_element_by_xpath('//div[@id="dashboard"]/header/div[@class="header__additional"]/div[@class="simple-dropdown header__dropdown"]/div[@class="simple-dropdown__menu"]/div[@class="simple-dropdown__section"]/div[@class="simple-dropdown__itm simple-dropdown__itm-readonly"][2]/div[@class="truncate-text"]).text
        # new_quiz = driver.find_element_by_link_text('Trivia Quiz')
        # new_quiz.click()
        # Enter quiz title.
        driver.get('https://www.opinionstage.com/dashboard/quizzes/new')
        # Enter quiz title.
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except NoAlertPresentException:
            pass
        quiz_name = driver.find_element_by_id('widget_internal_name')
        logmsg(L_TRACE, "Sending quiz name: " + exam_name_date)
        quiz_name.send_keys(exam_name_date)
        # Enter Cover Title.
        cover_title_control = driver.find_element_by_id('widget_title')
        logmsg(L_TRACE, "Sending cover title: " + cover_title_text)
        cover_title_control.send_keys(cover_title_text)
        # Enter cover text.
        if len(cover_text_text) > 0:
            iframe = driver.find_element_by_id('widget_text_ifr')
            driver.switch_to.frame(iframe)
            # time.sleep(2)
            # cover_text_control = driver.find_element_by_id('tinymce')
            cover_text_control = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "tinymce")))
            logmsg(L_TRACE, "Sending cover text: " + cover_text_text)
            cover_text_control.send_keys(cover_text_text)
            driver.switch_to.default_content()
        logmsg(L_TRACE, "Successfully uploaded cover text fields")
        # Enter image
        '''
        if len(cover_image_text) > 0:
            # If there is an image, upload it.
            # Click where it says "Click to add image".
            add_image = driver.find_element_by_class_name('upload-widget-opener')
            add_image.click()
            # time.sleep(5)
            # browse_button = driver.find_element_by_class_name('cloudinary_fileupload')
            # browse_button = driver.find_element_by_class_name('BUTTON')
            logmsg(L_TRACE, "str is " + str(type(str)) + ", str() is " + str(type(str())))
            max_tries = 5
            trynum = 0
            for trynum in range (max_tries):
                try:
                    # Find the frame containing the Browse button.
                    frameList = driver.find_elements_by_xpath("//iframe")
                    numOfFrames = len(frameList)
                    logmsg(L_TRACE, "Page has " + str(numOfFrames) + " frames")
                    frameNum = -1
                    for index in range(numOfFrames):
                        logmsg(L_TRACE, "Frame " + str(index) + " id= " + frameList[index].get_attribute('id') + ", src= " + frameList[index].get_attribute('src') + ", name= " + frameList[index].get_attribute('name'))
                        if (frameList[index].get_attribute('src')[0:30] == "https://widget.cloudinary.com/"):
                            frameNum = index
                    if (frameNum < 0):
                        logmsg(L_ERROR, "No frames found")
                        raise FrameNotFound(" The frame with src starting 'https://widget.cloudinary.com/' was not found")
                    else:
                        break
                except FrameNotFound:
                    logmsg(L_TRACE, "Exception raised")
            if frameNum < 0:
                logmsg(L_ERROR, "Frame not found after " + str(max_tries) + " tries")
            # Switch to the frame containing the Browse button.
            logmsg(L_TRACE, "Switching to frame " + str(frameNum))
            driver.switch_to.frame(frameNum)
            # time.sleep(2)
            # buttons = driver.find_elements_by_name('file')
            # List all the elements on the frame (for debugging).
            elementList = driver.find_elements_by_xpath("//*")
            logmsg(L_TRACE, "str is " + str(type(str)) + ", str() is " + str(type(str())))
            logmsg(L_TRACE, str(len(elementList)) + " elements found")
            for index in range(len(elementList)):
                elementList = driver.find_elements_by_xpath("//*")
                logmsg(L_TRACE, "index = " + str(index) + ", " + str(len(elementList)) + " elements found")
                if index >= len(elementList):
                    # The element we are trying to access no longer exists.
                    break
                str_index = str(index);
                try:
                    msg = "Index: " + str_index + ", tag: " + str(elementList[index].tag_name)
                    msg += ", name: " + str(elementList[index].get_attribute('name'))
                    msg += ", id: " + elementList[index].get_attribute('id')
                    msg += ", href: " + str(elementList[index].get_attribute('href'))
                    msg += ", src: " + str(elementList[index].get_attribute('src'))
                    msg += ", class: " + str(elementList[index].get_attribute('class'))
                    msg += ", style: " + str(elementList[index].get_attribute('style'))
                    logmsg(L_TRACE, msg)
                except StaleElementReferenceException:
                    continue
            # Find the Browse button.
            buttons = driver.find_elements_by_class_name('cloudinary_fileupload')
            logmsg(L_TRACE, "There are " + str(len(buttons)) + " buttons")
            # If there is more than one, list them all (for debugging).
            for index in range(len(buttons)):
                # logmsg(L_TRACE, "Button no. " + str(index) + " id = " + buttons[index].get_attribute('id') + ", name = " + buttons[index].get_attribute('name') + ", style = " + buttons[index].get_attribute('style'))
                str_index = str(index);
                msg = "Index: " + str_index + ", tag: " + str(buttons[index].tag_name)
                msg += ", name: " + str(buttons[index].get_attribute('name'))
                msg += ", id: " + buttons[index].get_attribute('id')
                msg += ", href: " + str(buttons[index].get_attribute('href'))
                msg += ", src: " + str(buttons[index].get_attribute('src'))
                msg += ", class: " + str(buttons[index].get_attribute('class'))
                msg += ", style: " + str(buttons[index].get_attribute('style'))
                logmsg(L_TRACE, msg)
            # buttons[0].click()
            # driver.switch_to.default_content()

            ##########
            # Get the list of iframes present on the web page using tag "iframe".
            seq = driver.find_elements_by_tag_name('iframe')
            logmsg(L_TRACE, "No of iframes present in the web page are: " + str(len(seq)))
            #switching between the iframes based on index
            # Try each frame in turn
            for index in range(len(seq)):
                driver.switch_to.default_content()
                iframe = driver.find_elements_by_tag_name('iframe')[index]
                driver.switch_to.frame(iframe)
                driver.implicitly_wait(30)
                #highlight the contents of the selected iframe
                driver.find_element_by_tag_name('a').send_keys(Keys.CONTROL, 'a')
                # time.sleep(2)
                # undo the selection within the iframe
                driver.find_element_by_tag_name('p').click()
                driver.implicitly_wait(30)
            # sample_image = "D:/XPS_8700 Extended Files/Users/RowanB/Documents/Dropbox/Dropbox/My_Scripts/Mock Exams/Exam Pictures/FD2-1.jpg"
            if (len(buttons)<=0):
                driver.find_element(By.NAME, "file").send_keys(image_path + cover_image_text)
            else:
                # button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cloudinary_fileupload')))
                # buttons[0].click()
                # buttons[0].send_keys(image_path + cover_image_text)
                # Wait until Browse button is clickable.
                i = 0
                i_max = 100
                while not(buttons[0].is_enabled()) and (i < i_max):
                    time.sleep(0.1)
                    i += 1
                if (i >= i_max):
                    logmsg(L_ERROR, "Timeout waiting for button")
                # Send file path to button.
                buttons[0].send_keys(image_path + cover_image_text)
                # Find all elements in frame.
                elements = driver.find_elements_by_xpath('//*')
                num_elems = len(elements)
                # Search them all for skip button.
                for index in range(num_elems):
                    element = elements[index]
                    if element.get_attribute('data-test') == 'skip-button':
                        break
                # Log properties of skip button (for debugging).
                msg = "Button is tag: " + str(element.tag_name)
                msg += ", name: " + str(element.get_attribute('name'))
                msg += ", id: " + element.get_attribute('id')
                msg += ", href: " + str(element.get_attribute('href'))
                msg += ", src: " + str(element.get_attribute('src'))
                msg += ", class: " + str(element.get_attribute('class'))
                msg += ", style: " + str(element.get_attribute('style'))
                logmsg(L_TRACE, msg)
                # Click the button.
                logmsg(L_TRACE, "clicking button ")
                element.click()
            driver.switch_to.default_content()
        '''
        # logmsg(L_TRACE, "Frame source is: " + str(driver.page_source, 'utf-8', 'backslashreplace'))
        source = driver.page_source
        logmsg(L_TRACE, "driver.page_source is type: " + str(type(source)))
        while True:
            try:
                logmsg(L_TRACE, "Frame source is: " + source)
                success = True
                break
            except UnicodeEncodeError:
                success = False
                source = source[0:int(len(source)/2)]
        logmsg(L_TRACE, "Sending cover image: " + cover_image.text)
        wait = Thread(target = waiting, args = (messages, "Waiting for image to upload", 90))
        wait.start()
        "//a[text() = 'Click to add image']"
        # upload4(cover_image.text, "//a[@class='upload-widget-opener']", '//div[@data-test="drag-area"]')
        upload4(cover_image.text, "//a[text() = 'Click to add image']", '//div[@data-test="drag-area"]')
        messages.put(_finished)
        time.sleep(5)
        # Uncheck the checkbox "Use this as default image for this quiz". 
        logmsg(L_TRACE, "Unchecking 'use as default' checkbox")
        default = driver.find_element_by_id("widget_cover_as_default")
        logmsg(L_TRACE, "Default control is: " + default.get_attribute("outerHTML"))
        if default == None:
            logmsg(L_ERROR, "Can't find default checkbox")
        # if (default.get_attribute('checked') == 'checked'):
        if (default.is_selected()):
            logmsg(L_TRACE, "default control is checked. Clicking it.")
            # default.click()
            driver.execute_script("arguments[0].click();", default)
        else:
            logmsg(L_TRACE, "default control is not checked, doing nothing")
        # default2 = driver.find_element_by_id("widget[cover_as_default]")
        default2 = driver.find_element_by_id("widget_cover_as_default")
        logmsg(L_TRACE, default2.get_attribute("outerHTML"))
        if (default.get_attribute('checked') == 'checked'):
            logmsg(L_TRACE, "default control is checked. Clicking it.")
            default2.click()
        # Get filter properties for this exam
        this_discipline = exam.find('discipline').text
        this_level = exam.find('level').text
        # this_topic = exam.find('topic').text
        # Find all questions
        questions_xml = exams.find("questions")
        questions = questions_xml.findall("question")
        num_quest = len(questions)
        logmsg(L_TRACE, "Found " + str(num_quest) + " questions")
        if num_quest <= 0:
            logmsg(L_ERROR, "XML file must contain at least one question, " + str(num_quest) + " found")
        question_num = 0                        # question_num is the number of questions we have added to the exam. 0-based
        for q_index in range(num_quest):        # q_index is the index of questions read from the XML file. 0-based
            # Do next question.
            question = questions[q_index]
            logmsg(L_TRACE, "Question is: " + str(tostring(question)))
            if question.find("discipline").text != this_discipline:
                logmsg(L_TRACE, "Question " + str(q_index) + " discipline does not match, skipping this question")
                print("Skipping question no. " + str(q_index) + " (wrong discipline: " + question.find("discipline").text + ")")
                continue
            if question.find("level").text != this_level:
                # logmsg(L_TRACE, "Question level does not match, skipping this question")
                logmsg(L_TRACE, "Question " + str(q_index) + " level (" + question.find("level").text + ") does not match current level (" + this_level + "), skipping this question")
                print("Skipping question no. " + str(q_index) + " (wrong level: " + question.find("level").text + ")")
                continue
            if question.find("topic").text != this_topic:
                logmsg(L_TRACE, "Question " + str(q_index) + " topic (" + question.find("topic").text + ") does not match current topic (" + this_topic + "), skipping this question")
                print("Skipping question no. " + str(q_index) + " (wrong topic: " + question.find("topic").text + ")")
                continue
            logmsg(L_TRACE, "Question " + str(q_index) + " matches discipline, level and topic, processing this question")
            print("Processing question no. " + str(q_index))
            if question_num > 0:
                # Add another question.
                # add_questions = driver.find_elements_by_xpath("//a[@class_name='add-card']")
                # logmsg(L_TRACE, "Frame source is " + driver.page_source)
                # logmsg(L_TRACE, "Frame source is: " + str(driver.page_source, 'utf-8', 'backslashreplace'))
                source = driver.page_source
                while True:
                    try:
                        logmsg(L_TRACE, "Frame source is: " + source)
                        success = True
                        break
                    except UnicodeEncodeError:
                        success = False
                        source = source[0:int(len(source)/2)]
                elements = driver.find_elements_by_xpath("//*")
                for elementnum in range(len(elements)):
                    try:
                        element = elements[elementnum]
                        logmsg(L_TRACE, "Element no. " + str(elementnum) + " is " + element.get_attribute("outerHTML")[:64])
                    except UnicodeEncodeError:
                        break
                add_questions = driver.find_elements_by_xpath("//div[@id='cards-section']/div[@class='f-section-body']/div[2]/a")
                if len(add_questions) > 1:
                    logmsg(L_ERROR, "There should be only one element with 'add-card' style, " + str(len(add_questions)) + " found")
                if len(add_questions) < 1:
                    logmsg(L_ERROR, "No elements found with 'add-card' style.")
                add_question = add_questions[0]
                # add_question.click()
                driver.execute_script("arguments[0].click();", add_question)
            # Add the question text.
            question_textboxes = driver.find_elements_by_id('widget_cards_attributes_' + str(question_num) + '_title')
            if len(question_textboxes) != 1:
                logmsg(L_ERROR, "there should be only one element, " + str(len(question_textboxes)) + " found")
            question_textbox = driver.find_element_by_id('widget_cards_attributes_' + str(question_num) + '_title')
            # Log properties of question text field (for debugging).
            msg = "Element is tag: " + str(question_textbox.tag_name)
            msg += ", name: " + str(question_textbox.get_attribute('name'))
            msg += ", id: " + question_textbox.get_attribute('id')
            msg += ", href: " + str(question_textbox.get_attribute('href'))
            msg += ", src: " + str(question_textbox.get_attribute('src'))
            msg += ", class: " + str(question_textbox.get_attribute('class'))
            msg += ", style: " + str(question_textbox.get_attribute('style'))
            logmsg(L_TRACE, msg)
            logmsg(L_TRACE, "Looking for element Id = " + 'widget_cards_attributes_' + str(question_num) + '_title')
            # question_textbox = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'widget_cards_attributes_' + str(question_num) + '_title')))
            question_textbox = driver.find_element_by_id('widget_cards_attributes_' + str(question_num) + '_title')
            logmsg(L_TRACE, "question_textbox is " + question_textbox.get_attribute("outerHTML")[:64])
            question_text = question.find('text').text
            logmsg(L_TRACE, "Sending text: " + question_text)
            # question_textbox.send_keys(question.find('text').text)
            driver.execute_script("arguments[0].value = '" + question_text + "';", question_textbox)
            # driver.find_element_by_xpath("//div[@id='a']/div/a[@class='click']")
            # If there is an image, add it.
            image = question.find('image')
            if image != None:
                logmsg(L_TRACE, "This question has an image")
                image_text = image.text
                if image_text == None:
                    logmsg(L_WARNING, "Image has no filename")
                else:
                    logmsg(L_TRACE, "Sending question image: " + image_text)
                    wait = Thread(target = waiting, args = (messages, "Waiting for image to upload", 150))
                    wait.start()
                    upload4(image_text, "//div[@id='card-" + str(question_num) + "']/div[@class='cloudinary-widget-container']/a[@class='upload-widget-opener']", '//input[@class="cloudinary_fileupload"]')
                    messages.put(_finished)
            driver.switch_to.default_content()
            answers = question.findall("answer")
            num_ans = len(answers)
            logmsg(L_TRACE, "Found " + str(num_ans) + " answers")
            if num_ans < 2:
                logmsg(L_ERROR, "XML file: Each question must contain at least two answers, " + str(num_ans) + " found")
            for a_index in range (num_ans):
                do_answer(a_index)
            # See if there is an explanation.
            root = doc.getroot()
            explanation = question.find("explanation")
            enable_explanation = driver.find_element_by_xpath("//input[@id='widget_cards_attributes_" + str(question_num) + "_has_explanation']")
            logmsg(L_TRACE, "enable_explanation is " + enable_explanation.get_attribute("outerHTML"))
            if explanation != None:
                logmsg(L_TRACE, "Explanation found")
                explanation_text = explanation.text
                if explanation_text == None:
                    logmsg(L_ERROR, " explanation must have text. None found")
                else:
                    logmsg(L_TRACE, "Processing explanation for question " + str(q_index))
                    print("Processing explanation for question " + str(q_index))
                    # Enabling explanation.
                    # if enable_explanation.is_enabled():
                    if False:
                        # Do nothing
                        logmsg(L_TRACE, "enable_explanation is already enabled, do nothing")
                        pass
                    else:
                        # Click checkbox
                        '''
                        //find tinymce iframe
                        editorFrame = driver.findElement(By.cssSelector(".col_right iframe"));  

                        //switch to iframe
                        driver.switchTo().frame(editorFrame);
                        WebElement body = driver.findElement(By.className("mceContentBody"));
                        body.sendKeys("YOOOO");
                        driver.switchTo().defaultContent();
                        '''
                        logmsg(L_TRACE, "Assuming enable_explanation is not enabled, checking checkbox")
                        driver.execute_script("arguments[0].click();", enable_explanation)
                        # Upload text
                        explanation_frame = driver.find_element_by_id("widget_cards_attributes_" + str(question_num) + "_text_ifr")
                        logmsg(L_TRACE, "explanation_frame is " + explanation_frame.get_attribute("outerHTML")[:64])
                        driver.switch_to.frame(explanation_frame)
                        # Find all elements in this frame.
                        elements = driver.find_elements_by_xpath("//*")
                        for elementnum in range(len(elements)):
                            try:
                                element = elements[elementnum]
                                logmsg(L_TRACE, "Element no. " + str(elementnum) + " is " + element.get_attribute("outerHTML")[:64])
                            except UnicodeEncodeError:
                                logmsg(L_ERROR, "UnicodeEncodeError exception ocurred")
                                break
                        explanation_text_control = driver.find_element_by_xpath("//body[@id='tinymce']")
                        if explanation_text_control == None:
                            logmsg(L_ERROR, "Can't find tinymce text control")
                        # explanation_text_control = driver.find_element_by_class_name("mceContentBody")
                        # explanation_text_control = driver.findElement(By.tagName("body")).click().sendKeys("YOOOO")
                        logmsg(L_TRACE, "Uploading explanation text " + explanation_text + " to control " + explanation_text_control.get_attribute("outerHTML")[:64])
                        # driver.execute_script("arguments[0].setAttribute('value', '" + explanation_text +"')", explanation_text_control)
                        # driver.execute_script("tinyMCE.activeEditor.setContent('" + explanation_text + "')");
                        # explanation_text_control.click().send_keys(explanation_text)
                        action = ActionChains(driver) 
                        action.move_to_element(explanation_text_control).click().send_keys(explanation_text).perform()
                        driver.switch_to.parent_frame()
                    explanation_image = explanation.find("image")
                    if explanation_image != None:
                        explanation_image_text = explanation_image.text
                        logmsg(L_ERROR, "Explanation image found - currently not supported")
            question_num = question_num + 1     
        print("Finishing off exam " + str(examnum))
        save_draft = driver.find_element_by_xpath('//input[@type="submit" and contains(@class, "btn_aqua-filled") and @value="save draft"]')
        driver.execute_script("arguments[0].click();", save_draft)
    quit()    

try:
    main()
except KeyboardInterrupt:
    logmsg(L_TRACE, "KeyboardInterrupt occurred")
    messages.put(_interrupted)
finally:
    logmsg(L_TRACE, "Program terminated, finally block being executed")
    messages.put(_interrupted)
quit()
