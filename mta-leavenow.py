#!/usr/bin/python
# =============================================================================

# Leave Now - Encouraging stress-free travel to your local MTA subway station
# by knowing when it's time to leave home.

# Version 1.5 22-Nov-2017 by Rob D <http://github.com/rob718/mta-leavenow>
# Based on a concept written by Anthony N <http://github.com/neoterix/nyc-mta-arrival-notify>

# == Change Log
# v1.5 22-Nov-2017: Bug fixes.
# v1.4 15-Nov-2017: General tweaks and code cleanup.
# v1.3 13-Nov-2017: Now ignoring trains that 'appear' to arrive in the past
# v1.2 12-Nov-2017: My room mate requested that we display train arrival times
#	instead of this program's original intent, where we tell you when it's
#	time to leave your home or office by factoring in the station travel
#	time. So here it is - uncomment either of the last two lines in this file
#	to switch program behaviour (the original, "leavenow" mode or the new
#	"traintime" mode). Also added error checking when getting the MTA feed.
#
# v1.1 04-Nov-2017: Added Scroll pHAT HD Support
# v1.0 29-Oct-2017: Initial version

# == Prerequisites
# Install Google's "gtfs-realtime-bindings" and Ben Hodgson's "protobuf-to-dict"
# libraries. Depending on your system, you can install them with something like:
#  pip install --upgrade gtfs-realtime-bindings
#  pip install --upgrade protobuf-to-dict

# == License
# This is free and unencumbered software released into the public domain.

# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.

# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# For more information, please refer to <http://unlicense.org>
# =============================================================================

import time
import threading

from mta_data import MTAData

# Enable support for third-party displays like the Pimoroni scroll pHAT HD
#import scrollphathd

data = MTAData(
# You'll need an API key. Get yours from http://datamine.mta.info/user
api_key = 'YOUR_KEY',

# Specifiy the subway station ID to use. For example 'R31N' for "Northbound
# Atlantic Av - Barclays Ctr"
station_id = 'R32N',

# Which subway feeds should we use for this subway station? MTA feeds are
# based on subway lines and some stations have multiple lines, therefore
# you may need to specify more than one. Comma seperate these. Of course
# it only makes sense to specify lines that pass through that station.
# For more info see http://datamine.mta.info/list-of-feeds
#subway_feed_ids = [16,21]
feed_ids = [16],

# In case we are unable to connect and/or process the feed, how many attemps
# before giving up (default is 30)
max_attempts = 30,
)

# How long does it take (in seconds) to walk to our subway station
TRAVEL_TIME = 170

# How long should we wait before attempting to refresh the feed (in seconds)?
# Feeds are generated every 30 seconds, so anything less wouldn't make sense.
#
# Note the size of each feed is going to be anything from 50 to 120 kiBs
# depending on the line. It doesn't sound much, but with a delay of 30 seconds,
# for two lines (feeds), expect to pull around 450 MiB in a 24 hour period!
#
# On a RaspPi Zero, expect a turn-around of retrieving and processing data
# to be around 12-15 seconds.
REFRESH_DELAY = 65


# Function to handle display -this will run continuously as a seperate thread
def scrolldisplay():
    text_to_display = None
    while True:
        if text_to_display != display_message:
            # message has changed, let's update display
            text_to_display = display_message
            print ('{} mta-leavenow:{}'
                .format(time.strftime('%b %d %H:%M:%S'),text_to_display) )

            # third-party display specific commands here
            #scrollphathd.clear()
            #scrollphathd.set_brightness(0.1)
            #scrollphathd.write_string(text_to_display)
        else:
            # no change, so continue to show original message

            # third-party display specific commands here
            #scrollphathd.show()
            #scrollphathd.scroll()

            time.sleep(0.02)

def format_trains_leave(next_trains):
    now = time.time()

    train_texts = []
    for (train_time, train_name) in next_trains[:2]:
        time_to_leave = int(round((train_time - now - TRAVEL_TIME)/60.0))
        if time_to_leave < 1:
            train_texts.append("NOW for (%s)" % train_name)
        else:
            train_texts.append("in %d' for (%s)" % (time_to_leave, train_name))

    return "     Leave %s" % ' or '.join(train_texts)

def format_trains_arrival(next_trains):
    now = time.time()

    train_texts = []
    for (train_time, train_name) in next_trains[:2]:
        train_texts.append("(%s) in %d'" % (train_name, int(round((train_time - now)/60.0))))
    return "     %s" % ' then '.join(train_texts)

def main(formatter):
    global display_message

    # start display in a seperate thread
    display_message = (' Getting train data...')
    display = threading.Thread(target=scrolldisplay)
    display.daemon = True
    display.start()

    # loop indefinitely, pausing for a set time
    while True:
        next_trains = data.fetch_station_trains()
        if not next_trains:
            display_message = ('     Cannot get train data or there are no trains.')

        display_message = formatter(next_trains)
        time.sleep(REFRESH_DELAY)

# Set formatter to format_trains_leave to let you know when it's time to leave your home/office)
# or to format_trains_arrival to simply displays the arrival times of the next two trains.
if __name__ == '__main__':
    main(formatter=format_trains_leave)
