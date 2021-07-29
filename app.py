# -*- coding: utf-8 -*-
"""
Created on Mon Jun 21 14:20:20 2021

@author: User
"""

import io
from flask import Flask, request, render_template, session, send_file
from datetime import datetime
import pandas as pd
import sys
sys.path.append('../')

app = Flask(__name__)

# Set the secret key to some random bytes and keep it secret.
# A secret key is needed in order to use sessions.
app.secret_key = b"_j'yXdW7.63}}b7"


all_parameters = {}
selected_parameters = {}
df_col = []
no_data_msg = ""

@app.route("/")
def home():
    return render_template("generator.html", title="SportyDataGen")

@app.route("/results", methods=("POST", "GET"))
def results():
    
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
        #intensity = request.form.get("intensity")
        #clusters = request.form.get("clusters")
        #approach = request.form.get("approach")
        #allowMissData = request.form.get("allowMissData")
        
        all_parameters.update({"duration":duration, "distance":distance, "heart_rate":heart_rate, "calories":calories, "avg_altitude":avg_altitude, "max_altitude":max_altitude, "ascent":ascent, "descent":descent})
        #all_parameters = {activity_type, number_activities, duration, distance, hr_avg, calories, altitude_avg, altitude_max, pace, ascent, descent, allowMissData}
        
        if number_activities.isnumeric():
            for key, value in all_parameters.items():
                if(value != None):
                    selected_parameters.update({key:value})
            
            if selected_parameters != {}:
                from sport_activities_features.data_extraction_from_csv import DataExtractionFromCSV
                
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
            
                return render_template("results.html", title="Generated data", column_names=random_activities.columns.values, row_data=list(random_activities.values.tolist()),
                                       link_column="Activity ID", zip=zip, selected_parameters=selected_parameters, current_time=current_time)
        
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

@app.route("/news")
def news():
    return render_template("news.html", title="News")

@app.route("/addNews")
def addNews():
    return render_template("addNews.html", title="Add news")

if __name__ == "__main__":
    app.run()