#! /usr/bin/python
# -*- coding: utf-8 -*-

# Python ctypes bindings for VLC
#
# Copyright (C) 2009-2017 the VideoLAN team
# $Id: $
#
# Authors: Olivier Aubert <contact at olivieraubert.net>
#          Jean Brouwers <MrJean1 at gmail.com>
#          Geoff Salmon <geoff.salmon at gmail.com>
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2.1 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301 USA

"""This module provides bindings for the LibVLC public API, see
U{http://wiki.videolan.org/LibVLC}.

You can find the documentation and a README file with some examples
at U{https://www.olivieraubert.net/vlc/python-ctypes/}.

Basically, the most important class is L{Instance}, which is used
to create a libvlc instance.  From this instance, you then create
L{MediaPlayer} and L{MediaListPlayer} instances.

Alternatively, you may create instances of the L{MediaPlayer} and
L{MediaListPlayer} class directly and an instance of L{Instance}
will be implicitly created.  The latter can be obtained using the
C{get_instance} method of L{MediaPlayer} and L{MediaListPlayer}.
"""

import sys
import time
import json
import vlc


if __name__ == '__main__':
    # Requires:
    #  vlc.py [http source] [zone ID] [zone audio hw device]

    if len(sys.argv) >= 3:
        url = sys.argv[1]
        src = sys.argv[2]
    else:
        print('Error starting VLC component: missing URL or SRC parameter.')
        sys.exit(1)

    if len(sys.argv) >= 4:
        add_src = " --alsa-audio-device {}".format(sys.argv[3])
    else:
        add_src = ""

    instance = vlc.Instance(("--aout=alsa " + add_src).split())
    try:
        media = instance.media_new(url)
    except (AttributeError, NameError) as e:
        print('%s: %s (%s LibVLC %s)' % (e.__class__.__name__, e,
                                         sys.argv[0], vlc.libvlc_get_version()))
        sys.exit(1)
    player = instance.media_player_new()
    player.set_media(media)
    player.play()

    f = open('/home/pi/config/srcs/{}/currentSong'.format(src), "wt")
    f.write(json.dumps({"state": str(player.get_state())}))
    f.close()

    # Allow stream to start playing
    time.sleep(2)
    current_track = ''
    current_url = ''

    # Monitor track meta data and update currently_playing file if the track changed
    while True:
        try:
            if str(player.get_state()) == 'State.Playing':
                cur = str(media.get_meta(vlc.Meta.Artist)) + ' - ' + str(media.get_meta(vlc.Meta.Title))
                if (current_track != cur or current_url != vlc.bytes_to_str(media.get_mrl())):
                    # Update currently_playing file if the track has changed
                    current_track = cur
                    current_url = vlc.bytes_to_str(media.get_mrl())
                    print('Current track: %s - %s' % (media.get_meta(vlc.Meta.Artist), media.get_meta(vlc.Meta.Title)))

                    json_write = json.dumps({
                        "artist": media.get_meta(vlc.Meta.Artist),
                        "song": media.get_meta(vlc.Meta.Title),
                        "state": str(player.get_state())
                    })

                    try:
                        f = open('/home/pi/config/srcs/{}/currentSong'.format(src), "wt")
                        f.write(json_write)
                        f.close()
                    except Exception:
                        print('Error: %s' % sys.exc_info()[1])
            else:
                print('State: %s' % player.get_state())

        except Exception:
            print('Error: %s' % sys.exc_info()[1])

        time.sleep(1)
