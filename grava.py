# -*- coding: utf-8 -*-

import sys
import os
import subprocess
from time import sleep
from fnmatch import fnmatch
from select import select
import pyaudio
import wave
import thread, time 


AUDIO_DEVICE = 'sysdefault:CARD=P1330NC'

REPEAT_TIMEOUT = 2
STORY_PARTS = 4
REC_DEVICE_IDX = 7
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000
RECORD_TIME = 2

WAVE_OUTPUT_FILENAME = "output.wav"
LAST_PARTS = 3

WAIT_TO_RECORD = 2

#pa = pyaudio.PyAudio()

def record(filename):
    stream = pa.open(format=FORMAT,
                     channels=CHANNELS,
                     input_device_index=REC_DEVICE_IDX,
                     rate=RATE,
                     input=True,
                     frames_per_buffer=CHUNK)
    
    frames = []
    
    for i in range(0, int(RATE / CHUNK * RECORD_TIME)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    pa.terminate()
    
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pa.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close() 

def play(filename):
    pa = pyaudio.PyAudio() 
    wf = wave.open(filename, 'rb')
    stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                     channels=wf.getnchannels(),
                     rate=wf.getframerate(),
                     output=True)
    
    data = wf.readframes(CHUNK)
    
    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)
    
        stream.stop_stream()
        stream.close()
    
        pa.terminate()
 
if len(sys.argv) > 1:
    story_dir = sys.argv[1]
    
    if not os.path.isdir(story_dir):
        os.mkdir(story_dir)

    # Vai pro diretorio da historia
    os.chdir(story_dir)

files = os.listdir('.')
story_parts = sorted([p for p in files if fnmatch(p, "part-??.mp3")])

if story_parts:
    last_number = story_parts[-1].split('-')[1].split('.')[0]
    last_number = int(last_number)
else:
    last_number = 0

record_command = ['arecord', 
                  '--device={}'.format(AUDIO_DEVICE), 
                  '-f',
                  'cd']

part_name = 'part-{0:02d}.mp3'

lame_command = ['lame',
               '-r',
               '-']


parts_list = 'concat:{}'
story_file = 'story-{}.mp3'
avconv_command = ['avconv',
                  '-y',
                  '-i',
                  parts_list,
                  '-acodec',
                  'copy',
                  story_file]

fnull = open(os.devnull, "w")

def concatenate_parts():
    files = os.listdir('.') 
    story_parts = sorted([p for p in files if fnmatch(p, "part-??.mp3")]) 
    story_parts = ["../era-uma-vez.mp3"] + story_parts
    str_conc = reduce(lambda x,y: "{}|{}".format(x,y), story_parts)
    avconv_command[3] = parts_list.format(str_conc)
    avconv_command[6] = story_file.format(story_dir)
    subprocess.call(avconv_command, stdout=fnull, stderr=fnull)
    
def input_thread(L):
   raw_input()
   L.append(None)

def do_print():
    L = []
    thread.start_new_thread(input_thread, (L,))
    while 1:
        time.sleep(.1)
        print "E"
        if L: break
 
 
while True:
    last_number = last_number + 1 

    # Se possui número máximo de partes, concatena e para
    if last_number > STORY_PARTS:
        concatenate_parts()
        sys.exit()
       
    print "ESPERANDO ALGUEM ENTRAR E APERTAR O BOTAO"
    e = raw_input()
    print "APERTOU, ESPERA APERTAR NOVAMENTE PRA GRAVAR..."

    subprocess.call(["mpg123", '../era-uma-vez.mp3'], stdout=fnull, stderr=fnull) 

    if last_number > 1:
        files = os.listdir('.') 
        story_parts = sorted([p for p in files if fnmatch(p, "part-??.mp3")]) 

        for p in story_parts[-LAST_PARTS:]:
            subprocess.call(["mpg123", p], stdout=fnull,
                        stderr=fnull)

    subprocess.call(["mpg123", "../continuar.mp3"], stdout=fnull,
                        stderr=fnull)

    print "APERTE O BOTAO PRA GRAVAR"
    while True:

       rlist, _, _ = select([sys.stdin], [], [], WAIT_TO_RECORD)

       if rlist:
           s = sys.stdin.readline()
           rlist = None
           break
       else:
           break
 
    print "APERTOU, COMEÇA A GRAVAR..."

    # Gera nome para a parte a ser gravada
    part = part_name.format(last_number)
    lame_command.append(part) 
 
    gravando = True
    while gravando:

        # Grava con o arecord e converte para mp3 com o lame
        rec = subprocess.Popen(record_command, stdin=None, stderr=fnull, stdout=subprocess.PIPE)
        lame = subprocess.Popen(lame_command, stdout=fnull, stderr=fnull, stdin=rec.stdout)
        rec.stdout.close()
        sleep(RECORD_TIME)
        rec.terminate()
        lame.terminate()

        # Loop para tocar novamente o que foi gravado

        print "OUÇA O QUE GRAVOU"
        subprocess.call(["mpg123", "../escute.mp3"], stdout=fnull,
                            stderr=fnull)
        subprocess.call(["mpg123", part], stdout=fnull,
                            stderr=fnull)
        subprocess.call(["mpg123", "../novamente.mp3"])
 
        while True:
            rlist, _, _ = select([sys.stdin], [], [], REPEAT_TIMEOUT)

            if rlist:
                s = sys.stdin.readline()
                break
            else:
                gravando = False
                break

