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
#AUDIO_DEVICE = 'sysdefault:CARD=Pro'
REPEAT_TIMEOUT = 2
STORY_PARTS = 4
RECORD_TIME = 5
LAST_PARTS = 3
WAIT_TO_RECORD = 2
MAX_TRIES = 2

if len(sys.argv) > 1:
    story_dir = sys.argv[1]
    
    if not os.path.isdir(story_dir):
        os.mkdir(story_dir)

    # Vai pro diretorio da historia
    os.chdir(story_dir)

files = os.listdir('.')
story_parts = sorted([p for p in files if fnmatch(p, "part-??.ogg")])

if story_parts:
    last_number = story_parts[-1].split('-')[1].split('.')[0]
    last_number = int(last_number)
else:
    last_number = 0

rec_cmd = [ 'rec',
            "OUTPUT",
            'trim',
            '00:00:00.2']

part_name = 'part-{0:02d}.ogg'

parts_list = '{}'
story_file = 'story-{}.ogg'

fnull = open(os.devnull, "w")

def concatenate_parts():
    concat_cmd = ['sox']
    files = os.listdir('.') 
    story_parts = sorted([p for p in files if fnmatch(p, "part-??.ogg")]) 
    story_parts = ["../era-uma-vez.ogg"] + story_parts
    concat_cmd += story_parts
    concat_cmd.append(story_file.format(story_dir))
    subprocess.call(concat_cmd, stdout=fnull, stderr=fnull)

def wait_button(timeout=0):
    tcflush(sys.stdin, TCIOFLUSH)

    if not timeout:
        raw_input()
        return False
    else:
        while True:
           rlist, _, _ = select([sys.stdin], [], [], timeout)

           if rlist:
               sys.stdin.readline()
               rlist = None
               return False
           else:
               return True

def play(part_name):
    parts = { 'era uma vez': '../era-uma-vez.ogg' 
            , 'aperte para continuar': "../continuar.ogg"
            , 'voce gravou': "../escute.ogg"
            , 'aperte para gravar novamente': "../novamente.ogg" }

    if parts.has_key(part_name):
        subprocess.call(["mplayer", parts[part_name]], stdout=fnull, stderr=fnull) 
    else:
        subprocess.call(["mplayer", part_name], stdout=fnull, stderr=fnull) 

last_number += 1

while True:
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
        story_parts = sorted([p for p in files if fnmatch(p, "part-??.ogg")]) 

        for p in story_parts[-LAST_PARTS:]:
            subprocess.call(["mplayer", p], stdout=fnull,
                        stderr=fnull)

    play('aperte para continuar')

    print "APERTE O BOTAO PRA GRAVAR"
    timeout = wait_button(WAIT_TO_RECORD)

    if not timeout:

        print "APERTOU, COMEÇA A GRAVAR..."

        # Gera nome para a parte a ser gravada
        part = part_name.format(last_number)
        rec_cmd[1] = part
 
        # Loop para gravar 
        repeat = 0
        while True:
            if timeout or repeat >= MAX_TRIES:
               last_number = last_number + 1 
               break       
            print "GRAVANDO..."

            # Grava con o arecord e converte para mp3 com o lame
            rec = subprocess.Popen(rec_cmd, stdin=None, stderr=fnull,
                    stdout=fnull)
            timeout = wait_button(RECORD_TIME)
            sleep(1)
            rec.terminate()

            print "OUÇA O QUE GRAVOU E REGRAVE SE QUISER"

            repeat += 1

            play('voce gravou')
            play(part)

            if repeat < MAX_TRIES:
                play('aperte para gravar novamente')
                print "APERTE PARA REGRAVAR"

            timeout = wait_button(REPEAT_TIMEOUT)


