# src/constants.py

import os
import sys
import logging
import json
import time
import random
import re
import unicodedata
from datetime import datetime
from urllib.parse import urlparse, unquote
from logging.handlers import RotatingFileHandler
from collections import deque
import concurrent.futures
import signal
import gc
import threading
from queue import Queue

# Configuration globale des avertissements
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
