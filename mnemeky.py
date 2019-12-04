# TODO
# - demonize
# - logging
# - exceptions
# - multiple calendars and chats
# - pretty fomatting
# - new event updating and handling
# - upcoming events

from __future__ import print_function
import httplib2

import datetime
import time
import config
import telebot
import schedule

from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
from telebot import apihelper

apihelper.proxy = {'https': 'socks5://localhost:9050'}

def job():
    print("I'm working...")
    bot = telebot.TeleBot(config.tg_token)

    def main():
        credentials = ServiceAccountCredentials.from_json_keyfile_name(config.client_secret_calendar, 'https://www.googleapis.com/auth/calendar.readonly')
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        now_1day = round(time.time())+86400
        now_1day = datetime.datetime.fromtimestamp(now_1day).isoformat() + 'Z'

        eventsResult = service.events().list(
            calendarId=config.gcalendar_id, timeMin=now, timeMax=now_1day, maxResults=100, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            print('There are no events today')
            bot.send_message(config.tg_chat_id, 'There are no events today')
        else:
            msg = '<b>There is event today</b>\n'
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if "summary" not in event:
                    ev_title = 'No name'
                    print(ev_title)
                else:
                    print(start,' ', event['summary'])
                    ev_title = event['summary']
                if "description" not in event:
                    ev_desc = 'No description'
                    print(ev_desc)
                else:
                    print(event['description'])
                    ev_desc = event['description']

                
                cal_link = '<a href="/%s">More...</a>'%event['htmlLink']
                ev_start = event['start'].get('dateTime')
                print (cal_link)
                msg = msg+'%s\n%s\n%s\n%s\n\n'%(ev_title, ev_start, ev_desc, cal_link)
                print('===================================================================')
            bot.send_message(config.tg_chat_id, msg, parse_mode='HTML')

    if __name__ == '__main__':
        main()

print('Listening ...')
schedule.every(1).seconds.do(job)
#schedule.every().hour.do(job)
#schedule.every().day.at("11:15").do(job)
#schedule.every().monday.do(job)
#schedule.every().wednesday.at("13:15").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)