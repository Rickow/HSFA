"""Modules utilises par les scripts du depot pendant une construction (releve_imports.py) : cites ici pour que
PyInstaller les embarque. Fichier genere ; ne pas modifier a la main."""
# noqa: F401
import importlib
MODULES = [
    'PIL',
    'PIL.ExifTags',
    'PIL.GimpGradientFile',
    'PIL.GimpPaletteFile',
    'PIL.Image',
    'PIL.ImageChops',
    'PIL.ImageColor',
    'PIL.ImageFile',
    'PIL.ImageMode',
    'PIL.ImagePalette',
    'PIL.ImageSequence',
    'PIL.PaletteFile',
    'PIL.PngImagePlugin',
    'PIL.TiffTags',
    '__future__',
    '_abc',
    '_ast',
    '_bisect',
    '_blake2',
    '_bz2',
    '_codecs',
    '_collections',
    '_collections_abc',
    '_colorize',
    '_compat_pickle',
    '_contextvars',
    '_csv',
    '_ctypes',
    '_cython_3_3_0',
    '_datetime',
    '_decimal',
    '_functools',
    '_hashlib',
    '_heapq',
    '_hmac',
    '_imp',
    '_interpreters',
    '_io',
    '_json',
    '_locale',
    '_lzma',
    '_opcode',
    '_opcode_metadata',
    '_operator',
    '_pickle',
    '_posixsubprocess',
    '_py_warnings',
    '_queue',
    '_random',
    '_signal',
    '_sitebuiltins',
    '_socket',
    '_sre',
    '_ssl',
    '_stat',
    '_statistics',
    '_string',
    '_struct',
    '_thread',
    '_tokenize',
    '_types',
    '_typing',
    '_warnings',
    '_weakref',
    '_weakrefset',
    '_zstd',
    'abc',
    'annotationlib',
    'argparse',
    'array',
    'ast',
    'atexit',
    'base64',
    'binascii',
    'bisect',
    'builtins',
    'bz2',
    'capstone',
    'capstone.arm',
    'capstone.arm64',
    'capstone.arm64_const',
    'capstone.arm_const',
    'capstone.bpf',
    'capstone.bpf_const',
    'capstone.evm',
    'capstone.evm_const',
    'capstone.m680x',
    'capstone.m680x_const',
    'capstone.m68k',
    'capstone.m68k_const',
    'capstone.mips',
    'capstone.mips_const',
    'capstone.mos65xx',
    'capstone.mos65xx_const',
    'capstone.ppc',
    'capstone.ppc_const',
    'capstone.riscv',
    'capstone.riscv_const',
    'capstone.sh',
    'capstone.sh_const',
    'capstone.sparc',
    'capstone.sparc_const',
    'capstone.systemz',
    'capstone.sysz_const',
    'capstone.tms320c64x',
    'capstone.tms320c64x_const',
    'capstone.tricore',
    'capstone.tricore_const',
    'capstone.wasm',
    'capstone.wasm_const',
    'capstone.x86',
    'capstone.x86_const',
    'capstone.xcore',
    'capstone.xcore_const',
    'codecs',
    'collections',
    'collections.abc',
    'compression',
    'compression.zstd',
    'concurrent',
    'concurrent.futures',
    'concurrent.futures.thread',
    'contextlib',
    'contextvars',
    'copy',
    'copyreg',
    'csv',
    'ctypes',
    'ctypes.util',
    'cython_runtime',
    'dataclasses',
    'datetime',
    'decimal',
    'difflib',
    'dis',
    'email',
    'email.base64mime',
    'email.charset',
    'email.encoders',
    'email.errors',
    'email.feedparser',
    'email.header',
    'email.iterators',
    'email.message',
    'email.parser',
    'email.quoprimime',
    'email.utils',
    'encodings',
    'encodings.aliases',
    'encodings.cp437',
    'encodings.latin_1',
    'encodings.utf_8',
    'encodings.utf_8_sig',
    'enum',
    'errno',
    'fcntl',
    'fnmatch',
    'fractions',
    'functools',
    'genericpath',
    'gettext',
    'glob',
    'grp',
    'gzip',
    'hashlib',
    'heapq',
    'hmac',
    'http',
    'http.client',
    'importlib',
    'importlib.machinery',
    'importlib.readers',
    'importlib.resources',
    'importlib.resources.abc',
    'importlib.resources.readers',
    'importlib.util',
    'inspect',
    'io',
    'ipaddress',
    'itertools',
    'json',
    'json.decoder',
    'json.encoder',
    'json.scanner',
    'keyword',
    'linecache',
    'locale',
    'logging',
    'lzma',
    'marshal',
    'math',
    'mmap',
    'ntpath',
    'numbers',
    'numpy',
    'numpy.dtypes',
    'numpy.exceptions',
    'numpy.lib',
    'numpy.lib.array_utils',
    'numpy.lib.format',
    'numpy.lib.introspect',
    'numpy.lib.mixins',
    'numpy.lib.npyio',
    'numpy.lib.scimath',
    'numpy.lib.stride_tricks',
    'numpy.linalg',
    'numpy.matrixlib',
    'numpy.matrixlib.defmatrix',
    'numpy.random',
    'numpy.random.bit_generator',
    'numpy.random.mtrand',
    'numpy.version',
    'opcode',
    'operator',
    'os',
    'os.path',
    'pathlib',
    'pickle',
    'platform',
    'posix',
    'posixpath',
    'pwd',
    'queue',
    'quopri',
    'random',
    're',
    'reprlib',
    'secrets',
    'select',
    'selectors',
    'shlex',
    'shutil',
    'signal',
    'site',
    'socket',
    'ssl',
    'stat',
    'statistics',
    'string',
    'struct',
    'subprocess',
    'sys',
    'sysconfig',
    'tarfile',
    'tempfile',
    'textwrap',
    'threading',
    'time',
    'token',
    'tokenize',
    'traceback',
    'types',
    'typing',
    'urllib',
    'urllib.error',
    'urllib.parse',
    'urllib.request',
    'urllib.response',
    'warnings',
    'wave',
    'weakref',
    'zipfile',
    'zipimport',
    'zlib',
]
if __name__ == '__main__':
    for m in MODULES: importlib.import_module(m)
# imports explicites (analyse statique de PyInstaller) ; absents sur certains systemes : ignores
try:
    import PIL
except ImportError:
    pass
try:
    import PIL.ExifTags
except ImportError:
    pass
try:
    import PIL.GimpGradientFile
except ImportError:
    pass
try:
    import PIL.GimpPaletteFile
except ImportError:
    pass
try:
    import PIL.Image
except ImportError:
    pass
try:
    import PIL.ImageChops
except ImportError:
    pass
try:
    import PIL.ImageColor
except ImportError:
    pass
try:
    import PIL.ImageFile
except ImportError:
    pass
try:
    import PIL.ImageMode
except ImportError:
    pass
try:
    import PIL.ImagePalette
except ImportError:
    pass
try:
    import PIL.ImageSequence
except ImportError:
    pass
try:
    import PIL.PaletteFile
except ImportError:
    pass
try:
    import PIL.PngImagePlugin
except ImportError:
    pass
try:
    import PIL.TiffTags
except ImportError:
    pass
try:
    import __future__
except ImportError:
    pass
try:
    import _abc
except ImportError:
    pass
try:
    import _ast
except ImportError:
    pass
try:
    import _bisect
except ImportError:
    pass
try:
    import _blake2
except ImportError:
    pass
try:
    import _bz2
except ImportError:
    pass
try:
    import _codecs
except ImportError:
    pass
try:
    import _collections
except ImportError:
    pass
try:
    import _collections_abc
except ImportError:
    pass
try:
    import _colorize
except ImportError:
    pass
try:
    import _compat_pickle
except ImportError:
    pass
try:
    import _contextvars
except ImportError:
    pass
try:
    import _csv
except ImportError:
    pass
try:
    import _ctypes
except ImportError:
    pass
try:
    import _cython_3_3_0
except ImportError:
    pass
try:
    import _datetime
except ImportError:
    pass
try:
    import _decimal
except ImportError:
    pass
try:
    import _functools
except ImportError:
    pass
try:
    import _hashlib
except ImportError:
    pass
try:
    import _heapq
except ImportError:
    pass
try:
    import _hmac
except ImportError:
    pass
try:
    import _imp
except ImportError:
    pass
try:
    import _interpreters
except ImportError:
    pass
try:
    import _io
except ImportError:
    pass
try:
    import _json
except ImportError:
    pass
try:
    import _locale
except ImportError:
    pass
try:
    import _lzma
except ImportError:
    pass
try:
    import _opcode
except ImportError:
    pass
try:
    import _opcode_metadata
except ImportError:
    pass
try:
    import _operator
except ImportError:
    pass
try:
    import _pickle
except ImportError:
    pass
try:
    import _posixsubprocess
except ImportError:
    pass
try:
    import _py_warnings
except ImportError:
    pass
try:
    import _queue
except ImportError:
    pass
try:
    import _random
except ImportError:
    pass
try:
    import _signal
except ImportError:
    pass
try:
    import _sitebuiltins
except ImportError:
    pass
try:
    import _socket
except ImportError:
    pass
try:
    import _sre
except ImportError:
    pass
try:
    import _ssl
except ImportError:
    pass
try:
    import _stat
except ImportError:
    pass
try:
    import _statistics
except ImportError:
    pass
try:
    import _string
except ImportError:
    pass
try:
    import _struct
except ImportError:
    pass
try:
    import _thread
except ImportError:
    pass
try:
    import _tokenize
except ImportError:
    pass
try:
    import _types
except ImportError:
    pass
try:
    import _typing
except ImportError:
    pass
try:
    import _warnings
except ImportError:
    pass
try:
    import _weakref
except ImportError:
    pass
try:
    import _weakrefset
except ImportError:
    pass
try:
    import _zstd
except ImportError:
    pass
try:
    import abc
except ImportError:
    pass
try:
    import annotationlib
except ImportError:
    pass
try:
    import argparse
except ImportError:
    pass
try:
    import array
except ImportError:
    pass
try:
    import ast
except ImportError:
    pass
try:
    import atexit
except ImportError:
    pass
try:
    import base64
except ImportError:
    pass
try:
    import binascii
except ImportError:
    pass
try:
    import bisect
except ImportError:
    pass
try:
    import builtins
except ImportError:
    pass
try:
    import bz2
except ImportError:
    pass
try:
    import capstone
except ImportError:
    pass
try:
    import capstone.arm
except ImportError:
    pass
try:
    import capstone.arm64
except ImportError:
    pass
try:
    import capstone.arm64_const
except ImportError:
    pass
try:
    import capstone.arm_const
except ImportError:
    pass
try:
    import capstone.bpf
except ImportError:
    pass
try:
    import capstone.bpf_const
except ImportError:
    pass
try:
    import capstone.evm
except ImportError:
    pass
try:
    import capstone.evm_const
except ImportError:
    pass
try:
    import capstone.m680x
except ImportError:
    pass
try:
    import capstone.m680x_const
except ImportError:
    pass
try:
    import capstone.m68k
except ImportError:
    pass
try:
    import capstone.m68k_const
except ImportError:
    pass
try:
    import capstone.mips
except ImportError:
    pass
try:
    import capstone.mips_const
except ImportError:
    pass
try:
    import capstone.mos65xx
except ImportError:
    pass
try:
    import capstone.mos65xx_const
except ImportError:
    pass
try:
    import capstone.ppc
except ImportError:
    pass
try:
    import capstone.ppc_const
except ImportError:
    pass
try:
    import capstone.riscv
except ImportError:
    pass
try:
    import capstone.riscv_const
except ImportError:
    pass
try:
    import capstone.sh
except ImportError:
    pass
try:
    import capstone.sh_const
except ImportError:
    pass
try:
    import capstone.sparc
except ImportError:
    pass
try:
    import capstone.sparc_const
except ImportError:
    pass
try:
    import capstone.systemz
except ImportError:
    pass
try:
    import capstone.sysz_const
except ImportError:
    pass
try:
    import capstone.tms320c64x
except ImportError:
    pass
try:
    import capstone.tms320c64x_const
except ImportError:
    pass
try:
    import capstone.tricore
except ImportError:
    pass
try:
    import capstone.tricore_const
except ImportError:
    pass
try:
    import capstone.wasm
except ImportError:
    pass
try:
    import capstone.wasm_const
except ImportError:
    pass
try:
    import capstone.x86
except ImportError:
    pass
try:
    import capstone.x86_const
except ImportError:
    pass
try:
    import capstone.xcore
except ImportError:
    pass
try:
    import capstone.xcore_const
except ImportError:
    pass
try:
    import codecs
except ImportError:
    pass
try:
    import collections
except ImportError:
    pass
try:
    import collections.abc
except ImportError:
    pass
try:
    import compression
except ImportError:
    pass
try:
    import compression.zstd
except ImportError:
    pass
try:
    import concurrent
except ImportError:
    pass
try:
    import concurrent.futures
except ImportError:
    pass
try:
    import concurrent.futures.thread
except ImportError:
    pass
try:
    import contextlib
except ImportError:
    pass
try:
    import contextvars
except ImportError:
    pass
try:
    import copy
except ImportError:
    pass
try:
    import copyreg
except ImportError:
    pass
try:
    import csv
except ImportError:
    pass
try:
    import ctypes
except ImportError:
    pass
try:
    import ctypes.util
except ImportError:
    pass
try:
    import cython_runtime
except ImportError:
    pass
try:
    import dataclasses
except ImportError:
    pass
try:
    import datetime
except ImportError:
    pass
try:
    import decimal
except ImportError:
    pass
try:
    import difflib
except ImportError:
    pass
try:
    import dis
except ImportError:
    pass
try:
    import email
except ImportError:
    pass
try:
    import email.base64mime
except ImportError:
    pass
try:
    import email.charset
except ImportError:
    pass
try:
    import email.encoders
except ImportError:
    pass
try:
    import email.errors
except ImportError:
    pass
try:
    import email.feedparser
except ImportError:
    pass
try:
    import email.header
except ImportError:
    pass
try:
    import email.iterators
except ImportError:
    pass
try:
    import email.message
except ImportError:
    pass
try:
    import email.parser
except ImportError:
    pass
try:
    import email.quoprimime
except ImportError:
    pass
try:
    import email.utils
except ImportError:
    pass
try:
    import encodings
except ImportError:
    pass
try:
    import encodings.aliases
except ImportError:
    pass
try:
    import encodings.cp437
except ImportError:
    pass
try:
    import encodings.latin_1
except ImportError:
    pass
try:
    import encodings.utf_8
except ImportError:
    pass
try:
    import encodings.utf_8_sig
except ImportError:
    pass
try:
    import enum
except ImportError:
    pass
try:
    import errno
except ImportError:
    pass
try:
    import fcntl
except ImportError:
    pass
try:
    import fnmatch
except ImportError:
    pass
try:
    import fractions
except ImportError:
    pass
try:
    import functools
except ImportError:
    pass
try:
    import genericpath
except ImportError:
    pass
try:
    import gettext
except ImportError:
    pass
try:
    import glob
except ImportError:
    pass
try:
    import grp
except ImportError:
    pass
try:
    import gzip
except ImportError:
    pass
try:
    import hashlib
except ImportError:
    pass
try:
    import heapq
except ImportError:
    pass
try:
    import hmac
except ImportError:
    pass
try:
    import http
except ImportError:
    pass
try:
    import http.client
except ImportError:
    pass
try:
    import importlib
except ImportError:
    pass
try:
    import importlib.machinery
except ImportError:
    pass
try:
    import importlib.readers
except ImportError:
    pass
try:
    import importlib.resources
except ImportError:
    pass
try:
    import importlib.resources.abc
except ImportError:
    pass
try:
    import importlib.resources.readers
except ImportError:
    pass
try:
    import importlib.util
except ImportError:
    pass
try:
    import inspect
except ImportError:
    pass
try:
    import io
except ImportError:
    pass
try:
    import ipaddress
except ImportError:
    pass
try:
    import itertools
except ImportError:
    pass
try:
    import json
except ImportError:
    pass
try:
    import json.decoder
except ImportError:
    pass
try:
    import json.encoder
except ImportError:
    pass
try:
    import json.scanner
except ImportError:
    pass
try:
    import keyword
except ImportError:
    pass
try:
    import linecache
except ImportError:
    pass
try:
    import locale
except ImportError:
    pass
try:
    import logging
except ImportError:
    pass
try:
    import lzma
except ImportError:
    pass
try:
    import marshal
except ImportError:
    pass
try:
    import math
except ImportError:
    pass
try:
    import mmap
except ImportError:
    pass
try:
    import ntpath
except ImportError:
    pass
try:
    import numbers
except ImportError:
    pass
try:
    import numpy
except ImportError:
    pass
try:
    import numpy.dtypes
except ImportError:
    pass
try:
    import numpy.exceptions
except ImportError:
    pass
try:
    import numpy.lib
except ImportError:
    pass
try:
    import numpy.lib.array_utils
except ImportError:
    pass
try:
    import numpy.lib.format
except ImportError:
    pass
try:
    import numpy.lib.introspect
except ImportError:
    pass
try:
    import numpy.lib.mixins
except ImportError:
    pass
try:
    import numpy.lib.npyio
except ImportError:
    pass
try:
    import numpy.lib.scimath
except ImportError:
    pass
try:
    import numpy.lib.stride_tricks
except ImportError:
    pass
try:
    import numpy.linalg
except ImportError:
    pass
try:
    import numpy.matrixlib
except ImportError:
    pass
try:
    import numpy.matrixlib.defmatrix
except ImportError:
    pass
try:
    import numpy.random
except ImportError:
    pass
try:
    import numpy.random.bit_generator
except ImportError:
    pass
try:
    import numpy.random.mtrand
except ImportError:
    pass
try:
    import numpy.version
except ImportError:
    pass
try:
    import opcode
except ImportError:
    pass
try:
    import operator
except ImportError:
    pass
try:
    import os
except ImportError:
    pass
try:
    import os.path
except ImportError:
    pass
try:
    import pathlib
except ImportError:
    pass
try:
    import pickle
except ImportError:
    pass
try:
    import platform
except ImportError:
    pass
try:
    import posix
except ImportError:
    pass
try:
    import posixpath
except ImportError:
    pass
try:
    import pwd
except ImportError:
    pass
try:
    import queue
except ImportError:
    pass
try:
    import quopri
except ImportError:
    pass
try:
    import random
except ImportError:
    pass
try:
    import re
except ImportError:
    pass
try:
    import reprlib
except ImportError:
    pass
try:
    import secrets
except ImportError:
    pass
try:
    import select
except ImportError:
    pass
try:
    import selectors
except ImportError:
    pass
try:
    import shlex
except ImportError:
    pass
try:
    import shutil
except ImportError:
    pass
try:
    import signal
except ImportError:
    pass
try:
    import site
except ImportError:
    pass
try:
    import socket
except ImportError:
    pass
try:
    import ssl
except ImportError:
    pass
try:
    import stat
except ImportError:
    pass
try:
    import statistics
except ImportError:
    pass
try:
    import string
except ImportError:
    pass
try:
    import struct
except ImportError:
    pass
try:
    import subprocess
except ImportError:
    pass
try:
    import sys
except ImportError:
    pass
try:
    import sysconfig
except ImportError:
    pass
try:
    import tarfile
except ImportError:
    pass
try:
    import tempfile
except ImportError:
    pass
try:
    import textwrap
except ImportError:
    pass
try:
    import threading
except ImportError:
    pass
try:
    import time
except ImportError:
    pass
try:
    import token
except ImportError:
    pass
try:
    import tokenize
except ImportError:
    pass
try:
    import traceback
except ImportError:
    pass
try:
    import types
except ImportError:
    pass
try:
    import typing
except ImportError:
    pass
try:
    import urllib
except ImportError:
    pass
try:
    import urllib.error
except ImportError:
    pass
try:
    import urllib.parse
except ImportError:
    pass
try:
    import urllib.request
except ImportError:
    pass
try:
    import urllib.response
except ImportError:
    pass
try:
    import warnings
except ImportError:
    pass
try:
    import wave
except ImportError:
    pass
try:
    import weakref
except ImportError:
    pass
try:
    import zipfile
except ImportError:
    pass
try:
    import zipimport
except ImportError:
    pass
try:
    import zlib
except ImportError:
    pass
