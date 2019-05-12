# Sync discuss calendars with google calendar

Provides a unidirectional sync from discuss calendars to an existing google calendar. It pulls all discuss events from an ics file and generates google events on a regular basis.

![calsync](https://user-images.githubusercontent.com/16271389/57576778-faf86580-741c-11e9-834c-4601681e24fc.gif)

## Setup

You will need google api credentials and discuss credentials.

### Google API credentials

Follow step 1 from here: https://developers.google.com/calendar/quickstart/python#step_1_turn_on_the. It tells you to download a `credentials.json` file. Make sure that file is in the same directory as `import.py`

### Discuss credentials

Discuss creds are set via environment variables. Specifically `DISCUSS_URL` and `DISCUSS_TOKEN`.

`DISCUSS_URL` is the base url for your discuss (e.g. `http://discuss.eastbayforeveryone.org`)

`DISCUSS_TOKEN` is a personal auth token. This is pretty jank but the easiest way I could find to do this is to snatch the cookies from your activity on discuss. You're looking for the "_t" cookie

![Screen Shot 2019-05-11 at 6 04 19 PM](https://user-images.githubusercontent.com/16271389/57576587-e82f6200-7417-11e9-9164-25947e94bb72.png)

Then just run

```
export DISCUSS_URL=<discuss url>
export DISCUSS_TOKEN=<discuss token>
```

### Running the program

I recommend installing dependencies and running within virtualenv. In which case follow these steps:

```
$ python3 -m venv venv
$ source venv/bin/activate
```

Whether you're in a virtualenv or not you can install dependencies via:

```
$ pip install -r requirements.txt
```

Once you've finished the setup, simply run `python import.py`. The first thing it'll do is prompt you to login to google calendar. On successful login it'll show you a list of all your calendars. Pick the one you want to sync discuss events to. From there the program will just run indefinitely syncing on a regular schedule (default every 5 minutes)

## Known Problems:

It does not handle updates to discuss events. If the time / description / title changes in discuss, it will create a brand new event on google cal but does not delete the previous one. In general it does not take any destructive actions on the google calendar it's syncing to.
