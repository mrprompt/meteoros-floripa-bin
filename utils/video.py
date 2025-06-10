import os
import subprocess

from . import config

def converter(video_input: str, video_output: str):
    configuration = config.load_config()
    converter_path = configuration['converter']['path']

    if not os.path.exists(converter_path):
        return

    if os.path.exists(video_input) and not os.path.exists(video_output):
        subprocess.Popen([
            converter_path,
            '-loglevel',
            'error',
            '-hide_banner',
            '-nostats',
            '-n',
            '-i',
            video_input,
            '-c:v',
            'libx264',
            '-profile:v',
            'baseline',
            '-level',
            '3.0',
            '-pix_fmt',
            'yuv420p',
            video_output
        ])
