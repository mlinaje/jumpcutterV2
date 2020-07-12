import glob
import sys
import os
import subprocess
import argparse
from shutil import rmtree
from fastVideo import fastVideo
from fasterVideo import fasterVideo

TEMP_FOLDER = ".TEMP_LONG"
if os.path.exists(TEMP_FOLDER):
	rmtree(TEMP_FOLDER)

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser()
parser.add_argument("videoFile", help="the path to the video file you want modified.")
parser.add_argument(
    "-v",
    "--videoSpeed",
    type=float,
    default=1.0,
    help="the speed that the video plays at.",
)
parser.add_argument(
    "--silentSpeed",
    "-s",
    type=float,
    default=99999,
    help="the speed that silent frames should be played at.",
)
parser.add_argument(
    "--silentThreshold",
    "-t",
    type=float,
    default=0.04,
    help="the volume that frames audio needs to surpass to be sounded. It ranges from 0 to 1.",
)
parser.add_argument(
    "--frameMargin",
    "-m",
    type=int,
    default=4,
    help="tells how many frames on either side of speech should be included.",
)
parser.add_argument(
    "--splitDuration",
    "-d",
    type=int,
    default=1800,
    help="tells how many seconds should the video split chunks be, \
        use lower values if system has low ram, default 1800 (30 minutes).",
)
parser.add_argument(
    "--open", 
    "-o", 
    type=str2bool, 
    nargs='?', 
    const=True, 
    default=False,
    help="open file after processing is complete. Accepts boolean as input",
)
args = parser.parse_args()

videoFile = args.videoFile

try:
    os.mkdir(TEMP_FOLDER)
except OSError:
    rmtree(TEMP_FOLDER)
    os.mkdir(TEMP_FOLDER)

# splitting
filename, filetype = os.path.splitext(videoFile)
splitVideo = 'ffmpeg -i "{}" -acodec copy -f segment -segment_time {} -vcodec copy -reset_timestamps 1 -map 0 {}/%d{}'.format(
    videoFile, args.splitDuration, TEMP_FOLDER, filetype
)
subprocess.call(splitVideo, shell=True)


# processing
if args.silentSpeed == 99999 and args.videoSpeed == 1.0:
    for files in os.listdir(TEMP_FOLDER):
        videoPath = os.path.join('{}', '{}').format(TEMP_FOLDER, files)
        fasterVideo(videoPath, args.silentThreshold, args.frameMargin)
        os.remove(videoPath)
else:
    for files in os.listdir(TEMP_FOLDER):
        videoPath = os.path.join('{}', '{}').format(TEMP_FOLDER, files)
        fastVideo(
            videoPath,
            args.silentSpeed,
            args.videoSpeed,
            args.silentThreshold,
            args.frameMargin,
        )
        os.remove(videoPath)

MyFile=open('mylist.txt','w')

for item in glob.glob(os.path.join('.', TEMP_FOLDER, '*.mp4')):
	MyFile.write("file '")
	MyFile.write(item)
	MyFile.write("'\n")

MyFile.close()


concatVideo = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "mylist.txt", "-c", "copy", filename + "_faster.mp4"]
subprocess.call(concatVideo)

os.remove('mylist.txt')

outFile = filename + "_faster.mp4"

if not os.path.isfile(outFile):
    raise IOError(f"the file {outFile} was not created")

if args.open:
    try:  # should work on Windows
        os.startfile(outFile)
    except AttributeError:
        try:  # should work on MacOS and most linux versions
            subprocess.call(["open", outFile])
        except:
            try: # should work on WSL2
                subprocess.call(["cmd.exe", "/C", "start", outFile])
            except:
                print("could not open output file")

rmtree(TEMP_FOLDER)
