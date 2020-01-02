# TODO
# - demonize
# - logging
# - exceptions
# - multiple calendars and chats
# - pretty fomatting
# - new event updating and handling
# - upcoming events
# - push notifications

import sqlite3
import config
import httplib2
import datetime
import schedule
import time
import telebot

from oauth2client.service_account import ServiceAccountCredentials
from apiclient import discovery
from datetime import datetime as dt
from telebot import apihelper

onoma = 'mnemeky'

apihelper.proxy = {'https': 'socks5://localhost:9050'}
bot = telebot.TeleBot(config.tg_token)

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    config.client_secret_calendar, 'https://www.googleapis.com/auth/calendar.readonly')
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
con.row_factory = dict_factory
cur = con.cursor()
cur.execute("create table events_tab (id text, created timestamp, updated timestamp, start timestamp, end timestamp, summary text, description text, notified text)")

def modify_events():

    print(onoma + ': check for new events')
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    from_events_result = service.events().list(
        calendarId=config.gcalendar_id, timeMin=now, singleEvents=True,
        orderBy='startTime').execute()
    events = from_events_result.get('items', [])
    if not events:
        print(onoma + ': no upcoming events in calendar')
    else:
        for event in events:
            event_id = event['id']
            cur.execute("select id from events_tab where id=:event_id", {
                        "event_id": event_id})
            if not cur.fetchall():
                if "summary" not in event:
                    event_summary = 'No name'
                else:
                    event_summary = event['summary']
                if "description" not in event:
                    event_description = 'No description'
                else:
                    event_description = event['description']
                event_created = event['created']
                event_created = dt.fromisoformat(event_created.replace('Z', ''))
                event_created = event_created.strftime('%Y-%m-%d %H:%M:%S')
                event_updated = event['updated']
                event_updated = dt.fromisoformat(event_updated.replace('Z', ''))
                event_updated = event_updated.strftime('%Y-%m-%d %H:%M:%S')
                event_start = event['start']['dateTime']
                event_start = dt.fromisoformat(event_start.replace('Z', ''))
                event_start = event_start.strftime('%Y-%m-%d %H:%M:%S')
                event_end = event['end']['dateTime']
                event_end = dt.fromisoformat(event_end.replace('Z', ''))
                event_end = event_end.strftime('%Y-%m-%d %H:%M:%S')

                print(onoma + ': inserting new event ' + event['id'], event_created, event_updated, event_start, event_end, event_summary, event_description)
                cur.execute("insert into events_tab (id, created, updated, start, end, summary, description, notified) values (?, ?, ?, ?, ?, ?, ?, ?)", (
                    event['id'], event_created, event_updated, event_start, event_end, event_summary, event_description, 'no'))
                con.commit()
            else:
                print(onoma + ': event ' + event['id'] + ' already in database')

def today_events():
    print(onoma + ': check for today events')
    cur.execute(
        "select * from events_tab where datetime(start) >= date('now')")
    if not cur.fetchall():
        print(onoma + ': there is no events today(tonight)')
        bot.send_message(config.tg_chat_id, 'There is no events today(tonight)')
    else:
        cur.execute(
            "select * from events_tab where datetime(start) >= date('now')")
        today_events_dict = (cur.fetchall())
        msg = '<b>There is ' + str(len(today_events_dict)) + ' upcoming event(s) today(tonight):</b>\n\n'
        for event in today_events_dict:
            msg = msg+'%s\n%s\n%s\n\n'%(event['summary'], event['start'], event['description'])
        print(onoma + ': sending message\n' + msg)
        bot.send_message(config.tg_chat_id, msg, parse_mode='HTML')

def upcoming_events():
    print(onoma + ': check for upcoming events')
    cur.execute(
        "select * from events_tab where datetime(start) >= datetime('now', 'localtime', '-15 minutes') and notified = 'no'")
    if not cur.fetchall():
        print(onoma + ': there is no upcoming events')
    else:
        cur.execute(
            "select * from events_tab where datetime(start) >= datetime('now', 'localtime', '-15 minutes') and notified = 'no'")
        upcoming_events_dict = (cur.fetchall())
        msg = '<b>Event starting in 15 minutes:</b>\n\n'
        for event in upcoming_events_dict:
            msg = msg+'%s\n%s\n%s\n\n'%(event['summary'], event['start'], event['description'])
            cur.execute("update events_tab set notified = 'yes' where id=:event_id", {"event_id": event['id']})
            con.commit()
        print(onoma + ': sending message\n' + msg)
        bot.send_message(config.tg_chat_id, msg, parse_mode='HTML')

print(onoma + ': let me take the burden of routine reminders upon myself')
schedule.every(1).minute.do(modify_events)
schedule.every(1).minute.do(upcoming_events)
schedule.every().day.at("20:08").do(today_events)

while True:
    schedule.run_pending()
    time.sleep(1)