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
    """BlueRov video capture class constructor
    Attributes:
        port (int): Video UDP port
        video_codec (string): Source h264 parser
        video_decode (string): Transform YUV (12bits) to BGR (24bits)
        video_pipe (object): GStreamer top-level pipeline
        video_sink (object): Gstreamer sink element
        video_sink_conf (string): Sink configuration
        video_source (string): Udp source ip and port
    """

    def __init__(self, port=5000):
        """Summary
        Args:
            port (int, optional): UDP port
        """

        Gst.init(None)

        self.port = port
        self._sample = None


        # # [Software component diagram](https://www.ardusub.com/software/components.html)
        # # UDP video stream (:5600)
        # self.video_source = 'udpsrc port={}'.format(self.port)
        # # [Rasp raw image](http://picamera.readthedocs.io/en/release-0.7/recipes2.html#raw-image-capture-yuv-format)
        # # Cam -> CSI-2 -> H264 Raw (YUV 4-4-4 (12bits) I420)
        # self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264'
        # # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        # self.video_decode = \
        #     '! queue2 max-size-bytes=655360 max-size-buffers=655360 max-size-time=100 ! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert '
        # # Create a sink to get data
        # self.video_sink_conf = \
        #     '! appsink emit-signals=true sync=false max-buffers=2 drop=true'

        self.media_pipe = None
        self.media_sink = None

        self.run()

    def start_gst(self, config=None):
        # """ Start gstreamer pipeline and sink
        # Pipeline description list e.g:
        #     [
        #         'videotestsrc ! decodebin', \
        #         '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
        #         '! appsink'
        #     ]
        # Args:
        #     config (list, optional): Gstreamer pileline description list
        # """

        # if not config:
        #     config = \
        #         [
        #             'videotestsrc ! decodebin',
        #             '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
        #             '! appsink'
        #         ]

        # command = ' '.join(config)
        # self.video_pipe = Gst.parse_launch(command)
        # self.video_pipe.set_state(Gst.State.PLAYING)
        # self.video_sink = self.video_pipe.get_by_name('appsink0')

        #command = 'audiotestsrc ! audioconvert ! appsink' #autoaudiosink
        command = 'audiotestsrc ! audioconvert ! appsink emit-signals=True' #autoaudiosink

        self.media_pipe = Gst.parse_launch(command)
        self.media_pipe.set_state(Gst.State.PLAYING)
        self.media_sink = self.media_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_array(sample):
        """Transform byte array into np array
        Args:
            sample (TYPE): Description
        Returns:
            TYPE: Description
        """
        # buf = sample.get_buffer()
        # caps = sample.get_caps()
        # array = np.ndarray(
        #     (
        #         caps.get_structure(0).get_value('height'),
        #         caps.get_structure(0).get_value('width'),
        #         3
        #     ),
        #     buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        # return array
        
        buf = sample.get_buffer()
        #caps = sample.get_caps()
        array = np.ndarray(
             (
                 #caps.get_structure(0).get_value('rate'),
                 #caps.get_structure(0).get_value('channels')
                 buf.get_size()
             ),
             buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8) + 127 # por que esse 127 ?
        #return array
        return array

    def sample(self):
        """ Get Frame
        Returns:
            iterable: bool and image frame, cap.read() output
        """
        return self._sample

    def sample_available(self):
        """Check if frame is available
        Returns:
            bool: true if frame is available
        """
        return type(self._sample) != type(None)

    def run(self):
        """ Get frame to update _frame
        """

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

def plot():    #Function to create the base plot, make sure to make global the lines, axes, canvas and any part that you would want to update later

    global line,ax,canvas
    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(1,1,1)
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.show()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    line, = ax.plot([1,2,3], [1,2,10])

def updateplot(q):
    try:       #Try to check if there is data in the queue
        result=q.get_nowait()

        if result !='Q':
             print (result)
                 #here get crazy with the plotting, you have access to all the global variables that you defined in the plot function, and have the data that the simulation sent.
             line.set_ydata([1,result,10])
             ax.draw_artist(line)
             canvas.draw()
             window.after(500,updateplot,q)
        else:
             print ('done')
    except:
        print ("empty")
        window.after(500,updateplot,q)


def simulation(q):
    iterations = range(100)
    for i in iterations:
        if not i % 10:
            time.sleep(1)
                #here send any data you want to send to the other process, can be any pickable object
            q.put(random.randint(1,10))
    q.put('Q')

if __name__ == '__main__':
    #Create a queue to share data between process
    q = multiprocessing.Queue()

    #Create and start the simulation process
    simulate=multiprocessing.Process(None,simulation,args=(q,))
    simulate.start()

    #Create the base plot
    plot()

    #Call a function to update the plot when there is new data
    updateplot(q)

    window.mainloop()



    # Create the video object
    # Add port= if is necessary to use a different one
    media = Media()
    window.mainloop()
    # mqtt_topic = sys.argv[1]
    # mqtt_hostname = sys.argv[2]
    # mqtt_port = sys.argv[3]    
    
    while True:
        # Wait for the next frame
        if not media.sample_available():
            continue

        #teste = media.gst_to_array(media._sampleteste)
        sample = media.sample()


        #frame.setflags(write=True)

        # # Find all the faces in the image using the default HOG-based model.
        # # This method is fairly accurate, but not as accurate as the CNN model and not GPU accelerated.
        # # See also: find_faces_in_picture_cnn.py
        # face_locations = face_recognition.face_locations(frame)
        
        # print("I found {} face(s) in this photograph.".format(len(face_locations)))

        # publish.single(mqtt_topic, str(len(face_locations)), hostname=mqtt_hostname, port=int(mqtt_port))

        # # cv2.imshow('frame', frame)
        # # if cv2.waitKey(1) & 0xFF == ord('q'):
        # #    break

