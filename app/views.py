from app import app, render_template, request

data = []

@app.route("/")
def home():
    return render_template("generator.html", title="SportyDataGen")

@app.route("/results", methods=["POST"])
def results():
    sport = request.form.get("sport")
    activities = request.form.get("activities")
    workDuration = request.form.get("workDuration")
    workDistance = request.form.get("workDistance")
    avgHeartRate = request.form.get("avgHeartRate")
    calories = request.form.get("calories")
    avgAltitude = request.form.get("avgAltitude")
    maxAltitude = request.form.get("maxAltitude")
    pace = request.form.get("pace")
    ascent = request.form.get("ascent")
    descent = request.form.get("descent")
    intensity = request.form.get("intensity")
    clusters = request.form.get("clusters")
    approach = request.form.get("approach")
    allowMissData = request.form.get("allowMissData")
    data.append(f"{sport} {activities} {workDuration} {workDistance} {avgHeartRate} {calories} {avgAltitude} {maxAltitude} {pace} {ascent} {descent} {intensity} {clusters} {approach} {allowMissData}")
    return render_template("results.html", title="Results", data=data)

@app.route("/home")
def home2():
    return render_template("generator.html", title="SportyDataGen")

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/news")
def news():
    return render_template("news.html", title="News")

@app.route("/addNews")
def addNews():
    return render_template("addNews.html", title="Add news")