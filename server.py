import phototext
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def home():
    today = phototext.get_today()
    day_month = phototext.day_month
    week = phototext.finnish_weekday
    return render_template("index.html", today=today, day_month=day_month, week=week)

@app.route("/week")
def week():
    all_menus = phototext.get_all_menus()
    taste_lunch = all_menus['taste-buffet-lunch-porvoo']
    taste_daynight = all_menus['taste-day-night-club-porvoo']
    week_number = phototext.week
    return render_template("week.html", taste_lunch=taste_lunch, taste_daynight=taste_daynight, week_number=week_number)

if __name__ == "__main__":
    app.run(debug=True)