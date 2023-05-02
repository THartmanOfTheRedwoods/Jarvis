#!/usr/bin/env python

from gtts import gTTS
from io import BytesIO
from pygame import mixer, time

class Mouth:

    def __init__(self):
        self.language = 'en'
        self.slow = False
        self.tld = 'com'  # tld options - US: 'com', UK: 'co.uk', Australia: 'com.au'
        mixer.init()

    def speak(self, message):
        mem_file = BytesIO()
        tts_obj = gTTS(text=message, lang=self.language, slow=self.slow, tld=self.tld)
        tts_obj.write_to_fp(mem_file)
        mem_file.seek(0)
        mixer.music.load(mem_file, "mp3")
        mixer.music.play()
        while mixer.music.get_busy():
            time.Clock().tick(10)


if __name__ == '__main__':
    m = Mouth()
    m.speak("Hello World")
