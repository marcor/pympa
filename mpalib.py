# -*- coding: ISO-8859-1 -*-

# maplib.py is part of Pympa.
# Copyright (C) 2006 by Marco Rimoldi
# Released under the GNU General Public License
# (See the included COPYING file)
#
# Pympa is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pympa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pympa; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, struct
from StringIO import StringIO

default_in_enc = "iso-8859-1"
default_out_enc = "iso-8859-1"

resv = 0
f = "free"

version = ["2.5", "reserved", "2", "1"]
layer = ["reserved", "III", "II", "I"]

bitrates = ( (f, 32, 64, 96, 128, 160, 192, 224,
                      256, 288, 320, 352, 384, 416, 448, resv),
             (f, 32, 48, 56, 64, 80, 96, 112, 128,
                      160, 192, 224, 256, 320, 384, resv),
             (f, 32, 40, 48, 56, 64, 80, 96, 112, 128,
                      160, 192, 224, 256, 320, resv),
             (f, 32, 48, 56, 64, 80, 96, 112, 128, 144,
                      160, 176, 192, 224, 256, resv),
             (f, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96,
                      112, 128, 144, 160, resv) )

btr_table = ( ((resv,)*16,)*4,                                        # reserved
              (bitrates[4], (resv,)*16, bitrates[4], bitrates[2]),    # III
              (bitrates[4], (resv,)*16, bitrates[4], bitrates[1]),    # II
              (bitrates[3], (resv,)*16, bitrates[3], bitrates[0]) )   # I

sample_rates = ( (11025, 12000, 8000, resv),    # 2.5
                 (resv,) * 4,                   # reserved
                 (22050, 24000, 16000, resv),   # 2
                 (44100, 48000, 32000, resv) )  # 1

samples = ( (resv, 576, 1152, 384),    # 2.5
            (resv,) * 4,               # reserved
            (resv, 576, 1152, 384),    # 2
            (resv, 1152, 1152, 384) )  # 1

xing_offset = ( (17, 32), # stereo
                (17, 32), # joint s.
                (17, 32), # dual s.
                (9, 17) ) # mono

padding = (0, 1, 1, 4)

channel_modes = ("stereo", "joint stereo", "dual stereo", "mono")

emphasis = ("none", "50/15 ms", "reserved", "CCIT J. 17")

genres = ["Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk",
          "Grunge", "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies",
          "Other", "Pop", "R&B", "Rap", "Reggae", "Rock", "Techno",
          "Industrial", "Alternative", "Ska", "Death Metal", "Pranks",
          "Soundtrack", "Euro-Techno", "Ambient", "Trip-Hop", "Vocal",
          "Jazz+Funk", "Fusion", "Trance", "Classical", "Instrumental",
          "Acid", "House", "Game", "Sound Clip", "Gospel", "Noise",
          "AlternRock", "Bass", "Soul", "Punk", "Space", "Meditative",
          "Instrumental Pop", "Instrumental Rock", "Ethnic", "Gothic",
          "Darkwave", "Techno-Industrial", "Electronic", "Pop-Folk",
          "Eurodance", "Dream", "Southern Rock", "Comedy", "Cult", "Gangsta",
          "Top 40", "Christian Rap", "Pop/Funk", "Jungle", "Native American",
          "Cabaret", "New Wave", "Psychedelic", "Rave", "Showtunes",
          "Trailer", "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz", "Polka",
          "Retro", "Musical", "Rock & Roll", "Hard Rock", "Folk",
          "Folk-Rock", "National Folk", "Swing", "Fast Fusion", "Bebop",
          "Latin", "Revival", "Celtic", "Bluegrass", "Avantgarde",
          "Gothic Rock", "Progressive Rock", "Psychedelic Rock",
          "Symphonic Rock", "Slow Rock", "Big Band", "Chorus",
          "Easy Listening", "Acoustic", "Humour", "Speech", "Chanson",
          "Opera", "Chamber Music", "Sonata", "Symphony", "Booty Brass",
          "Primus", "Porn Groove", "Satire", "Slow Jam", "Club", "Tango",
          "Samba", "Folklore", "Ballad", "Power Ballad", "Rhytmic Soul",
          "Freestyle", "Duet", "Punk Rock", "Drum Solo", "A Cappella",
          "Euro-House", "Dance Hall", ""]


##--------------------------------------------------------------- FUNCTIONS

def file_from(object, mode="rb"):
  """If it is a file-like object, returns 'object' itself. Otherwise
tries to open a file with the given 'mode' using 'object' as the file
path."""
  if hasattr(object, "seek"):
    return object
  else:
    return open(object, mode)

def str_to_seconds(time):
  """Converts a time string to the equivalent number of seconds
in floating point precision."""
  secs = 0
  try:
    pieces = time.split(":")
    for i in range(len(pieces)):
      secs += float(pieces[-(i+1)]) * (60 ** i)
  except:
    raise ValueError, "'%s' does not represent a valid time length" % time
  return secs

def seconds_to_str(time):
  pieces = []
  secs = "%05.2f" % (time % 60)
  mins = "%02d" % ((time / 60) % 60)
  return mins + ":" + secs

def update_xing(stream):
  """Rebuild the existing VBR Xing header found in 'stream'. NOTE:
'stream' must be an instance of the MpegAudioStream class."""
  if not isinstance(stream, MpegAudioStream):
    raise TypeError, "can only update mpeg stream objects"
  if not stream.vbr: return
  frames = []
  toc = []
  bitrate_sum = 0
  for frame in stream:
    frames.append(frame)
    bitrate_sum += frame.bitrate
  frames_per_sector = len(frames) / float(100)
  for i in map(lambda n: int(frames_per_sector * n), range(100)):
    toc.append(frames[i].begins / float(stream.stream_size) * 256)
  stream.length = len(frames) * stream.frame_length
  avg_bitrate = float(bitrate_sum) / len(frames)
  stream.seek(stream.xing_header.offset + 8)
  stream.write(struct.pack(">LLL100B", 7, len(frames), stream.stream_size, *toc))

##----------------------------------------------------------------- CLASSES

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Byte:
  """Implements a sliceable byte object.
Initialize it using a byte value (i.e. a single character string, as
obtained by calling read(1) on an open file, or converting a 0-255
integer value using the built-in function 'chr').
Use the resulting object as a function, passing it a bit mask (i.e. a
string made up of (at most) eight 1's and 0's). Return value: the
bit-wise AND of byte and mask, RIGHT SHIFTED according to the number of
zeros on the right side of mask.
Example:

extract = Byte(chr(57))  # 57 is decimal for 111001

extract('1000')          # (57 & 8) >> 3
extract('0100')          # (57 & 4) >> 2
extract('011010')        # (57 & 26) >> 1"""

  def __init__(self, char):
    self.byte = char

  def __call__(self, mask):
    tmp = list(mask)[::-1]
    rshift = tmp.index("1")
    mask = mask[:-rshift] or mask
    return (self.byte >> rshift) & int(mask, 2)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Id3Tag1(dict):
  """Implementation of the Id3 Tag v.1.1. You can initialize new
objects in two ways. If you assign a readable file-like object or
a file path to the 'source' parameter, __init__ will search this
resource for valid Id3 tag information and populate the new object with
it. In addition to that, you can also specify field values manually
using keywords (for example "title = 'my title'"). If you specify
both 'source' and keyword arguments, these will take precedence in
case of conflict.

The returned object acts like a dictionary whose keys are the field
names used in Id3 tags: title, artist, album, year, comment, track,
genre. You can manually change a field value at any time, but you must
provide new values as either standard or unicode strings (an exception
will be raised otherwise). If you need to set the genre field, pass
a string containing the chosen genre index (i.e. "5" for "Funk").

Internally, all values will be stored as unicode strings. On this respect
'input_encoding' and 'output_encoding' define which character encoding
should be used for respectively reading strings (i.e. converting a byte
sequence to an unicode string) and writing them to file or stream (i.e.
reducing an unicode string to a byte sequence). Note that any field value
manually provided at init time (or as a parameter to the __setitem__ and
update methods) which is not expressed as an unicode string will be
decoded using 'input_encoding' before being stored. Likewise, encoding
using 'output_encoding' will happen at each call to the __getitem__ and
save_to_file methods.

'input_encoding' defaults to 'iso-8859-1'. 'output_encoding' defaults
to the same value as that of 'input_encoding'.
To convert a file Id3 tag from one encoding to another (provided that
they are compatible with each other, at least in this specific case)
just do this:

  id3 = Id3Tag1("myfile.mp3", input_encoding="original_encoding",
                              output_encoding="new_encoding")
  id3.save_to_file("myfile.mp3")"""

  fields = ("title", "artist", "album", "year", "comment", "track", "genre")
  default = dict.fromkeys(fields, "")
  max_len = dict(zip(fields, (30, 30, 30, 4, 30, 2, 3)))
  def __init__(self, source=None, input_encoding=default_in_enc,
                                output_encoding=None,
                                errors="strict", **kwargs):
    dict.__init__(self)
    self.input_enc = input_encoding
    self.output_enc = output_encoding or input_encoding
    self.errmode = errors
    self.update(self.default)
    if source:
      fromsource = self.parse(source)
      self.update(fromsource, **kwargs)

  def parse(self, source):
    openfile = file_from(source)
    fields = {}
    if self.__has_id3(openfile):
        pad_chars = " \x00" # winamp using 32?
        extract = lambda name: fields.__setitem__(name, openfile.read(self.max_len[name]).rstrip(pad_chars))
        extract("title")
        extract("artist")
        extract("album")
        extract("year")
        comment = openfile.read(30)
        if comment[-2] == "\x00":
            fields["track"] = str(ord(comment[-1]) or "")
            comment = comment[:-2]
        fields["comment"] = comment.rstrip(pad_chars)
        genre = ord(openfile.read(1))
        if genre in range(len(genres)):
            fields["genre"] = str(genre)
    return fields

  def __setitem__(self, name, value):
    if name not in self.fields:
        raise KeyError, name
    kind = type(value)
    if kind in (str, unicode):
        value = value[:self.max_len[name]]
        if kind == str:
              value = value.decode(self.input_enc)
    else:
        raise TypeError, "string expected, got %s instead" % type(value)
    dict.__setitem__(self, name, value)

  def  __getitem__(self, name):
    value = dict.__getitem__(self, name)
    return value.encode(self.output_enc, self.errmode)

  def update(self, mapping={}, **kwargs): # the original update method bypasses __setitem__
    '''Examples:
id3.update({"title": "I am the Walrus",
            "artist": "The Beatles"})
id3.update( (("year", "1968"),
            ("album", "Magical Mystery Tour")) )
id3.update(comment="recorded in Abbey Road, London")'''

    if isinstance(mapping, dict):
        for key in mapping:
            self[key] = mapping[key]
    elif type(mapping) in (list, tuple):
        for key, value in mapping:
              self[key] = value
    else:
        raise TypeError, "expected a mapping object, got %s instead" % type(mapping)

    for key in kwargs:
        self[key] = kwargs[key]

  def __has_id3(self, audiofile):
    try:
        audiofile.seek(-128, 2)
    except IOError:
        return False
    if audiofile.read(3) == "TAG":
        return True
    return False

  def save_to_file(self, dest):
    openfile = file_from(dest, "ab+")
    if not self.__has_id3(openfile):
        openfile.seek(0, 2)
    else:
        openfile.seek(-128, 2)
        openfile.truncate()

    format = lambda name: self[name].ljust(self.max_len[name], "\x00")

    openfile.write("TAG".encode(self.output_enc))
    openfile.write(format("title"))
    openfile.write(format("artist"))
    openfile.write(format("album"))
    openfile.write(format("year"))
    if self["track"]:
        openfile.write(self["comment"][:28].ljust(29, "\x00"))
        openfile.write(chr(int(self["track"])))
    else:
        openfile.write(format("comment"))
    if self["genre"]:
        openfile.write(chr(int(self["genre"]) % 256))
    else:
        openfile.write(chr(255))
    openfile.flush()

  def __nonzero__(self):
    for field in self.fields:
      if self[field]:
        return True
    return False


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class FrameHeader:
  """A class for representing Mpeg audio frame headers."""

  def __init__(self, mpa, start):
    self.begins = start
    mpa.seek(start)
    if not mpa.is_sync():
      raise ValueError, "no frame starting at byte %d" % start

    mpa.read(1)
    bits = Byte(mpa.read_byte())
    self.version = bits("11000")
    self.layer   = bits("00110")
    self.crc_on  = not bits("00001")
    bits = Byte(mpa.read_byte())
    self.bitrate_code = bits("11110000")
    self.smprate_code = bits("00001100")
    self.padding = bits("10") and padding[self.layer]
    self.private = bits("01")
    bits = Byte(mpa.read_byte())
    self.ch_mode =  bits("11000000")
    self.mode_ext = bits("00110000")
    self.copyright = bits("1000")
    self.original =  bits("0100")
    self.emphasis =  bits("0011")

    self.validate_against(mpa)

    if self.valid:
      self.bitrate = btr_table[self.layer][self.version][self.bitrate_code]
      self.smprate = sample_rates[self.version][self.smprate_code]
      self.size = mpa.get_frame_size(self)

  def validate_against(self, mpa):
    self.valid = True
    check_table = mpa.check_table
    if (self.bitrate_code in (0, 15) or
        self.smprate_code == 3):
      self.valid = False
      return
    for key in check_table:
      if getattr(self, key) != check_table[key]:
        self.valid = False
        return

  def info(self):
    return "\n".join(( \
    "\nMPEG %s (layer %s) frame information:" % (version[self.version],
                                                 layer[self.layer]),
    "start position: %d" % self.begins,
    "frame size: %d" % self.size,
    "bitrate: %s Kbs" % str(self.bitrate),
    "sampling rate: %s Hz" % self.smprate,
    "padding: %s" % str(self.padding or "none"),
    "private bit set: %s" % (self.private and "yes" or "no"),
    "channel mode: %s" % channel_modes[self.ch_mode],
    "mode extension code: %d" % self.mode_ext,
    "copyrighted: %s" % (self.copyright and "yes" or "no"),
    "original: %s" % (self.original and "yes" or "no"),
    "emphasis: %s\n" % emphasis[self.emphasis] ))

  def __repr__(self):
    return self.info()



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class XingInfoHeader(object):
  """A class for representing Xing/Info headers (no support for
VBRI tags)."""

  types = ("Xing", "Info")

  def __init__(self, mpa, force=False):
    restore = mpa.tell()
    self.offset = xing_offset[mpa.version & 1][mpa.ch_mode]
    self.start = mpa.stream_start + 4 + self.offset
    mpa.seek(self.start)
    tag = mpa.read(4)
    self.tag = (tag in self.types) and tag or None
    if self.tag:
      mpa.seek(3, 1)
      self.fields = []
      flags = mpa.read_byte()

      if flags & 1:                                                   # frames
        self.fields.append("frames")
        self.frames = self.__get_field(mpa)

      if flags & 2:                                                   # bytes
        self.fields.append("bytes")
        self.bytes = self.__get_field(mpa)

      if flags & 4:                                                   # toc
        self.fields.append("toc")
        self.toc = []
        for i in range(100):
          self.toc.append(mpa.read_byte())

      if flags & 8:                                                   # quality
        self.fields.append("quality")
        self.quality = self.__get_field(mpa)

      self.end = mpa.tell()
      self.container = mpa.read_header(mpa.stream_start)
    elif force in self.types:
      pass

    mpa.seek(restore)

  def __get_field(self, mpa):
    val = 0
    for i in range(4):
      val <<= 8
      val += mpa.read_byte()
    return val

  def __str__(self):
    if self.tag:
        output = ("Type: \"%s\"\nHeader found at byte %d\n" % (self.tag, self.start))
    else:
        return "Not found."
    toc = "toc" in self.fields
    for field in [key for key in self.fields if key != "toc"]:
        output += "%s: %s\n" % (field.capitalize(), getattr(self, field))
    output += "Table of contents%savailable" % (toc and " " or " not ")
    return output

  def __repr__(self):
    if self:
      return object.__repr__(self)
    else:
      return 'None'

  def __nonzero__(self):
    return bool(self.tag)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class MpegAudio:
  """This is a base class used to represent Mpeg audio data.
You CAN'T instantiate this class directly: you should use the
provided wrapper classes MpegAudioFile or MpegAudioStream instead.
Choose the first one if you need to initialize your MpegAudio object
with a file (insert the file path as the first argument); the second
one in case your Mpeg data is stored in a memory buffer (insert the
relative StringIO instance as the first argument).
At init time you may specify some optional parameters:
- the 'accuracy' level: an integer between 1 and 3 that defines the
  'strictness' used to check for a frame's header validity (i.e. is it
  to be considered an actual header or a 'false positive'?); the greater
  the value, the wider the set of header fields that the parser will
  compare in search of possible inconsistencies:
  (default) 1 = [version, layer, bitrate (only cbr)]
            2 = 1 + [sample rate, channel mode]
            3 = 2 + [crc, original and copyrighted flags]
- an input and output encoding to be passed as parameters to the
  Id3Tag1 class __init__ method (see the relative documentation for
  reasons why you may want to override the default values)."""

  def __init__(self, accuracy=1, input_encoding=default_in_enc,
                                 output_encoding=default_out_enc):

    if accuracy not in (1, 2, 3):
      raise ValueError, "the accuracy parameter must be an integer in the range 1-3"
    self.id3 = Id3Tag1(self.filepath, input_encoding, output_encoding or None)

    if self.id3:
      self.seek(-128, 2)
    else:
      self.seek(0, 2)
    self.stream_end = self.tell()
    self.seek(0)

    self.check_table = {}
    check_fields = ["version", "layer", "bitrate_code"]
    if accuracy > 1:
      check_fields += ["smprate_code", "ch_mode"]
      if accuracy > 2:
        check_fields += ["crc_on", "original", "copyright"]

    try:
      self.first_frame = self.next()                                                                  # this saves the first frame header in self.cur_frame
    except:
      raise IOError, "this source contains no valid mpeg audio data"

    self.stream_start = self.cur_frame.begins
    self.stream_size = self.stream_end - self.stream_start

    for i in ("version", "layer", "smprate_code", "ch_mode", "bitrate_code",
              "bitrate", "original", "copyright", "crc_on", "smprate", "emphasis"):
      setattr(self, i, getattr(self.cur_frame, i))

    self.get_info_header()                                                       # look for xing or info header

    if self.vbr:
      self.length = self.xing_header.frames \
                    * samples[self.version][self.layer] / float(self.smprate)
      self.bitrate = int(self.xing_header.bytes * 8 \
                     / float(self.length) / 1000)
      self.cur_frame.size = self.tell() - self.stream_start                             # may not be necessary
      check_fields.remove("bitrate_code")
      self.get_frame_size = self._get_vbr_frame_size
    else:
      self.length = self.stream_size * 8 / float(self.bitrate) / 1000
      self.frame_size = int(self.frame_constant * self.bitrate)
      self.get_frame_size = self._get_cbr_frame_size

    self.check_table = dict(zip(check_fields,
                       [getattr(self, field) for field in check_fields]))

  def _synchronize(self):
    while self.tell() < self.stream_end:
      if self.is_sync(): return

  def _get_vbr_frame_size(self, frame):
    return int(self.frame_constant * frame.bitrate + frame.padding)

  def _get_cbr_frame_size(self, frame):
    return int(self.frame_size + frame.padding)

  def __iter__(self):
    self.seek(0)
    self._synchronize()
    return self

  def get_frame_size(self, frm):
    length = samples[frm.version][frm.layer] / float(frm.smprate)
    constant = length * 1000 / 8
    self.frame_constant = constant
    self.frame_length = length
    return int(constant * frm.bitrate) + frm.padding

  def update_id3(self, mapping={}, **kwargs):
    """Updates the file Id3 Tag information."""

    self.id3.update(mapping, **kwargs)
    self.id3.save_to_file(self.filepath)

  def read_byte(self):
    try:
      return ord(self.read(1))
    except TypeError: # EOF
      return None

  def get_info_header(self):
    hdr = XingInfoHeader(self)
    self.xing_header = hdr
    self.vbr = hdr.tag == "Xing"

  def is_sync(self):
    byte = self.read_byte()
    if byte == 255:                      # 8 bits are on...
      byte = self.read_byte()
      if  byte >= 224:                   # ...and so are the next three
          self.seek(-2, 1)               # back to the header start
          return True
    return False                         # on we go, ready to scan another one

  def read_header(self, pos, max_offset=4):
    try:
      hdr = FrameHeader(self, pos)
      if hdr.valid: return hdr
    except:
      for offset in range(1, max_offset + 1):
        for direction in ("back", "forth"):
          try: # this catches illegal negative targets as well
            hdr = FrameHeader(self, pos - offset)
            if hdr.valid: return hdr
          except:
            offset = -offset
    self.seek(pos + max_offset + 1) # get ready to seek for other sync bytes
    return None

  def next(self):
    pos = self.tell()
    while pos < self.stream_end:
      hdr = self.read_header(pos)
      if not hdr:  # no (valid) header found
        self._synchronize()
        pos = self.tell()
      else:
        self.seek(pos + hdr.size)
        if self.tell() > (self.stream_end + 1):
          hdr.size = self.stream_end - hdr.begins
        self.cur_frame = hdr
        return hdr
    raise StopIteration

  def stats(self):
    restore = self.tell()
    current = self.cur_frame
    report = """Valid frames: %(frames)d"""
    n = 0
    for i in self:
      n += 1
    print report % dict(frames = n)
    self.cur_frame = current
    self.seek(restore)

  def seek_time(self, time=0):
    arg_type = type(time)
    if arg_type in (float, int):
      secs = float(time)
    elif arg_type == str:
      secs = str_to_seconds(time)
    if self.length < secs:
      raise ValueError, "target exceeds total playing time!"
    oldpos = self.tell()
    try:
      if not self.vbr:
        bytes = self.stream_start + int(secs * self.stream_size / self.length)
        self.seek(bytes)
        self.next()
      else:
        round_float = lambda f: int("%.0f" % f) # converts floats like 2.9999999999996 to ints
        sector_length = self.length / 100
        sector = int(secs / sector_length)
        offset_frames = round_float((secs % sector_length) / self.frame_length)
        sector_start = self.stream_start + int(self.xing_header.toc[sector] * self.stream_size / 256)
        self.seek(sector_start)
        for frame in range(offset_frames):
          self.next()
    except StopIteration:
        raise ValueError, "no headers found after this point"
        self.seek(oldpos)
    return self.cur_frame

  def split(self, cutpoints, titles, targetdir="split", bufsize=2048):
    if (type(cutpoints) != list) or (type(titles) != list):
      raise TypeError, "both 'cutpoints' and 'titles' must be lists"
    if not os.path.exists(targetdir):
      os.mkdir(targetdir)
    cutpoints = [self.seek_time(time).begins for time in cutpoints] + [self.stream_end]
    self.seek(self.stream_start)
    if self.vbr:
      xing_frame = self.read(self.first_frame.size)
      self.next() # leave the xing frame out
    else:
      xing_frame = ""
    for end in cutpoints:
      self.next()
      begin = self.cur_frame.begins
      self.seek(begin)
      data = self.read(end - begin)
      track = MpegAudioStream(xing_frame + data)
      track_number = cutpoints.index(end)
      fname = "%02d - %s.mp%d" % (track_number + 1, titles[track_number] or "Untitled", 4 - self.layer)
      update_xing(track)
      track.update_id3(self.id3, title=titles[track_number], track=str(track_number + 1))
      output = open(targetdir + os.sep + fname, "wb")
      track.seek(0)
      output.write(track.read())
      output.close()

  def __str__(self):
    info = """Mpeg %s layer %s

Stream size: %d bytes (%d KB)
Estimated length: %d secs
First header found at byte %d
Bitrate: %d,000 bits/sec (%s)
Sampling frequency: %d Hz
Channel mode: %s
CRCs: %s
Original: %s
Copyrighted: %s
Emphasis: %s""" % (version[self.version],
                   layer[self.layer],
                   self.stream_size,
                   self.stream_size / 1024,
                   self.length,
                   self.stream_start,
                   self.bitrate,
                   self.vbr and "VBR" or "CBR",
                   self.smprate,
                   channel_modes[self.ch_mode],
                   self.crc_on and "yes" or "no",
                   self.original and "yes" or "no",
                   self.copyright and "yes" or "no",
                   emphasis[self.emphasis])
    return info

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class MpegAudioFile(MpegAudio, file):
  """Wrapper of the MpegAudio class. 'filename' must be an existing
Mpeg audio file path. See the MpegAudio documentation for details
about optional arguments."""

  def __init__(self, filename, **kwds):
    file.__init__(self, filename, "rb")
    self.filepath = os.path.abspath(filename)
    MpegAudio.__init__(self, **kwds)

  def __repr__(self):
    return "<open MPEG%s audio file '%s', mode '%s' at 0x%08X>" % (version[self.version],
                                                                self.filepath,
                                                                self.mode,
                                                                id(self))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class MpegAudioStream(MpegAudio, StringIO):
  """Wrapper of the MpegAudio class. 'stream' must be a StreamIO or
a str object, containing valid Mpeg audio data. See the MpegAudio
documentation for details about optional arguments."""

  def __init__(self, stream, **kwds):
    if type(stream) == str:
      data = stream
    else:
      data = stream.getvalue()
    self.filepath = self
    StringIO.__init__(self, data)
    MpegAudio.__init__(self, **kwds)

  def __repr__(self):
    return "<open MPEG%s audio stream at 0x%08X>" % (version[self.version],
                                                         id(self))
