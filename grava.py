# -*- coding: utf-8 -*-

import sys
import os
import subprocess
from time import sleep
from fnmatch import fnmatch
from select import select
import thread, time 
from termios import tcflush, TCIOFLUSH 


AUDIO_DEVICE = 'sysdefault:CARD=P1330NC'

REPEAT_TIMEOUT = 2
STORY_PARTS = 4
RECORD_TIME = 2

LAST_PARTS = 3

WAIT_TO_RECORD = 2

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

def wait_button(timeout=0):
    tcflush(sys.stdin, TCIOFLUSH)

    if not timeout:
        e = raw_input()
        return False
    else:
        while True:
           rlist, _, _ = select([sys.stdin], [], [], timeout)

           if rlist:
               s = sys.stdin.readline()
               rlist = None
               return False
           else:
               return True

def play(part_name):
    parts = { 'era uma vez': '../era-uma-vez.mp3' 
            , 'aperte para continuar': "../continuar.mp3"
            , 'voce gravou': "../escute.mp3"
            , 'aperte para gravar novamente': "../novamente.mp3" }

    if parts.has_key(part_name):
        subprocess.call(["mpg123", parts[part_name]], stdout=fnull, stderr=fnull) 
    else:
        subprocess.call(["mpg123", part_name], stdout=fnull, stderr=fnull) 
    
while True:
    last_number = last_number + 1 

    # Se possui número máximo de partes, concatena e para
    if last_number > STORY_PARTS:
        concatenate_parts()
        sys.exit()
       
    print "ESPERANDO ALGUEM ENTRAR E APERTAR O BOTAO"
    wait_button()
    print "APERTOU, ESPERA APERTAR NOVAMENTE PRA GRAVAR..."

    play('era uma vez')

    # Toca ultimas LAST_PARTS da historia
    if last_number > 1:
        files = os.listdir('.') 
        story_parts = sorted([p for p in files if fnmatch(p, "part-??.mp3")]) 

        for p in story_parts[-LAST_PARTS:]:
            subprocess.call(["mpg123", p], stdout=fnull,
                        stderr=fnull)

    play('aperte para continuar')

    print "APERTE O BOTAO PRA GRAVAR"
    wait_button(WAIT_TO_RECORD)
    print "APERTOU, COMEÇA A GRAVAR..."

    # Gera nome para a parte a ser gravada
    part = part_name.format(last_number)
    lame_command.append(part) 
 
    # Loop para gravar 
    while True:

        # Grava con o arecord e converte para mp3 com o lame
        rec = subprocess.Popen(record_command, stdin=None, stderr=fnull, stdout=subprocess.PIPE)
        lame = subprocess.Popen(lame_command, stdout=fnull, stderr=fnull, stdin=rec.stdout)
        rec.stdout.close()
        sleep(RECORD_TIME)
        rec.terminate()
        lame.terminate()

        print "OUÇA O QUE GRAVOU E REGRAVE SE QUISER"

        play('voce gravou')
        play(part)
        play('aperte para gravar novamente')

        timeout = wait_button(REPEAT_TIMEOUT)

        if timeout:
            lame_command.pop()
            break
