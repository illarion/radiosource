import subprocess, shlex
import meta


class FfmpegRecoder(object):
    CMD = 'ffmpeg -i "{input}" -metadata title="{title}" -metadata artist="{artist}" -vn -codec:a libvorbis -b:a {bitrate}k -minrate {bitrate}k -maxrate {bitrate}k -f ogg pipe:1 '
    # CMD = 'ffmpeg -i "{input}" -strict -2 -vn -codec:a libmp3lame -b:a {bitrate}k -f mp3 -'

    def __init__(self, input_file_name, bitrate=128):
        self.input_file_name = input_file_name
        self.bitrate = bitrate
        artist, title = meta.parse_fn(input_file_name)
        self.cmdline = FfmpegRecoder.CMD.format(input=input_file_name,
                                                bitrate=bitrate,
                                                title=title,
                                                artist=artist)

        args = shlex.split(self.cmdline)
        null = open('/dev/null', mode='w')
        self.p = subprocess.Popen(args,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=null)
        print self.cmdline

    def read(self, n=-1):
        return self.p.stdout.read(n)

    def close(self):
        self.p.terminate()
        return self.p.stdout.close()

    def closed(self):
        return self.p.stdout.closed()