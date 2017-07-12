from flask import Flask, render_template, request
import json, urllib, urllib3
import feedparser
import os
import time
import re
from fl import settings
from fl.db_mysql import MySqlHelper
app = Flask(__name__)

weather_api_server = "http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=cb22a5d44cba4381795a8b51562e2927"
weather_api_key = "cb22a5d44cba4381795a8b51562e2927"


RRS_FEEDS = {
    'cnn': "http://rss.cnn.com/rss/edition.rss",
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml"
}


@app.route('/', methods=["GET", "POST"])
def get_publication():
    publisher = request.args.get("publisher", "bbc")
    publisher_uri = RRS_FEEDS.get(publisher.lower(), False)
    message = False
    articles = False
    weather = False
    city = 'London, Uk'
    if request.method == 'POST':
        city_from_form = request.form["city"]
        if city_from_form != '':
            city = city_from_form
    weather = get_weather(city)
    if not publisher_uri:
        message = "Sorry no eny feeds"
        return render_template("feed.html", articles=articles, title=publisher, message=message, weather=weather)

    feed = feedparser.parse(publisher_uri)
    return render_template("feed.html", articles=feed['entries'], title=publisher, message=message, weather=weather)


@app.route('/words', methods=['GET', 'POST'])
def words():
    if request.method == 'GET':

        return render_template('words.html')
    if request.method == 'POST':
        files = request.files.getlist('files')
        files_to_parsing = []
        for file in files:
            file_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            files_to_parsing.append(file_path)
        glob_words_dict = dict()
        for file_parse in files_to_parsing:
            file_dict = parse_file(file_parse)
            for word in file_dict:
                if word.lower() in glob_words_dict:
                    glob_words_dict[word.lower()] += 1
                else:
                    glob_words_dict[word.lower()] = 1
        start_time = time.time()
        save_stat_in_db(collect_stat(glob_words_dict))
        escaped = time.time() - start_time
        msg = '{:.2f}s'
        return render_template('words.html', files=files, stat={'len': len(glob_words_dict),
                                                                'time': msg.format(escaped)})


def collect_stat(dict_to_merge):
    saved_stat = get_from_db()
    for word in dict_to_merge:
        if word.lower() in saved_stat:
            saved_stat[word.lower()] += dict_to_merge[word.lower()]
        else:
            saved_stat[word.lower()] = dict_to_merge[word.lower()]
    return saved_stat


def save_stat_in_db(stat):
    DB = MySqlHelper()
    DB.add_many_entries(stat.items())
    #for item in stat.items():
    #    DB.add_entry(item)
    return True


def get_from_db():
    DB = MySqlHelper()
    return dict(DB.get_all_entry())


def parse_file(file):
    data = file_get_contents(file)
    regex_dot = re.compile('\.')
    data = regex_dot.sub(' ', data)
    regex_num = re.compile('[0-9]')
    data = regex_num.sub('', data)
    regex_bslash = re.compile('\\\\')
    data = regex_bslash.sub(' ', data)
    regex_slash = re.compile('/')
    data = regex_slash.sub(' ', data)

    words = data.split()
    alfa_only = []
    regex = re.compile('[^a-zA-Z]')
    for word in words:
        w = regex.sub('', word)
        if len(w) != 0:
            alfa_only.append(w)
    return alfa_only


def file_get_contents(file_name):
    file = open(file_name)
    return file.read()


def get_weather(city):
    city = urllib.parse.quote(city)
    url = weather_api_server.format(city)
    http = urllib3.PoolManager()

    r = http.request('GET', url)
    parsed = json.loads(r.data.decode('utf-8'))
    weather = None
    if parsed.get("weather"):
        weather = {
            "description": parsed["weather"][0]["description"],
            "temperature": parsed["main"]["temp"],
            "city": parsed["name"]
            }
    return weather

if __name__ == '__main__':
    app.run()
