import subprocess, shlex
import meta


class FfmpegRecoder(object):
    CMD = ('ffmpeg -i "{input}" -acodec pcm_s16le -ac 2 -f wav pipe:1',
           'oggenc - -b {bitrate} --managed -o -')

    # CMD = 'ffmpeg -i "{input}" -metadata title="{title}" -metadata artist="{artist}" -vn -codec:a libvorbis -b:a {
    # bitrate}k -minrate {bitrate}k -maxrate {bitrate}k -f ogg pipe:1 '
    # CMD = 'ffmpeg -i "{input}" -strict -2 -vn -codec:a libmp3lame -b:a {bitrate}k -f mp3 -'

    def __init__(self, input_file_name, bitrate=128):
        self.input_file_name = input_file_name
        self.bitrate = bitrate
        artist, title = meta.parse_fn(input_file_name)

        cmdlines = [x.format(input=input_file_name,
                             bitrate=bitrate,
                             title=title,
                             artist=artist) for x in FfmpegRecoder.CMD]

        null = open('/dev/null', mode='w')

        self.p1 = subprocess.Popen(shlex.split(cmdlines[0]),
                                   # stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=null)

        self.p2 = subprocess.Popen(shlex.split(cmdlines[1]),
                                   stdin=self.p1.stdout,
                                   stdout=subprocess.PIPE,
                                   stderr=null)

    def read(self, n=-1):
        return self.p2.stdout.read(n)

    def close(self):
        self.p1.terminate()
        self.p2.terminate()
        return self.p2.stdout.close()

    def closed(self):
        return self.p2.stdout.closed()
