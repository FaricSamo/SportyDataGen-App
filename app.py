# -*- coding: utf-8 -*-
"""
Created on Mon Jun 21 14:20:20 2021

@author: User
"""

import io
import os
from flask import Flask, request, render_template, redirect, session, send_file, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from datetime import datetime
import pandas as pd
import sys
sys.path.append('../')
import re

from sport_activities_features.data_extraction_from_csv import DataExtractionFromCSV
from sport_activities_features.tcx_manipulation import TCXFile
from sport_activities_features.data_extraction import DataExtraction
from sport_activities_features.topographic_features import TopographicFeatures
from sport_activities_features.hill_identification import HillIdentification
from sport_activities_features.interval_identification import IntervalIdentificationByHeartrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "secretkey123"

# Get current path
path = os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, 'uploads')

# Make directory if uploads is not exists
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set(['tcx', 'gpx'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Set the secret key to some random bytes and keep it secret.
# A secret key is needed in order to use sessions.
#app.secret_key = b"_j'yXdW7.63}}b7"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Sign Up")
    
    def validate_username(self, username):
        existing_username = User.query.filter_by(username=username.data).first()
        
        if existing_username:
            raise ValidationError("That username already exists. Please choose a different one.")

            
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField("Log In")


all_parameters = {}
selected_parameters = {}
df_col = []
no_data_msg = ""
login_failed = ""
register_failed = {}
temp_key = ""
temp_value = ""
activities_msg = ""

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
        else:
            login_failed = "The username or password is incorrect!"
            return render_template("login.html", title="Log In", form=form, login_failed=login_failed)
    
    return render_template("login.html", title="Log In", form=form)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    global register_failed
    global temp_key
    global temp_value
    register_failed = {}
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        for key, value in form.errors.items():
            if(key == 'username' or key == 'password'):
                temp_value = str(value).replace("['","").replace("']", "")
                register_failed.update({key:temp_value})
        if (register_failed != ""):
            return render_template("register.html", title="Sign Up", form=form, register_failed=register_failed)
        
    return render_template("register.html", title="Sign Up", form=form)

@app.route("/")
def home():
    return render_template("generator.html", title="SportyDataGen")

@app.route("/results", methods=("POST", "GET"))
def results():
    
    global activities_msg
    activities_msg = ""
    
    try:
        all_parameters = {}
        selected_parameters = {}
        df_col = []
        
        activity_type = request.form.get("activity_type")
        number_activities = request.form.get("number_activities")
        duration = request.form.get("duration")
        distance = request.form.get("distance")
        heart_rate = request.form.get("heart_rate")
        calories = request.form.get("calories")
        avg_altitude = request.form.get("avg_altitude")
        max_altitude = request.form.get("max_altitude")
        #pace = request.form.get("pace")
        ascent = request.form.get("ascent")
        descent = request.form.get("descent")
        number_of_hills = request.form.get("number_of_hills")
        distance_between_hills = request.form.get("distance_between_hills")
        number_of_intervals = request.form.get("number_of_intervals")
        average_interval_duration = request.form.get("average_interval_duration")
        longest_interval = request.form.get("longest_interval")
        #intensity = request.form.get("intensity")
        #clusters = request.form.get("clusters")
        #approach = request.form.get("approach")
        #allowMissData = request.form.get("allowMissData")
        
        all_parameters.update({"duration":duration, "distance":distance, "heart_rate":heart_rate, "calories":calories, "avg_altitude":avg_altitude, "max_altitude":max_altitude, "ascent":ascent, "descent":descent, "number_of_hills":number_of_hills, "distance_between_hills":distance_between_hills, "number_of_intervals":number_of_intervals, "average_interval_duration":average_interval_duration, "longest_interval":longest_interval})
        #all_parameters = {activity_type, number_activities, duration, distance, hr_avg, calories, altitude_avg, altitude_max, pace, ascent, descent, allowMissData}
        
        if number_activities.isnumeric():
            for key, value in all_parameters.items():
                if(value != None):
                    selected_parameters.update({key:value})
            
            if selected_parameters != {}:
                
                if os.path.isfile("C:\\Users\\User\\anaconda3\\SportyDataGenEnv\\data\\data.csv"):
                    data_extraction_from_csv = DataExtractionFromCSV()
                    # Extract data from CSV files to dataframe
                    activities = data_extraction_from_csv.from_all_files("C:\\Users\\User\\anaconda3\\SportyDataGenEnv\\data")
                    
                    # Selection of a certain number of random activities
                    temp = data_extraction_from_csv.select_random_activities(int(number_activities))
                    
                    for key in selected_parameters.keys():
                        df_col.append(key) 
                        
                    random_activities = temp[df_col]
                    
                    #Sets the variable now to the current date and time
                    now = datetime.now()
                    
                    #The variable current_time contains the string values of the current time
                    current_time = now.strftime("%d.%m.%Y  |  %H:%M:%S")
                    
                    # Store the CSV data as a string in the session
                    session["df"] = random_activities.to_csv(index=False, header=True, sep=";")
                    
                    num_all = re.findall(r'\d+', str(activities.count()))
                    if int(number_activities) > int(num_all[0]):
                        activities_msg = "These are all sports activity data collections currently available for given conditions."
                    
                    return render_template("results.html", title="Generated data", column_names=random_activities.columns.values, row_data=list(random_activities.values.tolist()),
                                           link_column="Activity ID", zip=zip, selected_parameters=selected_parameters, current_time=current_time, activities_msg=activities_msg)
                else:
                    no_data_msg = "Please upload .tcx or .gpx files"
                    return render_template("results.html", title="Generated data", no_data_msg=no_data_msg, df_col=df_col)
            else:
                no_data_msg = "Data was generated but not displayed because you didn't select any physical activity parameters"
                return render_template("results.html", title="Generated data", no_data_msg=no_data_msg, df_col=df_col)
        else:
            return render_template("generator.html", title="Generated data", input_msg="Input must be integer")
    except:
      return render_template("error.html", title="Generated data")
  
@app.route("/download", methods=["POST"])
def download():
    # Get the CSV data as a string from the session
    csv = session["df"] if "df" in session else "" 
    # Create a string buffer
    buf_str = io.StringIO(csv)

    # Create a bytes buffer from the string buffer
    buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
    
    # Return the CSV data as an attachment
    return send_file(buf_byt,
                     mimetype="text/csv",
                     as_attachment=True,
                     attachment_filename="generatedData.csv")

@app.route("/home")
def home2():
    return render_template("generator.html", title="SportyDataGen")

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/upload")
@login_required
def upload():
    return render_template("upload.html", title="Upload file")

@app.route('/', methods = ['POST', 'GET'])
def uploader():
    if request.method == 'POST':

        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('files[]')

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Retrieving all TCX files in a directory
        tcx_file = TCXFile()
        all_files = tcx_file.read_directory("C:\\Users\\User\\anaconda3\\SportyDataGenEnv\\uploads")
            
        # Extracting the data of all files
        activities = []
        for file in all_files:
            try: 
                activity = { "ID" : os.path.splitext(os.path.split(file)[-1])[0] }
                activity.update(tcx_file.read_one_file(file))
                activity.update(tcx_file.extract_integral_metrics(file))
        
                # Hills
                Hill = HillIdentification(activity['altitudes'], 30)
                Hill.identify_hills() 
                all_hills = Hill.return_hills()             
                Top = TopographicFeatures(all_hills)
                num_hills = Top.num_of_hills()
                distance_hills = Top.distance_of_hills(activity['positions'])
                distance_between_hills = activity["distance"] - distance_hills
        
                activity.update({ "number_of_hills": num_hills, "distance_between_hills": distance_between_hills })
        
                # Identifying the intervals in the activity by heart rate
                # Since a lot of TCX files contain invalid data, intervals cannot be identified,
                # thus those activities cannot be extracted to CSV
                try:
                    Intervals = IntervalIdentificationByHeartrate(activity["distances"], activity["timestamps"], activity["altitudes"], activity["heartrates"])
                    Intervals.identify_intervals()
                    all_intervals = Intervals.return_intervals()
                    activity.update(Intervals.calculate_interval_statistics())
                except:
                    continue
        
                activities.append(activity)
            except:
                continue
        
        # Extracting the data in CSV format
        data_extraction = DataExtraction(activities)
        data_extraction.extract_data("C:\\Users\\User\\anaconda3\\SportyDataGenEnv\\data\\data")
        
        return redirect('/')
    
    

if __name__ == "__main__":
    app.run()