# criado com base no VMS face-counter.py do Anselmo Battisti

# outras referencias gstreamer utilizadas:
# https://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html
# https://www.jonobacon.com/2006/08/28/getting-started-with-gstreamer-with-python/
# http://lifestyletransfer.com/how-to-use-gstreamer-appsink-in-python/
# https://stackoverflow.com/questions/58763496/receive-numpy-array-realtime-from-gstreamer
# https://mathieuduponchelle.github.io/2018-02-15-Python-Elements-2.html?gi-language=undefined
# https://www.jejik.com/articles/2007/01/streaming_audio_over_tcp_with_python-gstreamer/

# referencias python audio
# https://stackoverflow.com/questions/34140831/detecting-a-loud-impulse-sound
# https://www.youtube.com/watch?v=AShHJdSIxkY
# https://www.kaggle.com/fizzbuzz/beginner-s-guide-to-audio-data

# referencias python plot
# https://jakevdp.github.io/PythonDataScienceHandbook/04.00-introduction-to-matplotlib.html
# https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread

# gst-launch-1.0 audiotestsrc ! audioconvert ! autoaudiosink

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk#Agg
import matplotlib.pyplot as plt
import tkinter

import threading

import multiprocessing
import time
import random

import numpy as np
import wave
import sys
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

window=tkinter.Tk()

class Media():

    def __init__(self, port=5000):

        Gst.init(None)

        self.port = port
        self._sample = None
        self._sample_queue = multiprocessing.Queue()

        self.media_pipe = None
        self.media_sink = None

        self.run()

    def start_gst(self, config=None):

        command = 'audiotestsrc ! audioconvert ! appsink emit-signals=True' #autoaudiosink

        self.media_pipe = Gst.parse_launch(command)
        self.media_pipe.set_state(Gst.State.PLAYING)
        self.media_sink = self.media_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_array(sample):
        
        buf = sample.get_buffer()
        print (buf.get_size())
        #caps = sample.get_caps()
        array = np.ndarray(
             (
                 #caps.get_structure(0).get_value('rate'),
                 #caps.get_structure(0).get_value('channels')
                 buf.get_size()
             ),
             buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8) + 127 # por que esse 127 ?
        return array
        #return buf

    def sample(self):
        return self._sample

    def sample_available(self):
        return type(self._sample) != type(None)

    def run(self):
        self.start_gst()
            # [
            #     self.video_source,
            #     self.video_codec,
            #     self.video_decode,
            #     self.video_sink_conf
            # ])
        self.media_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        self._sampleteste = sample
        new_sample = self.gst_to_array(sample)
        self._sample = new_sample
        return Gst.FlowReturn.OK

def sample_plot():    #Function to create the base plot, make sure to make global the lines, axes, canvas and any part that you would want to update later

    global line,fig,ax,canvas
    fig, ax = plt.subplots() 
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()#show()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    line, = ax.plot(np.arange(1024),np.random.rand(1024))
    ax.set_ylim(0,255)
    ax.set_xlim(0,1024)

def sample_updateplot(q):
    try:       #Try to check if there is data in the queue
        result=q.get_nowait()

        # if result !='Q':
        #print (result)
            #here get crazy with the plotting, you have access to all the global variables that you defined in the plot function, and have the data that the simulation sent.
        line.set_ydata(result)
        ax.draw_artist(line)
        canvas.draw()
        #window.after(500,updateplot,q)
        # else:
        #      print ('done')
    except:
        print ("empty")
        # window.after(500,updateplot,q)

if __name__ == '__main__':

    q = multiprocessing.Queue() #Create a queue to share data between process
    sample_plot() #Create the base plot
    media = Media() # Create the media object
    

    # fig, ax = plt.subplots() 
    # line, = ax.plot(np.arange(1024),np.random.rand(1024))
    # plt.show()
    while True:
        # Wait for the next frame
        if not media.sample_available():
            continue

        teste = media.gst_to_array(media._sampleteste)
        sample = media.sample()
        q.put(sample)
        
        sample_updateplot(q)


