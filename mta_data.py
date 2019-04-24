import time
import urllib

from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict

class MTAData:

    def __init__(self, api_key, station_id, feed_ids, max_attempts):
        self.API_KEY = api_key
        self.STATION_ID = station_id
        self.FEED_IDS = feed_ids
        self.MAX_ATTEMPTS = max_attempts

    # Function connects to MTA feed and gets list of trains for the given station.
    def station_time_lookup(self, feed_id, station_id):
        global display_message

        for attempt in range((self.MAX_ATTEMPTS - 1)):
            try:
                # Get the MTA's data feed for a given set of lines. For more info,
                # see http://datamine.mta.info/list-of-feeds. The format of the feed
                # is "GTFS Realtime" (based on "protocol buffers") by Google.
                # Retrieval takes around 8-9 seconds on a RaspPi Zero
                transit_feed_pb = gtfs_realtime_pb2.FeedMessage()
                response = urllib.urlopen('http://datamine.mta.info/mta_esi.php?key={}&feed_id={}'
                    .format(self.API_KEY, feed_id))
                transit_feed_pb.ParseFromString(response.read())

                # Convert feed from Google's "protocol buffer" to a dictionary
                # and attempt to read FeedEntity message. Sometimes we have to
                # retry as a full dataset is not always provided by MTA. See:
                # https://developers.google.com/transit/gtfs-realtime/reference/
                # Conversion takes around 2-3 seconds on a RaspPi Zero
                transit_feed_dict = protobuf_to_dict(transit_feed_pb)
                train_data = transit_feed_dict['entity']
                break

            except Exception:
                if attempt <= self.MAX_ATTEMPTS:
                    display_message = (' ERROR getting data. Delaying for 30s. Attempt {} of {}.'
                        .format((attempt + 1), self.MAX_ATTEMPTS))
                    time.sleep(30)
                    continue
                else:
                    display_message = (' ERROR getting data. Max # of retries attempted.')
                    time.sleep(10)
                    raise

        # Loop through the data to get train times, and line info
        arrival_list = []
        for trains in train_data:
            train_trips = trains.get('trip_update', None)
            if train_trips and 'stop_time_update' in train_trips and 'trip' in train_trips:
                station_times = train_trips['stop_time_update']
                train_name = train_trips['trip']['route_id']

                # Filter out data not pertaining to the given station
                # (and direction) and get train arrivals, and train names
                for arrivals in station_times:
                    if arrivals.get('stop_id', False) == station_id:
                        train_time = arrivals['arrival']['time']
                        if train_time != None:
                            arrival_list.append([train_time,train_name])
                            #print ('debug2: ',train_time,train_name)

        # Return two-dimensional list: arrival time, train name
        return arrival_list

    def fetch_station_trains(self, exclude_past=True):
        # return a list of (train name, seconds until arrival) pairs for a given station, sorted based on arrival time
        station_trains = []
        for subway_feed_id in self.FEED_IDS:
            station_trains.extend(self.station_time_lookup(subway_feed_id, self.STATION_ID))
        station_trains.sort()

        if exclude_past:
            now = time.time()
            return filter(lambda x: x[0] > now, station_trains)

        return station_trains
