import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from google.auth.transport.requests import Request
from apscheduler.schedulers.background import BackgroundScheduler
from ics import Calendar
from pick import pick
import requests
import signal
import html
import arrow
from redis import Redis

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
sched = BackgroundScheduler()

redis = Redis.from_url(os.getenv('REDIS_URL') or 'redis://')

# This is copy/pasted from https://developers.google.com/calendar/quickstart/python#step_3_set_up_the_sample
def handle_google_auth():
    creds = None
    # we store the user's access and refresh tokens in redis and is added automatically 
    # when the authorization flow completes for the first time.
    token = redis.get(redis_key('token'))
    if token:
      creds = pickle.loads(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = OAuth2WebServerFlow(client_id=os.environ['GOOGLE_CLIENT_ID'],
                                       client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
                                       scope=SCOPES,
                                       redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_uri = flow.step1_get_authorize_url()
            print(auth_uri)
            code = input("code: ")
            creds = flow.step2_exchange(code)

        # Save the credentials for the next run
        pickled = pickle.dumps(creds)
        redis.set(redis_key('token'), pickled)

    return build('calendar', 'v3', credentials=creds)


def get_google_calendar_id():
    cal_id = redis.get(redis_key('calendar_id'))
    if cal_id:
      return cal_id.decode()
    calendars = service.calendarList().list().execute()
    option, index = pick([c['summary'] for c in calendars['items']], 'Pick the correct calendar: ')
    cal_id = calendars['items'][index]['id']
    redis.set(redis_key('calendar_id'), cal_id)
    return cal_id


# Helpers
def redis_key(suffix):
  return 'discuss_cal_sync:{}'.format(suffix)

def fetch_discuss_calendar():
    url = "{}/calendar.ics?time_zone=America/Los_Angeles".format(os.environ['DISCUSS_URL'])
    cookies = { "_t": os.environ['DISCUSS_TOKEN'] }
    resp = requests.get(url, cookies=cookies)
    return Calendar(resp.text)

def transform_to_google_event(discuss_event):
  return {
      'summary': html.unescape(discuss_event.name),
      'location': discuss_event.location,
      'description': html.unescape(discuss_event.description),
      'start': {
          'dateTime': discuss_event.begin.format(fmt="YYYY-MM-DDTHH:mm:ssZZ"),
          'timeZone': 'America/Los_Angeles',
      },
      'end': {
          'dateTime': discuss_event.end.format(fmt="YYYY-MM-DDTHH:mm:ssZZ"),
          'timeZone': 'America/Los_Angeles',
      },
  }

def dedupe_key(gevent):
    return "::".join([
        gevent['summary'],
        gevent.get('description', ''),
        gevent['start']['dateTime'], 
        gevent['end']['dateTime'],
    ])


@sched.scheduled_job('cron', minute="*/5")
def sync_calendar():
    print("Starting sync")
    calendarId = get_google_calendar_id()
    if calendarId == None:
        return

    service = handle_google_auth()

    # Fetch and normalize discuss events
    c = fetch_discuss_calendar()
    events_from_discuss = [transform_to_google_event(e) for e in c.events if e.begin > arrow.now()]
    events_from_discuss = { dedupe_key(e): e for e in events_from_discuss }

    # Fetch and normalize google events
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events_from_google = {
        dedupe_key(e): e
        for e in service.events().list(calendarId=calendarId, timeMin=now).execute()['items']
        if e['status'] == 'confirmed'
    }

    # Diff the two to prevent creating dupe calendar events and add any new events found to gcal
    diff = set(events_from_discuss) - set(events_from_google)
    print("Starting cal adds")
    for k in diff:
        print("Adding calendar event")
        print("Dry run for now")
        #service.events().insert(calendarId=calendarId, body=events_from_discuss[k]).execute()


if __name__ == '__main__':
    # Auth with google and pick which google calendar to write to
    service = handle_google_auth()

    # Force a fetch of the google calendar to trigger selection if needed
    get_google_calendar_id()

    # Kick off an immediate sync
    sync_calendar()

    # Start the cron
    sched.start() 

    # Sleep indefinitely
    while True:
        signal.pause()
