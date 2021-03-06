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
import paho.mqtt.publish as publish
from scipy.fftpack import fft

import threading

import queue
import multiprocessing
import time
import random

import numpy as np
import datetime
import time
import wave
import sys
from Class_Audio import Media


window=tkinter.Tk()
#window.geometry('500x500')

def sample_plot(CHUNK):    #Function to create the base plot, make sure to make global the lines, axes, canvas and any part that you would want to update later

    global line, line_fft, fig, ax, ax_fft, ax_profile, canvas, perfil_list, perfil_list_analise
    fig, (ax, ax_fft, ax_profile, ax_analise) = plt.subplots(4,figsize = (7,7))
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
    ax_analise.set_title('analise')
    ax_analise.set_xlabel('')
    ax_analise.set_ylabel('')
    ax_analise.get_xaxis().set_visible(False)
    ax_analise.get_yaxis().set_visible(False)    
    x_perfil=.2
    y_perfil=1
    perfil_list =[]
    perfil_list_analise =[]
    for x in range(8):
        y_perfil -= .2
        perfil_list.append(ax_profile.text(x_perfil, y_perfil, '', horizontalalignment='center', verticalalignment='center', transform=ax_profile.transAxes))
        perfil_list_analise.append(ax_analise.text(x_perfil, y_perfil, '', horizontalalignment='center', verticalalignment='center', transform=ax_analise.transAxes))
        if (y_perfil <= .3):
            y_perfil = 1
            x_perfil += .5

def update_plot():
    
    global profile_amostragem
    global profile_canais
    global profile_tamanho_CHUNK_gst
    global profile_tamanho_CHUNK_analise
    global profile_tamanho_buffer_gst
    global profile_tamanho_buffer_q_sample
    global profile_tamanho_buffer_q_sample_pre_processado
    
    global my_array_show
    global my_array_fft_show
    global my_array_MAX_amplitude
    global my_array_MEAN_amplitude
    global my_array_MIN_amplitude
    global my_array_MAX_REL
    global my_array_MAX_bit_delta
    
    global hora_do_disparo
    global amplitude_do_disparo 
    global delta_bit_do_disparo
   
    try:       
        
        my_array_show_draw = my_array_show
        my_array_fft_show_draw = my_array_fft_show
        line.set_ydata(my_array_show_draw)
        line_fft.set_ydata(my_array_fft_show_draw)

        perfil_list[0].set_text('amostragem(Hz): ' + str(profile_amostragem))
        perfil_list[1].set_text('canais: ' + str(profile_canais))
        perfil_list[2].set_text('CHUNK saida gst: ' + str(profile_tamanho_CHUNK_gst))
        perfil_list[3].set_text('CHUNK entrada app: ' + str(profile_tamanho_CHUNK_analise))
        perfil_list[4].set_text('buffer0 gst: ' + str(profile_tamanho_buffer_gst))
        perfil_list[5].set_text('buffer1 entrada: ' + str(profile_tamanho_buffer_q_sample))
        perfil_list[6].set_text('buffer2 pré processado: ' + str(profile_tamanho_buffer_q_sample_pre_processado))

        perfil_list_analise[0].set_text('MAX_amplitude: ' + str(my_array_MAX_amplitude))
        perfil_list_analise[1].set_text('MEAN_amplitude: ' + str(my_array_MEAN_amplitude))
        perfil_list_analise[2].set_text('MIN_amplitude: ' + str(my_array_MIN_amplitude))
        perfil_list_analise[3].set_text('MAX_amp_REL: ' + str(my_array_MAX_REL))
        perfil_list_analise[4].set_text('MAX_bit_delta: ' + str(my_array_MAX_bit_delta))

        if disparo_detectado == True:
            perfil_list_analise[5].set_text('hora_do_disparo: ' + str(hora_do_disparo))
            perfil_list_analise[6].set_text('amplitude_do_disparo: ' + str(amplitude_do_disparo[0]) + ' (' + str(amplitude_do_disparo[1]) + ',+' + str(amplitude_do_disparo[2] - 1) + ')')
            perfil_list_analise[7].set_text('delta_bit_do_disparo: ' + str(delta_bit_do_disparo[0]) + ' (' + str(delta_bit_do_disparo[1]) + ',+' + str(delta_bit_do_disparo[2] - 1) + ')')
        else:
            perfil_list_analise[5].set_text('hora_do_disparo: ' )
            perfil_list_analise[6].set_text('amplitude_do_disparo: ')
            perfil_list_analise[7].set_text('delta_bit_do_disparo: ' )

        ax.draw_artist(line)
        ax_fft.draw_artist(line_fft)
        canvas.draw()
        window.after(0,update_plot)
    except Exception as e:
        print (str(e))
        # window.after(500,updateplot,q)

def profile():

    global media

    global profile_amostragem
    global profile_canais
    global profile_tamanho_CHUNK_gst
    global profile_tamanho_buffer_gst

    global profile_tamanho_buffer_q_sample
    global q_sample

    global profile_tamanho_buffer_q_sample_pre_processado
    global q_sample_pre_processado
    
    while True:
        if media._sampleteste != None:
            #teste = media.gst_to_array(media._sampleteste)
            profile_amostragem = media._sampleteste.get_caps().get_structure(0).get_value('rate')
            profile_canais = media._sampleteste.get_caps().get_structure(0).get_value('channels')
            profile_tamanho_CHUNK_gst = media._sampleteste.get_buffer().get_size()
            profile_tamanho_buffer_gst = media._sample_queue.qsize()
            profile_tamanho_buffer_q_sample = q_sample.qsize()
            profile_tamanho_buffer_q_sample_pre_processado = q_sample_pre_processado.qsize() 


def enfileiramento_q_sample():

    global media
    global q_sample

    while True:
        #if not media.sample_available():
        if media._sample_queue.qsize() == 0:
            continue
        
        sample = media.sample()
        q_sample.put(sample)

def enfileiramento_q_sample_pre_processado():
    
    global q_sample
    global q_sample_pre_processado
    global CHUNK

    temp = np.empty(0,dtype='uint8')
    while True:
        if q_sample.empty():
            continue
        try:       #Try to check if there is data in the queue
            novo = q_sample.get_nowait()
            temp_c =np.concatenate((temp,novo))
            temp = temp_c
            if temp.size >= CHUNK:
                temp_2, temp_3, lixo = np.hsplit(temp,[CHUNK,temp.size])
                temp = temp_3
                q_sample_pre_processado.put(temp_2)

            # q_sample_pre_processado.put(novo)
        except:
            print ("erro na transformação array to bits")
    
def enfileiramento_processamento():
    
    global q_sample_pre_processado
    global CHUNK
    
    global my_array
    global my_array_show
    global my_array_fft
    global my_array_fft_show
    global my_array_MAX_amplitude
    global my_array_MEAN_rolling
    global my_array_MEAN_rolling_aux
    global my_array_MEAN_amplitude
    global my_array_MEAN_amplitude_array
    global my_array_MEAN_amplitude_array_aux
    global my_array_MIN_amplitude
    global my_array_MAX_REL
    global my_array_MAX_bit_delta

    global disparo_detectado
    global hora_do_disparo
    global amplitude_do_disparo 
    global delta_bit_do_disparo 

    my_array = 0
    my_array_show = 0
    my_array_fft = 0
    my_array_fft_show = 0
    my_array_MAX_amplitude = 0
    my_array_MEAN_rolling = 1 # média móvel
    my_array_MEAN_rolling_aux = False
    my_array_MEAN_amplitude = 0
    my_array_MEAN_amplitude_array = np.empty(my_array_MEAN_rolling,dtype=float)
    my_array_MEAN_amplitude_array_aux = 0
    my_array_MIN_amplitude = 9999999999
    my_array_MAX_REL = 0
    my_array_MAX_bit_delta = 0

    disparo_detectado = False
    hora_do_disparo = datetime.time()
    amplitude_do_disparo = 0
    delta_bit_do_disparo = 0
    contador = 0

    while True:
        if q_sample_pre_processado.empty():
            if disparo_detectado and time.time()-contador>=10:
                disparo_detectado = False
                my_array_show = 0
                my_array_fft_show = 0 
            continue

        try:       #Try to check if there is data in the queue
            my_array = q_sample_pre_processado.get_nowait()
            #my_array_fft = np.abs(fft(my_array)) * 2 / (256*CHUNK) # transformada consome muito processamento!

            #temp_MAX = np.amax(my_array)
            temp_MAX_index = np.where(my_array == np.amax(my_array))
            temp_MAX_index_plus = len(temp_MAX_index[0])
            temp_MAX = my_array[temp_MAX_index[0][0]]
            if my_array_MAX_amplitude <= temp_MAX:
                my_array_MAX_amplitude = temp_MAX

            temp_MEAN = np.mean(my_array)     
            my_array_MEAN_amplitude_array[my_array_MEAN_amplitude_array_aux] = temp_MEAN
            my_array_MEAN_amplitude_array_aux+=1
            if my_array_MEAN_amplitude_array_aux >= my_array_MEAN_rolling-1:
                my_array_MEAN_amplitude_array_aux = 0
                my_array_MEAN_rolling_aux = True
            if my_array_MEAN_rolling_aux == True:
                my_array_MEAN_amplitude = np.around(np.mean(my_array_MEAN_amplitude_array),decimals=1)

            # temp_MIN = np.amin(my_array)
            temp_MIN_index = np.where(my_array == np.amin(my_array))
            temp_MIN_index_plus = len(temp_MIN_index[0])
            temp_MIN = my_array[temp_MIN_index[0][0]]            
            if my_array_MIN_amplitude >= temp_MIN:
                my_array_MIN_amplitude = temp_MIN

            temp_MAX_MEAN = abs(temp_MEAN - temp_MAX)
            temp_MIN_MEAN = abs(temp_MEAN - temp_MIN)
            if temp_MAX_MEAN >= temp_MIN_MEAN:
                temp_MAX_REL = np.around(temp_MAX_MEAN,decimals=1)
                temp_MAX_REL_index = temp_MAX_index
                temp_MAX_REL_index_plus = temp_MAX_index_plus
            else:
                temp_MAX_REL = np.around(temp_MIN_MEAN,decimals=1)
                temp_MAX_REL_index = temp_MIN_index
                temp_MAX_REL_index_plus = temp_MIN_index_plus
            if my_array_MAX_REL < temp_MAX_REL:
                my_array_MAX_REL = temp_MAX_REL


            temp_diff_array = np.diff(np.array(my_array,dtype=int))
            temp_diff_array_ABS = np.absolute(temp_diff_array)
            #temp_diff_array_ABS_MAX = np.amax(temp_diff_array_ABS)
            temp_diff_array_ABS_MAX_index = np.where(temp_diff_array_ABS == np.amax(temp_diff_array_ABS))
            temp_diff_array_ABS_MAX_index_plus = len(temp_diff_array_ABS_MAX_index[0])
            temp_diff_array_ABS_MAX = my_array[temp_diff_array_ABS_MAX_index[0][0]]            
            if my_array_MAX_bit_delta <= temp_diff_array_ABS_MAX:
                my_array_MAX_bit_delta = temp_diff_array_ABS_MAX


            ###detecção do disparo

            if disparo_detectado == False and temp_MAX_REL >= 83 and temp_diff_array_ABS_MAX >= 20:
                
                disparo_detectado = True

                hora_do_disparo = datetime.datetime.now().strftime("%H:%M:%S")
                amplitude_do_disparo = [temp_MAX_REL,temp_MAX_REL_index[0][0],temp_MAX_REL_index_plus]
                delta_bit_do_disparo = [temp_diff_array_ABS_MAX,temp_diff_array_ABS_MAX_index[0][0],temp_diff_array_ABS_MAX_index_plus]

                my_array_fft_show = np.abs(fft(my_array)) * 2 / (256*CHUNK) # transformada consome muito processamento!

                contador = time.time()
                my_array_show = my_array
                #my_array_fft_show = my_array_fft

            if disparo_detectado == False:
                my_array_show = my_array

        except Exception as e:
            print (str(e))

def envio_da_sinalização():

    global disparo_detectado
    global hora_do_disparo

    
    if disparo_detectado:
        sinalização = 'disparo ocorrido às' + hora_do_disparo
    else:
        sinalização = "detectando..."

    #publish.single(mqtt_topic, sinalização, hostname=mqtt_hostname, port=int(mqtt_port))
    


if __name__ == '__main__':

    global media
    media = Media() # Create the media object
    #media = Media(comando='teste') 
    #media = Media(comando='tocar')

    global mqtt_topic
    global mqtt_hostname
    global mqtt_port
    # mqtt_topic = sys.argv[1]
    # mqtt_hostname = sys.argv[2]
    # mqtt_port = sys.argv[3]

    global CHUNK
    global profile_amostragem
    global profile_canais
    global profile_tamanho_CHUNK_gst
    global profile_tamanho_CHUNK_analise
    global profile_tamanho_buffer_gst
    global profile_tamanho_buffer_q_sample 
    global profile_tamanho_buffer_q_sample_pre_processado
    
    CHUNK = 1024 * 20
    profile_amostragem = 0
    profile_canais = 0
    profile_tamanho_CHUNK_gst = 0
    profile_tamanho_CHUNK_analise = CHUNK
    profile_tamanho_buffer_gst = 0
    profile_tamanho_buffer_q_sample = 0 
    profile_tamanho_buffer_q_sample_pre_processado= 0

    sample_plot(CHUNK) #Create the base plot

    global q_sample
    global q_sample_pre_processado
    global q_sample_plot
    global q_sample_plot_fft

    q_sample = multiprocessing.Queue()
    q_sample_pre_processado = multiprocessing.Queue() 
    q_sample_plot = multiprocessing.Queue(maxsize=100000) #Create a queue to share data between process
    q_sample_plot_fft = multiprocessing.Queue(maxsize=1) #Create a queue to share data between process

    thread_profile = threading.Thread(target=profile)
    thread_profile.start()

    thread_enfileiramento_q_sample = threading.Thread(target=enfileiramento_q_sample)
    thread_enfileiramento_q_sample.start()

    thread_enfileiramento_q_sample_pre_processado = threading.Thread(target=enfileiramento_q_sample_pre_processado)
    thread_enfileiramento_q_sample_pre_processado.start()

    thread_enfileiramento_processamento = threading.Thread(target=enfileiramento_processamento)
    thread_enfileiramento_processamento.start()
    
    # while True:
    #     update_plot()
    update_plot()
    window.mainloop()




