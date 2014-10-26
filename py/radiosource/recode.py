import subprocess, shlex


class FfmpegRecoder(object):

    CMD = 'ffmpeg -i "{input}" -vn -codec:a libmp3lame -b:a {bitrate}k -f mp3 -'

    def __init__(self, input_file_name, bitrate=128):
        self.input_file_name = input_file_name
        self.bitrate = bitrate
        self.cmdline = FfmpegRecoder.CMD.format(input=input_file_name, bitrate=bitrate)

        args = shlex.split(self.cmdline)
        null = open('/dev/null', mode='w')
        self.p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=null)
        print self.cmdline

    def read(self, n=-1):
        return self.p.stdout.read(n)

    def close(self):
        return self.p.stdout.close()

    def closed(self):
        return self.p.stdout.closed()