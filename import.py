import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apscheduler.schedulers.background import BackgroundScheduler
from ics import Calendar
from pick import pick
import requests
import signal
import arrow

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
sched = BackgroundScheduler()


# This is copy/pasted from https://developers.google.com/calendar/quickstart/python#step_3_set_up_the_sample
def handle_google_auth():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


# Helpers
def fetch_discuss_calendar():
    url = os.environ['DISCUSS_URL']
    cookies = { "_t": os.environ['DISCUSS_TOKEN'] }
    resp = requests.get(url, cookies=cookies)
    return Calendar(resp.text)

def transform_to_google_event(discuss_event):
  return {
      'summary': discuss_event.name,
      'location': discuss_event.location,
      'description': discuss_event.description,
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
        gevent['description'], 
        gevent['start']['dateTime'], 
        gevent['end']['dateTime'],
    ])


calendarId = None
@sched.scheduled_job('cron', minute="*/5")
def sync_calendar():
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
        for e in service.events().list(calendarId=calendarId, timeMin=now,
                                       singleEvents=True).execute()['items']
    }

    # Diff the two to prevent creating dupe calendar events and add any new events found to gcal
    diff = set(events_from_discuss) - set(events_from_google)
    for k in diff:
        print("Adding calendar event")
        service.events().insert(calendarId=calendarId, body=events_from_discuss[k]).execute()


if __name__ == '__main__':
    # Auth with google and pick which google calendar to write to
    service = handle_google_auth()
    calendars = service.calendarList().list().execute()
    option, index = pick([c['summary'] for c in calendars['items']], 'Pick the correct calendar: ')
    calendarId = calendars['items'][index]['id']

    sched.start() 
    # Sleep indefinitely
    while True:
        signal.pause()
