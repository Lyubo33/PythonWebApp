import os
from flask import Flask, render_template, request, flash, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import csv, config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_db.sqlite3' #initializing the config for the database
app.secret_key = ['S]_U]-ioaUU6H&rDcu`glP,7;%}6Bk'] #used for flash messages

db = SQLAlchemy(app)

def validate_and_calculate_csv(file):
    """Takes a filepath to the uploaded csv file, parses it, validates it and calculates the result

    This function reads a CSV file with columns A, O, and B, where:
    - A and B are the left and right operands and are of float values.
    - O is the operator from the supported set of: {'+', '-', '*', '/'}.

    Args:
        file (str): Path to the uploaded CSV file.

    Returns:
        float: The total sum of all rows calculated from the CSV data.
        None, if validation fails due to incorrect headers or values.

    Raises:
        ValueError: If non-numeric data is found in the CSV file.
    """
    supported_operators={
        '+': lambda a,b : a + b,
        '-': lambda a,b : a - b,
        '*': lambda a,b : a * b,
        '/': lambda a,b : a / b if b!=0 else float('inf'),
    }
    total_sum =0
    with open(file, 'r') as file:
        csv_reader = csv.reader(file, delimiter='|')
        headers = next(csv_reader)
        if headers !=['A','O','B']:
            flash("The headers of the file should be A|O|B", 'error')
            return None
        for row in csv_reader:
            try:
                a = float(row[0].strip())
                o = row[1].strip()
                b = float(row[2].strip())
                if o not in supported_operators:
                    flash(f"Invalid operator '{o}' in row '{row}'. Supported operators are {list(supported_operators.keys())} ",'error')
                    return None
                result = supported_operators[o](a,b)
                if result == None:
                    flash(f"Division by zero error in row {row}",'error')
                    return None
                    
                total_sum += result
            except:
                ValueError(f"Invalid numeric values in row {row}", 'error')
                return None
    return total_sum

#Requests table                 
class Requests(db.Model):
    __tablename__ = 'requests'
    id = db.Column("id", db.Integer, primary_key = True)
    user_name = db.Column("username", db.String(100))
    request_name = db.Column("request", db.String(100))
    file_ref = db.Column("file_ref", db.String(100))
    results = db.relationship('Results', backref='requests',lazy='dynamic')
    
    def __init__(self, user_name,request_name,file_ref):
        self.user_name = user_name
        self.request_name = request_name
        self.file_ref = file_ref

#Results table
class Results(db.Model):
    __tablename__ = 'results'
    id = db.Column("id", db.Integer, primary_key = True)
    result = db.Column("result", db.Float)
    request_id = db.Column("req_id",db.ForeignKey('requests.id'))
    
    def __init__(self, result, request_id):
        self.result = result
        self.request_id = request_id

#Single endpoint for the api
@app.route('/app/compute', methods=['POST','GET'])
def compute():
    #Recieving input from the form
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        file = request.files['csv']
        #File from form gets stored in uploads
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        #Validating the API_KEY
        if password != config.API_KEY:
            flash("Invalid API key provided", 'error')
            return redirect(url_for('compute'))
        #Calculating the total_sum
        total_sum = validate_and_calculate_csv(file_path)
        if total_sum is None:
            return redirect(url_for('compute'))
        #Request to be stored in database
        new_request = Requests(user_name=username,request_name="File Upload",file_ref=file.filename)
        db.session.add(new_request)
        db.session.commit()
        
        #Result gets stored in database
        new_result = Results(result=total_sum,request_id=new_request.id)
        db.session.add(new_result)
        db.session.commit()

        #Showing message after succesful calculation
        flash(f"Calculation successful. Total sum: {total_sum}", "success")
        return redirect(url_for('compute'))
    
    #Rendering the interface  
    return render_template("index.html")

#Generating databse if it doesn't exist yet
with app.app_context():
    db.create_all()

#Entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")