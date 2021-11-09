#                             #
#           Imports           # 
#                             #

from kivy.lang import Builder
from plyer import gps
from kivy.app import App
from kivy.properties import StringProperty
from kivy.clock import mainthread
from itertools import cycle
from kivy.clock import Clock
from datetime import datetime
from dotenv import load_dotenv
import requests
import time
import googlemaps
import os

#loads environmental variables
load_dotenv('./.env')



#                        #
#           UI           # 
#                        #



kv = '''
BoxLayout:
    orientation: 'vertical'

    Label:
        text: app.gps_location

    Label:
        text: app.gps_status

    BoxLayout:
        size_hint_y: None
        height: '48dp'
        padding: '4dp'

        ToggleButton:
            text: 'Start' if self.state == 'normal' else 'Stop'
            on_state:
                app.start(1000, 0) if self.state == 'down' else \
                app.stop()
                            
'''



#                          #
#           Code           # 
#                          #



#creates class object for the app
class GpsTest(App):

    #creates StringProperty attributes
    gps_location = StringProperty()
    gps_status = StringProperty('Click Start to get GPS location updates')

    #codes for non-implemented error and configures the gps based on the Plyer Docs 
    def build(self):
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'
        



        return Builder.load_string(kv)



#                                      #
#           Fuction Obejects           # 
#                                      #



    # defines start function (is called in the kv code whenever 'Start' Button is clicked)
    def start(self, minTime, minDistance):
        self.gps_status = 'Started'
        gps.start(minTime, minDistance)
        Clock.schedule_once(self.ping_location, 0.1)
        Clock.schedule_interval(self.ping_location, 120)
    
    # defines status function (is called in kv code For label app.status)
    def status(self, dt):
        self.gps_status = 'Click Start to get GPS location updates'

    # defines stop function (is called in kv code whenever stop button is clicked)
    def stop(self):
        gps.stop()
        Clock.unschedule(self.ping_location)
        self.gps_location = ''
        self.gps_status = 'Stopped'
        Clock.schedule_once(self.status, 1)
        


#                             #
#           Threads           # 
#                             #



    @mainthread
    # calls on_location object and pass **kwargs as GPS Arguments including all GPS information
    def on_location(self, **kwargs):
        self.gps_location = '{lat}, {lon}'.format(**kwargs)
        # formats information from the **kwargs so that it only shows latitude and longitude

        return
    
    

    # defines function that is used to ping location and feed into gmap api (needed as output from gps was giving triple output)
    # instead of controlling the output of the gps, decided to control the output of the API
    def ping_location(self, dt):
        print(self.gps_location)
        # prints currently pinged location in console for testing
        

        #blank list for later handling of the JSON from the API
        words = []

        #for while loop
        running = True



#                              #
#           API Keys           # 
#                              #



        #API, AUTH keys as well as Destination (home address) and Discord Requests Server for pinging
        API = os.getenv('API')
        DEST = os.getenv('DEST')
        AUTH = os.getenv('AUTH')
        POST = os.getenv('POST')
        


#                                    #
#           Googlemaps API           # 
#                                    #



        gmaps = googlemaps.Client(key=f'{API}')

        #date and time needed for Gmaps
        now = datetime.now()

        #Access the api for direction (gives us dist and time of arrival)
        directions_result = gmaps.directions(origin=(self.gps_location),
                                            destination=f'{DEST}',
                                            mode="driving",
                                            departure_time=now)

        #converts the results into a string for later sifting
        directions_result = str(directions_result)

        


        # reads the words and splits them into different entries based on a " ' "
        # appends each subdivided entry to the list
        for word in directions_result.split("'"):
            words.append(word)

        #logic for finding the terms after the key words distance and duration
        cyclewords = cycle(words)
        nextword = next(cyclewords)

        #while loop to skip past the key words distance and duration and get the entry 4 steps ahead of the key words
        #A very crude way to look at a JSON file but I will update this in the future with an effective way of
        #looking at JSON
        #Basically converts the JSON to a str then divides the string based on a split of an apostrophe then adds that to an
        # empty list which is cycled through the cycle loop here
        while running:
            thisword, nextword = nextword, next(cyclewords)
            if nextword == "distance":
                for i in range(5):
                    if i != 4:
                        nextword = next(cyclewords)
                    else:
                        dis = nextword
            if nextword == "duration":
                for i in range(5):
                    if i != 4:
                        nextword = next(cyclewords)

                    else:
                        eta = nextword

        
                break #breaks the loop once the filter is finished

        
        #sends the discord message with the correct parameters    
        payload = {
            'content': f"Jorge Is currently around {dis} from his house. ETA {eta}"
        }

        header = {
            'authorization': AUTH
        }

        r = requests.post(POST, data=payload, headers=header)
        
        print(payload)
    
    
    # not sure what this does but left it in as part of the documentation
    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)
        
    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(1000, 0)
        pass
    


if __name__ == '__main__':
    GpsTest().run()