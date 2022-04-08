import sys
from datetime import datetime, timedelta

import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

API_KEY = 'a2eec5522c1c2c34cdf69f49e448083b'
user_agent = {'User-agent': 'Mozilla/5.0'}
DB_NAME = 'weather'

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}.db'

db = SQLAlchemy(app)


class WeatherInCity(db.Model):
    __tablename__ = DB_NAME

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)


def page_not_found(e):
    return render_template('404.html'), 404


def get_local_time(timezone: str) -> datetime:
    return datetime.utcnow() + timedelta(seconds=int(timezone))


def get_part_of_the_day(time_stamp: datetime) -> str:
    hour = time_stamp.hour
    parts_of_the_day = ((5, 12, 'morning'), (12, 17, 'afternoon'),
                        (17, 21, 'evening'), (21, 4, 'night'),
                        )
    for day_part in parts_of_the_day:
        if any((day_part[0] <= hour, hour < day_part[1])):
            return day_part[2]


def add_to_database(city_name, database=WeatherInCity):
    if not city_name:
        pass
    city = database(name=city_name)
    db.session.add(city)
    db.session.commit()


def get_weather_from_api(city_name) -> dict:
    def kelvin_to_celcius(kelvin_value: float) -> int:
        return int(round(kelvin_value - 273.15))

    web_site = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}'
    r = requests.get(web_site, headers=user_agent)
    if r.status_code == 200:
        json_data = r.json()
        dict_with_weather_info = {
            'name': json_data['name'].upper(),
            'temp': kelvin_to_celcius(float(json_data['main']['temp'])),
            'state': json_data['weather'][0]['main'],
            'day_part': get_part_of_the_day(get_local_time(json_data['timezone'])),
        }
        return dict_with_weather_info
    return dict()


def get_forecast() -> list:
    cities_in_db = WeatherInCity.query.all()
    weather_data: list = []
    for city in cities_in_db:
        data = get_weather_from_api(city.name)
        if data:
            weather_data.append(data)
    return weather_data


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        weather_data = get_forecast()
        return render_template('index.html', cities=weather_data)
    elif request.method == 'POST':
        city_name = request.form.get('city_name')
        add_to_database(city_name)
        return redirect(url_for('index'))  # name of the function


# don't change the following way to run flask:
if __name__ == '__main__':
    db.create_all()  # save the table in the database
    app.register_error_handler(404, page_not_found)
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port, debug=True)
    else:
        app.run(debug=True)
