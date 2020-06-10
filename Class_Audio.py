# Trabalho de sistemas multimidia UFF-IC-PGC 2020 - Bruno Teixeira Gondim
# Pipeline Gstreamer criado com base no VMS face-counter.py (https://github.com/midiacom/alfa)

import numpy as np
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

import queue

class Media():

    def __init__(self, port=5000, comando=''):
        Gst.init(None)
        self.port = port
        self._sample = None
        self._sampleteste = None
        self._sample_queue = queue.Queue(maxsize=10000)
        #self._sample_queue = multiprocessing.Queue()
        self.media_pipe = None
        self.media_sink = None

        self.comando = comando

        self.run()
    
    def run(self):
        self.start_gst()
            # [
            #     self.video_source,
            #     self.video_codec,
            #     self.video_decode,
            #     self.video_sink_conf
            # ])
        if self.comando != 'tocar':
            self.media_sink.connect('new-sample', self.callback)

    def start_gst(self, config=None):
    
        command = ''
        
        if self.comando == '':
            command = 'udpsrc port=5000 ! application/x-rtp, media=audio, clock-rate=44100, width=16, height=16, encoding-name=L16, encoding-params=1, channels=1, channel-positions=1, payload=96 ! \
                                        rtpL16depay ! \
                                        tee name=t ! \
                                            queue ! \
                                                audioconvert ! \
                                                alsasink sync=false t. ! \
                                            queue ! \
                                                audioconvert ! \
                                                audio/x-raw,format=S8,channels=1, rate=44100, max-buffers=1024 ! \
                                                appsink emit-signals=True' # t. ! \
                                            # queue ! \
                                            #     audioconvert ! goom ! videoconvert ! autovideosink'           
        elif self.comando == 'teste':
            command = 'audiotestsrc ! \
                            tee name=t ! \
                                queue ! \
                                    audioconvert ! \
                                    audio/x-raw,format=S8,channels=1, rate=44100 ! \
                                    appsink emit-signals=True t. ! \
                                queue ! \
                                     audioconvert ! \
                                     alsasink sync=false'
            
            #command = 'audiotestsrc ! audioconvert ! audio/x-raw,format=S8,channels=1, rate=44100, max-buffers=1024 ! appsink emit-signals=True' # ou usar: autoaudiosink
            #command = 'filesrc location=/home/bruno/Vprism/beta_VMS/teste.wav ! decodebin ! audioconvert ! audioresample ! audio/x-raw,format=S8,channels=1, rate=44100, max-buffers=1024 ! appsink emit-signals=True'
        elif self.comando == 'tocar':
            #command = 'audiotestsrc ! audioconvert ! autoaudiosink'
            command = 'udpsrc port=5000 ! application/x-rtp, media=audio, clock-rate=44100, width=16, height=16, encoding-name=L16, encoding-params=1, channels=1, channel-positions=1, payload=96 ! rtpL16depay ! audioconvert ! alsasink sync=false'

            #para teste
            # gst-launch-1.0 audiotestsrc ! audioconvert ! autoaudiosink
            # gst-launch-1.0 audiotestsrc ! audioconvert ! udpsink port=10001
            # gst-launch-1.0 filesrc location=/home/bruno/Vprism/beta_VMS/teste.wav ! audioconvert ! udpsink port=10001

            #exemplo de transmissão que deu certo
            #gst-launch-1.0 audiotestsrc ! audioconvert ! audio/x-raw,channels=1,depth=16,width=16,rate=44100 ! rtpL16pay  ! udpsink host=localhost port=5000
            #gst-launch-1.0 filesrc location=/home/bruno/Vprism/beta_VMS/teste.wav ! decodebin ! audioconvert ! audioresample !  audio/x-raw,channels=1,depth=16,width=16,rate=44100 ! rtpL16pay  ! udpsink host=localhost port=5000
            #gst-launch-1.0 -v udpsrc port=5000 ! "application/x-rtp,media=(string)audio, clock-rate=(int)44100, width=16, height=16, encoding-name=(string)L16, encoding-params=(string)1, channels=(int)1, channel-positions=(int)1, payload=(int)96" ! rtpL16depay ! audioconvert ! alsasink sync=false

        self.media_pipe = Gst.parse_launch(command)
        self.media_pipe.set_state(Gst.State.PLAYING)
        self.media_sink = self.media_pipe.get_by_name('appsink0')

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        self._sampleteste = sample
        new_sample = self.gst_to_array(sample)
        self._sample = new_sample
        self._sample_queue.put(new_sample)
        return Gst.FlowReturn.OK

    @staticmethod
    def gst_to_array(sample):
        
        buf = sample.get_buffer()
        caps = sample.get_caps()
        array = np.ndarray(
             (
                 #caps.get_structure(0).get_value('rate'),
                 #caps.get_structure(0).get_value('channels')
                 buf.get_size()
             ),
             buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8) + 128 # por que esse 127 ?
        return array
        #return buf

    def sample(self):
        #sample_extraido = self._sample
        self._sample = None
        sample_extraido = self._sample_queue.get_nowait()
        return sample_extraido

    def sample_available(self):
        return type(self._sample) != type(None)

    

