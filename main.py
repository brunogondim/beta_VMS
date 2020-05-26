# Trabalho de sistemas multimidia UFF-IC-PGC 2020 - Bruno Teixeira Gondim

# Pipeline Gstreamer criado com base no VMS face-counter.py (https://github.com/midiacom/alfa)

# outras referencias gstreamer utilizadas:
# https://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html
# https://www.jonobacon.com/2006/08/28/getting-started-with-gstreamer-with-python/
# http://lifestyletransfer.com/how-to-use-gstreamer-appsink-in-python/
# https://stackoverflow.com/questions/58763496/receive-numpy-array-realtime-from-gstreamer
# https://mathieuduponchelle.github.io/2018-02-15-Python-Elements-2.html?gi-language=undefined
# https://www.jejik.com/articles/2007/01/streaming_audio_over_tcp_with_python-gstreamer/
# https://lazka.github.io/pgi-docs/Gst-1.0/classes/Buffer.html
# https://tewarid.github.io/2011/10/04/read-and-write-raw-pcm-using-gstreamer.html

# referencias python audio
# https://stackoverflow.com/questions/34140831/detecting-a-loud-impulse-sound
# https://www.youtube.com/watch?v=AShHJdSIxkY
# https://www.kaggle.com/fizzbuzz/beginner-s-guide-to-audio-data

# referencias python plot
# https://jakevdp.github.io/PythonDataScienceHandbook/04.00-introduction-to-matplotlib.html
# https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread

# gst-launch-1.0 audiotestsrc ! audioconvert ! autoaudiosink

# filesrc location=/home/bruno/Vprism/beta_VMS/teste.wav

# gst-inspect-1.0 audioconvert

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk#Agg
import matplotlib.pyplot as plt
import tkinter
from scipy.fftpack import fft

import threading

import queue
import multiprocessing
import time
import random

import numpy as np
import wave
import sys
from Class_Audio import Media


window=tkinter.Tk()


def sample_plot(CHUNK, *perfis):    #Function to create the base plot, make sure to make global the lines, axes, canvas and any part that you would want to update later

    global line, line_fft, fig, ax, ax_fft, ax_profile, canvas, perfil_list
    fig, (ax, ax_fft, ax_profile) = plt.subplots(3)
    fig.subplots_adjust(hspace=1) 
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()#show()
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    line, = ax.plot(np.arange(CHUNK),np.random.rand(CHUNK))
    line_fft, = ax_fft.plot(np.linspace(0,44100,CHUNK),np.random.rand(CHUNK))
    ax.set_title('dominio do tempo')
    ax.set_xlabel('amostras')
    ax.set_ylabel('volume')
    ax.set_ylim(0,255)
    ax.set_xlim(0,CHUNK)
    ax_fft.set_title('dominio da frequencia')
    ax_fft.set_xlabel('frequencia')
    ax_fft.set_ylabel('intensidade')
    ax_fft.set_ylim(0,1)
    ax_fft.set_xlim(0,10000)
    ax_profile.set_title('perfil')
    ax_profile.set_xlabel('')
    ax_profile.set_ylabel('')
    ax_profile.get_xaxis().set_visible(False)
    ax_profile.get_yaxis().set_visible(False)
    x_perfil=.2
    y_perfil=1
    perfil_list =[]
    for perfil in perfis:
        y_perfil -= .2
        perfil_list.append(ax_profile.text(x_perfil, y_perfil, perfil, horizontalalignment='center', verticalalignment='center', transform=ax_profile.transAxes))
        if (y_perfil <= .3):
            y_perfil = 1
            x_perfil += .5

def sample_updateplot(q, CHUNK, *perfis):
    try:       #Try to check if there is data in the queue
        result=q.get_nowait()
        #here get crazy with the plotting, you have access to all the global variables that you defined in the plot function, and have the data that the simulation sent.
        line.set_ydata(result)
        line_fft.set_ydata(np.abs(fft(result)) * 2 / (256*CHUNK) )
        perfil_index = 0
        for perfil in perfis:
            perfil_list[perfil_index].set_text(perfil)
            perfil_index +=1
        ax.draw_artist(line)
        canvas.draw()
        #window.after(500,updateplot,q)
    except:
        print ("empty")
        # window.after(500,updateplot,q)

def sample_to_bits(q_sample,q_bits):
    try:       #Try to check if there is data in the queue
        result=q_sample.get_nowait()
        #for i = 0 to result.size - 1:
        for i in result:
            q_bits.put(i)
    except:
        print ("erro na transformação array to bits")
        # window.after(500,updateplot,q)

def bits_to_process(q_bits, q_sample_plot, CHUNK, *perfis):
    try:       #Try to check if there is data in the queue
        #my_array = np.ndarray(shape=(CHUNK,), dtype=np.uint8)
        # i = 0
        # while i <= CHUNK-1:
        #     bit = q_bits.get_nowait()
        #     i+=1
        my_list = [q_bits.get_nowait() for x in range(CHUNK)]
        
        my_array = np.asarray(my_list)


        #here get crazy with the plotting, you have access to all the global variables that you defined in the plot function, and have the data that the simulation sent.
        line.set_ydata(my_array)
        line_fft.set_ydata(np.abs(fft(my_array)) * 2 / (256*CHUNK) )
        perfil_index = 0
        for perfil in perfis:
            perfil_list[perfil_index].set_text(perfil)
            perfil_index +=1
        ax.draw_artist(line)
        canvas.draw()
        #window.after(500,updateplot,q)
    except Exception as e:
        print (str(e))
        # window.after(500,updateplot,q)

if __name__ == '__main__':

    CHUNK = 1024 #* 3
    q_sample = queue.Queue()
    q_bits = queue.Queue() 
    q_sample_plot = multiprocessing.Queue() #Create a queue to share data between process
    profile_amostragem = 0
    profile_canais = 0
    profile_tamanho_buffer_gst = 0
    profile_tamanho_buffer_q_sample = 0 
    profile_tamanho_buffer_q_bits = 0

    sample_plot(CHUNK, profile_amostragem,profile_canais,profile_tamanho_buffer_gst, profile_tamanho_buffer_q_sample, profile_tamanho_buffer_q_bits) #Create the base plot
    media = Media() # Create the media object

    while True:
        # Wait for the next frame
        if not media.sample_available():
            continue

        #teste = media.gst_to_array(media._sampleteste)
        profile_amostragem = media._sampleteste.get_caps().get_structure(0).get_value('rate')
        profile_canais = media._sampleteste.get_caps().get_structure(0).get_value('channels')
        profile_tamanho_buffer_gst = media._sampleteste.get_buffer().get_size()
        profile_tamanho_buffer_q_sample = q_sample.qsize() 
        profile_tamanho_buffer_q_bits = q_bits.qsize()


        sample = media.sample()
        q_sample.put(sample)


        sample_to_bits(q_sample,q_bits)
        if profile_tamanho_buffer_q_bits >= CHUNK:
            bits_to_process(
                q_bits,
                q_sample_plot,
                CHUNK, 
                'amostragem(Hz): ' + str(profile_amostragem),
                'canais: ' + str(profile_canais),
                'buffer_saida_gst: ' + str(profile_tamanho_buffer_gst),
                'buffer_entrada_app: ' + str(profile_tamanho_buffer_q_sample),
                'profile_tamanho_buffer_q_bits: ' + str(profile_tamanho_buffer_q_bits)
                )
        
        # sample_updateplot(
        #     q_sample,
        #     CHUNK, 
        #     'amostragem(Hz): ' + str(profile_amostragem),
        #     'canais: ' + str(profile_canais),
        #     'buffer_saida_gst: ' + str(profile_tamanho_buffer_gst),
        #     'buffer_entrada_app: ' + str(profile_tamanho_buffer_q_sample),
        #     'profile_tamanho_buffer_q_bits: ' + str(profile_tamanho_buffer_q_bits)
        #     )
        



