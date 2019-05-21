# Sync discuss calendars with google calendar

Provides a unidirectional sync from discuss calendars to an existing google calendar. It pulls all discuss events from an ics file and generates google events on a regular basis.

![calsync](https://user-images.githubusercontent.com/16271389/57576778-faf86580-741c-11e9-834c-4601681e24fc.gif)

NOTE: That setup with picking the calendar just happens once on app start. From there the program runs indefinitely continuously syncing every 5 minutes.

## Setup
These are the env vars that need to be set:

![setup_img](https://user-images.githubusercontent.com/16271389/57946127-6f555d80-7890-11e9-9d53-a495682feea7.png)

### Discuss credentials
DISCUSS_URL is the base url for your discuss (e.g. http://discuss.eastbayforeveryone.org)

DISCUSS_TOKEN is a personal auth token. This is pretty jank but the easiest way I could find to do this is to snatch the cookies from your activity on discuss. You're looking for the "_t" cookie

![discuss_creds](https://user-images.githubusercontent.com/16271389/57576587-e82f6200-7417-11e9-9164-25947e94bb72.png)

### Google API credentials
Follow step 1 from here: https://developers.google.com/calendar/quickstart/python#step_1_turn_on_the. You can grab a GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from there

### Redis
The heroku redis add-on automatically sets REDIS_URL. The other add-ons call the env var something else but I think it allows you to attach the add on with a custom env var name.

## Kicking off
The first time the program runs, it requires some configuration (auth with google + picking the calendar to sync to). The best way to do that is to run heroku run python import.py -a <app_name>.

It'll spit out an auth url. Navigate to it and go through the google auth flow. You'll need to paste the token the browser gives you back into the terminal.

From there, select the calendar you want to sync to and it will run an immediate sync. You can now kill this session. Scaling up the sync proc will take care of syncing indefinitely. Once you scale that up, you're done!


## Known Problems:

It does not handle updates to discuss events. If the time / description / title changes in discuss, it will create a brand new event on google cal but does not delete the previous one. In general it does not take any destructive actions on the google calendar it's syncing to.
