import os
from .microphone import MicrophoneStream
from .google import manage_stream

__version__ = '0.1.0'
__license__ = 'MIT'
__author__ = 'Edward Li and Konwoo Kim'

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

__all__ = [
    'MicrophoneStream',
    'manage_stream'
]
