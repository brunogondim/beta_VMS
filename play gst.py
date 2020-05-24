# criado com base no VMS face-counter.py do Anselmo Battisti

# outras referencias gstreamer utilizadas:
# https://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html
# https://www.jonobacon.com/2006/08/28/getting-started-with-gstreamer-with-python/
# http://lifestyletransfer.com/how-to-use-gstreamer-appsink-in-python/
# https://stackoverflow.com/questions/58763496/receive-numpy-array-realtime-from-gstreamer
# https://mathieuduponchelle.github.io/2018-02-15-Python-Elements-2.html?gi-language=undefined
# https://www.jejik.com/articles/2007/01/streaming_audio_over_tcp_with_python-gstreamer/

# referencias python
# https://stackoverflow.com/questions/34140831/detecting-a-loud-impulse-sound
# https://www.youtube.com/watch?v=AShHJdSIxkY
# https://www.kaggle.com/fizzbuzz/beginner-s-guide-to-audio-data
# https://jakevdp.github.io/PythonDataScienceHandbook/04.00-introduction-to-matplotlib.html

# https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread

# gst-launch-1.0 audiotestsrc ! audioconvert ! autoaudiosink

import matplotlib.pyplot as plt
import numpy as np
import wave
import sys

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

class Video():
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
        self._frame = None


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

        self.video_pipe = None
        self.video_sink = None

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

        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_opencv(sample):
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

    def frame(self):
        """ Get Frame
        Returns:
            iterable: bool and image frame, cap.read() output
        """
        return self._frame

    def frame_available(self):
        """Check if frame is available
        Returns:
            bool: true if frame is available
        """
        return type(self._frame) != type(None)

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

        self.video_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame
        self._sample = sample
        return Gst.FlowReturn.OK


if __name__ == '__main__':
    # Create the video object
    # Add port= if is necessary to use a different one
    video = Video()

    # mqtt_topic = sys.argv[1]
    # mqtt_hostname = sys.argv[2]
    # mqtt_port = sys.argv[3]    

    x = np.linspace(0, 10, 50)

    plt.plot(x, np.sin(x))
    plt.plot(x, np.cos(x))
    plt.show()
    i=0
    while True:
        # Wait for the next frame
        if not video.frame_available():
            continue

        teste = video.gst_to_opencv(video._sample)

        frame = video.frame()
        i=i+1
        x = np.linspace(0, 10, i)
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