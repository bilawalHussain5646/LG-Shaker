import base64
from io import BytesIO
import shutil
from flask import Flask,request, jsonify,Response,render_template,redirect,url_for,session,flash,send_file
from datetime import datetime,timedelta
from sqlalchemy.orm import load_only
from sqlalchemy import asc,desc,and_
from database import app, db
import chardet
from models import *
from functools import wraps
import jwt
from flask import request, abort
from flask_cors import cross_origin
import json
import qrcode
import os

from PIL import Image
import zipfile
import redis
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,get_jwt,get_jwt_identity
)
import pandas as pd
from datetime import datetime
from datetime import timedelta
from datetime import timezone


blacklist = set()





app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']
app.config['SQLALCHEMY_POOL_SIZE'] = 10  # Adjust as needed
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 1800  # Adjust as needed
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # Adjust as needed
app.config['SQLALCHEMY_POOL_PRE_PING'] = True  # Adjust as needed

# Set the secret key to sign the JWTs with
app.config['JWT_SECRET_KEY'] = ''  # Change this!

ACCESS_EXPIRES = timedelta(minutes=30)

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_EXPIRES

# from flask_mail import Mail, Message
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
jwt = JWTManager(app)


def check_token_in_blacklist(token):
    if token in blacklist:
        return True
    else:
        return False


@app.route('/user-info', methods=['POST'])
@jwt_required()
@cross_origin()
def user_data():
    
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    
    user_data = get_jwt_identity()
    print(user_data)
    return jsonify(user=user_data),200
    



# Fetch qr code image 
@app.route('/api/image/<entry_id>')
@cross_origin()
def get_qr_code(entry_id):
    try:
        image = db.session.query(entry).filter_by(id=entry_id).first()
    except:
        db.session.remove()
        db.session.close()
        db.session.remove()
        image = db.session.query(entry).filter_by(id=entry_id).first()

    db.session.close()
    if image:
        image_data = image.qr_code
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        response_data = {
            'image_id': image.id,
            'image_data': image_base64,
        }
        return jsonify(response_data)
    return jsonify({'error': 'qr code not found'}), 404



# For the dashboard --
# Functionality: Add Entry in the db table
@app.route('/add-entry', methods=['POST'])
def add_entry_data():
    if 'email' in session:
        if session['role'] == 1 or session['role'] == 2:
            model_name = request.form['model_name']
            report_number = request.form['report_number']
            issue_date = request.form['issue_date']
            issue_date=datetime.strptime(issue_date,"%Y-%m-%d").date()
            contact_number = request.form['contact_number']
            country_of_origin = request.form['country_of_origin']
            lab_name = request.form['lab_name']
            manufacturer_name = request.form['manufacturer_name']
            try:
                pdf_file = request.files["pdf_file"]
            except:
                pdf_file = None
            user_id = session['id']

            qr_code = None

            try:
                newrecord = entry(model_name,report_number,issue_date,contact_number,country_of_origin,lab_name,manufacturer_name,pdf_file.read(),user_id,qr_code)
                db.session.add(newrecord)
                db.session.commit()
            except:
                db.session.remove()
                db.session.close()
                # db.session.remove()
                newrecord = entry(model_name,report_number,issue_date,contact_number,country_of_origin,lab_name,manufacturer_name,pdf_file.read(),user_id,qr_code)
                db.session.add(newrecord)
                db.session.commit()
            
        
            db.session.refresh(newrecord)
            # Generate QR Code here and save it in the object and add the record
            data = str(str(request.base_url).replace("/add-entry","") + url_for("download",entry_id=str(newrecord.id)))
            print(data)
            # Creating an instance of QRCode class
            qr = qrcode.QRCode(version = 1,
                            box_size = 10,
                            border = 5)
            
            # Adding data to the instance 'qr'
            qr.add_data(data)
            
            qr.make(fit = True)
            img = qr.make_image(fill_color = 'black',
                                back_color = 'white')
            
            # Convert the image to a bytes object
            image_byte_io = BytesIO()
            img.save(image_byte_io, format='PNG')
            image_binary = image_byte_io.getvalue()

            newrecord.qr_code = image_binary
            db.session.commit()
            db.session.close()

            flash("Entry added successfuly","success")
            return redirect(url_for("index"))
            # return jsonify({
            #     "message": "Entry added successfully"
            # }),200
    else:
        flash("Session expired","warning")
        return redirect(url_for("index"))


# For the dashboard --
# Functionality: Add Entry in the db table
@app.route('/add-multiple-entry', methods=['POST'])
def add_multiple_data():
    if 'email' in session:
        if session['role'] == 1 or session['role'] == 2:

            unzip_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'unzipped')
            
            if 'zip_file' not in request.files:
                pass
                # return "No file part"
            else:
                zip_file = request.files['zip_file']

                if zip_file.filename == '':
                    pass

                elif zip_file:
                    try:
                        # Save the uploaded ZIP file
                        zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_file.filename)
                        zip_file.save(zip_file_path)

                        # Unzip the uploaded ZIP file
                        unzip_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"temp{session['id']}")
                        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                            zip_ref.extractall(unzip_folder)

                        # Delete the ZIP file after extraction
                        os.remove(zip_file_path)

                        # return "ZIP file uploaded, extracted, and deleted successfully"
                    except Exception as e:
                        print (str(e))
                        # return str(e)

            # Upload zip file and excel file

            try:
                excel_file = request.files['excel_file']
            except:
                print("Error")
                return redirect(url_for("index"))
                # Return to the form and show message 

            if excel_file.filename == '':
                print("Error in excel")
                return redirect(url_for("index"))
                # Return to the form and show message 

            if excel_file:
                df = pd.read_excel(excel_file)
            
                # try:
                for index, row in df.iterrows():
                        # Check if the file with that name exist in the zip folder or not 
                        # if exist then read it and upload to database 
                        # else, put none instead of file  
                        target_file = row.pdf_file  # Replace with the actual file name

                        # Check if the specified file exists in the extracted folder
                        target_file_path = os.path.join(unzip_folder, target_file)
                        # print(target_file_path)
                        if os.path.isfile(target_file_path):
                            
                            
                            # Read the file using the detected encoding
                            with open(target_file_path, 'rb') as f:
                                file_content = f.read()
                            # Read the file's content
                            # with open(target_file_path, 'r') as f:
                            #     file_content = f.read()
                        else:
                            file_content = None
                        print(type(row.issue_date))
                        issue_date=row.issue_date.date()
                        qr_code = None
                        try:
                            record = entry(row.model_name,	
                            row.report_number,	
                            issue_date,	
                            row.contact_number,	
                            row.country_of_origin,	
                            row.lab_name,	
                            row.manufacturer_name,	
                            file_content,session['id'],qr_code)

                            db.session.add(record)
                            db.session.commit()
                        except:
                            db.session.remove()
                            db.session.close()
                            db.session.remove()

                            record = entry(row.model_name,	
                            row.report_number,	
                            issue_date,	
                            row.contact_number,	
                            row.country_of_origin,	
                            row.lab_name,	
                            row.manufacturer_name,	
                            file_content,session['id'],qr_code)

                            db.session.add(record)
                            db.session.commit()
                        
                        db.session.refresh(record)
                        # Generate QR Code here and save it in the object and add the record
                        data = str(str(request.base_url).replace("/add-multiple-entry","") + url_for("download",entry_id=str(record.id)))
                        print(data)
                
                        # Creating an instance of QRCode class
                        qr = qrcode.QRCode(version = 1,
                                        box_size = 10,
                                        border = 5)
                        
                        # Adding data to the instance 'qr'
                        qr.add_data(data)
                        
                        qr.make(fit = True)
                        img = qr.make_image(fill_color = 'black',
                            back_color = 'white')
        
                        # Convert the image to a bytes object
                        image_byte_io = BytesIO()
                        img.save(image_byte_io, format='PNG')
                        image_binary = image_byte_io.getvalue()
                        record.qr_code = image_binary
                        db.session.commit()

                shutil.rmtree(unzip_folder, ignore_errors=True)  # Remove the directory and its contents if it exists

            # Read excel file and unzip the folder and read the file names
            #  If the file name is same as the excel id, then add that file in the database 
            #  else, skip that entry. 




            # user_id = session['id']


            # newrecord = entry(model_name,report_number,issue_date,contact_number,country_of_origin,lab_name,manufacturer_name,pdf_file.read(),user_id)
            # db.session.add(newrecord)
            # db.session.commit()
            db.session.close()

            flash("Entries added successfuly","success")
            return redirect(url_for("index"))
            # return jsonify({
            #     "message": "Entry added successfully"
            # }),200
    else:
        flash("Session expired","warning")
        return redirect(url_for("index"))



# Download excel 
@app.route("/download-excel",methods=['POST'])
def download_excel():
    # data = db.session.query(entry).values(entry.model_name).all()
    try:
        data = entry.query.all()
    except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            data = entry.query.all()
    # print(data)
    # Define the maximum number of rows per Excel sheet and sheets per Excel file
    max_rows_per_sheet = 100000  # You can adjust this as needed
    max_sheets_per_file = 250  # You can adjust this as needed

    # Calculate the number of sheets needed and the number of Excel files needed
    num_sheets = (len(data) + max_rows_per_sheet - 1) // max_rows_per_sheet
    num_files = (num_sheets + max_sheets_per_file - 1) // max_sheets_per_file

    # Create a temporary directory to store the Excel files
    temp_dir = 'temp_excel_files'
    os.makedirs(temp_dir, exist_ok=True)

    # Create a list to store the file paths
    file_paths = []

    for file_num in range(num_files):
        # Create a new Excel writer object for each file
        file_path = f'lg-shaker-{file_num}.xlsx'
        complete_path= os.path.join(f'{temp_dir}', file_path)
        with pd.ExcelWriter(complete_path, engine='openpyxl') as file_writer:
            # Split the data into sheets for this file
            start_sheet = file_num * max_sheets_per_file
            end_sheet = min((file_num + 1) * max_sheets_per_file, num_sheets)

            for sheet_num in range(start_sheet, end_sheet):
                start_idx = sheet_num * max_rows_per_sheet
                end_idx = (sheet_num + 1) * max_rows_per_sheet
                sheet_data = data[start_idx:end_idx]

                # Convert the sheet data to a Pandas DataFrame
                df = pd.DataFrame([{'model_name':record.model_name,	
                        'report_number':record.report_number,	
                        'issue_date':record.issue_date,	
                        'contact_number':record.contact_number,	
                        'country_of_origin':record.country_of_origin,	
                        'lab_name':record.lab_name,	
                        'manufacturer_name':record.manufacturer_name} for record in sheet_data])

                # Write the DataFrame to a sheet with a unique name
                sheet_name = f'lg-shaker-report-sheet-{sheet_num + 1}'
                df.to_excel(file_writer, sheet_name=sheet_name, index=False)

        # Add the file path to the list
        file_paths.append(complete_path)

    # Create a zip file to contain all Excel files
    zip_filename = 'lg-shaker.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))

    # Create a Flask response with the zip file
    response = Response(open(zip_filename, 'rb').read())
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=lg-shaker.zip'

    # Clean up temporary Excel files and the temporary directory
    for file_path in file_paths:
        os.remove(file_path)
    
    os.remove(zip_filename)

    os.rmdir(temp_dir)

    return response




# Functionality: Add Entry in the db table
@app.route('/add-entry', methods=['POST'])
@jwt_required()
@cross_origin()
def add_entry():
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    

    current_user = get_jwt_identity()
    if current_user['role'] == 1 or current_user['role'] == 2:
        model_name = request.form['model_name']
        report_number = request.form['report_number']
        issue_date = request.form['issue_date']
        issue_date=datetime.strptime(issue_date,"%Y-%m-%d").date()
        contact_number = request.form['contact_number']
        country_of_origin = request.form['country_of_origin']
        lab_name = request.form['lab_name']
        manufacturer_name = request.form['manufacturer_name']
        pdf_file = request.files["pdf_file"]
        user_id= current_user['id']

        qr_code = None

        
        
        
        # --------------------------------------------------------------------
        try:
            newrecord = entry(model_name,report_number,issue_date,contact_number,country_of_origin,lab_name,manufacturer_name,pdf_file.read(),user_id,qr_code)
            db.session.add(newrecord)
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            newrecord = entry(model_name,report_number,issue_date,contact_number,country_of_origin,lab_name,manufacturer_name,pdf_file.read(),user_id,qr_code)
            db.session.add(newrecord)
        db.session.commit()
        
        
        db.session.refresh(newrecord)
        # Generate QR Code here and save it in the object and add the record
        data = str(newrecord.id)
 
        # Creating an instance of QRCode class
        qr = qrcode.QRCode(version = 1,
                        box_size = 10,
                        border = 5)
        
        # Adding data to the instance 'qr'
        qr.add_data(data)
        
        qr.make(fit = True)
        img = qr.make_image(fill_color = 'red',
                            back_color = 'white')
        newrecord.qr_code = img.read()
        
        db.session.commit()
        db.session.close()

        # flash("Entry added successfuly","success")
        # return redirect(url_for("index"))
        return jsonify({
            "message": "Entry added successfully"
        }),200
    else:
        return jsonify({
            "message": "You don\'t have access"
        }),400



# Functionality: Edit User
@app.route("/edit_user/<int:user_id>",methods=['PUT'])
@jwt_required()
@cross_origin()
def edit_user(user_id):
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    current_user = get_jwt_identity()
    if current_user["role"] == 2:

        email = request.form['email']
        password = request.form['password']
        username = request.form['username']
        name = request.form['name']
        role = request.form['role']
        try:
            users = db.session.query(user).filter_by(id = user_id).first()
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            users = db.session.query(user).filter_by(id = user_id).first()

        if users is None:
            db.session.close()
            return jsonify({
                "message": f"{user_id} doesnt exist",
            }),400
        users.email = email
        users.username = username
        users.name = name
        users.password = generate_password_hash(password)
        users.role = role
        
        db.session.commit()
        db.session.close()

        return jsonify({
            "message": f"{user_id} updated successfully",
        }),200

    else:
        return jsonify({
             "message":"You don\'t have access"
        }),400    



# Functionality: Edit Entry
@app.route("/edit/<int:entry_id>",methods=['PUT'])
@jwt_required()
@cross_origin()
def edit_entry( entry_id):
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    current_user = get_jwt_identity()
    if current_user["role"] == 1 or current_user["role"] == 2:
                    
                    model_name = request.form['model_name']
                    report_number = request.form['report_number']
                    issue_date = request.form['issue_date']
                    contact_number = request.form['contact_number']
                    country_of_origin = request.form['country_of_origin']
                    lab_name = request.form['lab_name']
                    manufacturer_name = request.form['manufacturer_name']
                    pdf_file = request.files["pdf_file"]
                    user_id= request.form['user_id']

                    try:
                        entries = db.session.query(entry).filter_by(id = entry_id).first()
                    except:
                            db.session.remove()
                            db.session.close()
                            db.session.remove()
                            entries = db.session.query(entry).filter_by(id = entry_id).first()

                    if entries is None:
                        db.session.close()
                        return jsonify({
                            "message": f"{entry_id} doesnt exist",
                        })
                    entries.model_name = model_name
                    entries.report_number = report_number
                    entries.issue_date = issue_date
                    entries.contact_number = contact_number
                    entries.country_of_origin = country_of_origin
                    entries.lab_name = lab_name
                    entries.manufacturer_name = manufacturer_name
                    entries.pdf_file = pdf_file.read()
                    entries.user_id = user_id
                    db.session.commit()
                    db.session.close()
                    return jsonify({
                        "message": f"{entry_id} updated successfully",
                    })

    else:
        return jsonify({
             "message":"You don\'t have access"
        }),400  

# Functionality: Edit Entry
@app.route("/edit/entry",methods=['POST'])
def update_entry_data():
    
    if 'email' in session:
        if session["role"] == 1 or session["role"] == 2:
                        
                        entry_id = request.form['entry_id']
                        model_name = request.form['model_name_update']
                        report_number = request.form['report_number_update']
                        issue_date = request.form['issue_date_update']
                        contact_number = request.form['contact_number_update']
                        country_of_origin = request.form['country_of_origin_update']
                        lab_name = request.form['lab_name_update']
                        manufacturer_name = request.form['manufacturer_name_update']
                        pdf_file = request.files["pdf_file_update"]
                        
                        user_id= session['id']
                        try:
                            entries = db.session.query(entry).filter_by(id = entry_id).first()
                        except:
                            db.session.remove()
                            db.session.close()
                            db.session.remove()
                            entries = db.session.query(entry).filter_by(id = entry_id).first()

                        if entries is None:
                            db.session.close()
                            flash("Entry doesn\'t exist","warning")
                            return redirect(url_for("index"))
                            
                        entries.model_name = model_name
                        entries.report_number = report_number
                        entries.issue_date = issue_date
                        entries.contact_number = contact_number
                        entries.country_of_origin = country_of_origin
                        entries.lab_name = lab_name
                        entries.manufacturer_name = manufacturer_name
                        if not pdf_file:
                            pass
                        else:    
                            entries.pdf_file = pdf_file.read()
                        
                        entries.user_id = user_id
                        db.session.commit() 
                        db.session.close()
                        flash("Entry updated successfully","success")
                        return redirect(url_for("dashboard"))
        else:
            flash("You don't have access","warning")
            return redirect(url_for("index"))

    else:
        flash("Session expired","warning")
        return redirect(url_for("index")) 
   

# Functionality: Edit Entry
@app.route("/edit/user",methods=['POST'])
def update_user_data():
    
    if 'email' in session:
        if session["role"] == 1 or session["role"] == 2:      
            entry_id = request.form['entry_id']
            name = request.form['name_update']
            email = request.form['email_update']
            role = request.form['role_update']
            username = request.form['username_update']
            password = request.form['password_update']
            confirm_password = request.form['confirm_password_update']
            try:
                entries = db.session.query(user).filter_by(id = entry_id).first()
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                entries = db.session.query(user).filter_by(id = entry_id).first()
            if entries is None:
                db.session.close()
                flash("User doesn\'t exist","warning")
                return redirect(url_for("users_"))
            if password == "" or confirm_password == "":
                entries.name = name
                entries.email = email
                entries.username = username
                entries.role = role
                db.session.commit()
                db.session.close()
                flash("User updated successfully","success")
                return redirect(url_for("users_"))
            if password == confirm_password: 
                entries.name = name
                entries.email = email
                entries.username = username
                entries.password = generate_password_hash(password)
                entries.role = role
                db.session.commit()
                db.session.close()
                flash("User updated successfully","success")
                return redirect(url_for("users_"))
            else:
                flash("Password doesn\'t matched","danger")
                return redirect(url_for("users_"))
        else:
            flash("You don't have access","warning")
            return redirect(url_for("users_"))

    else:
        flash("Session expired","warning")
        return redirect(url_for("index")) 
   



# Delete Entry 
@app.route("/delete-entry",methods=['POST'])
def delete_entry_user():
    if 'email' in session:
        if session["role"] == 1 or session["role"] == 2:
            entry_id = request.form['id']
            try:
                check_entry = db.session.query(entry).filter(entry.id == entry_id).first()
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                check_entry = db.session.query(entry).filter(entry.id == entry_id).first()

            if check_entry is None:
                flash("Entry doesn\'t exist","warning")
                return redirect(url_for("dashboard"))
            
            db.session.query(entry).filter(entry.id == entry_id).delete()
            db.session.commit()
            db.session.close()
        
            flash("Entry removed successfully","success")
            return redirect(url_for("dashboard"))
        
        else:
            flash("You don't have access","warning")
            return redirect(url_for("index"))
    else:
        flash("Session expired","warning")
        return redirect(url_for("index"))


# Delete Entry 
@app.route("/delete-entry",methods=['POST'])
@jwt_required()
@cross_origin()
def delete_entry():
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    current_user = get_jwt_identity()

    if current_user["role"] == 1 or current_user["role"] == 2:
        entry_id = request.form['id']
        # model_name = request.form['model_name']
        # check if the entry exist or not 
        try:
            check_entry = db.session.query(entry).filter(entry.id == entry_id).first()
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            check_entry = db.session.query(entry).filter(entry.id == entry_id).first()
        if check_entry is None:
            db.session.close()
            return jsonify({
            "message": f"{entry_id} doesnt exist",
        }),404
        db.session.query(entry).filter(entry.id == entry_id).delete()
        db.session.commit()
        db.session.close()
    
        return jsonify({
            "message": f"{entry_id} is removed",
        }),200
    else:
        return jsonify({
             "message":"You don\'t have access"
        }),400  

# Delete user 
# @app.route("/delete_user",methods=['POST'])
# @jwt_required()
# @cross_origin()
# def delete_user():
#     jti = get_jwt()["jti"]
#     # print(jti)
    
#     if check_token_in_blacklist(jti):
#         return jsonify(msg="Token expired"),401
#     current_user = get_jwt_identity()

#     if current_user["role"] == 2:
#         user_id = request.form['id']
        
#         check_user = db.session.query(user).filter(user.id == user_id).first()
#         if check_user is None:
#             db.session.close()
#             return jsonify({
#             "message": f"{user_id} doesnt exist",
#         }),404
#         db.session.query(user).filter(user.id == user_id).delete()
#         db.session.commit()
#         db.session.close()
    
#         return jsonify({
#             "message": f"{user_id} is removed",
#         }),200
#     else:
#         return jsonify({
#              "message": "You don\'t have access"
#         }),400


# Delete user 
@app.route("/delete_user",methods=['POST'])
def deleteUser():

    if session["role"] == 2:
        user_id = request.form['id']
        try:
            check_user = db.session.query(user).filter(user.id == user_id).first()
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            check_user = db.session.query(user).filter(user.id == user_id).first()
        
        if check_user is None:
            db.session.close()
            return redirect(url_for("users_"))
        db.session.query(user).filter(user.id == user_id).delete()
        db.session.commit()
        db.session.close()
        return redirect(url_for("users_"))
    else:
        flash("You don't have access", "warning")
        return redirect(url_for("users_"))
        

# # Fetch Users
# @app.route('/users',methods=['GET'])
# @jwt_required()
# @cross_origin()
# def fetch_users():
    
#     jti = get_jwt()["jti"]
#     # print(jti)
    
#     if check_token_in_blacklist(jti):
#         return jsonify(msg="Token expired"),401
    
#     current_user = get_jwt_identity()
#     if current_user['role'] == 2:
#         res = db.session.query(user).all()
#         db.session.close()
#         temp = []
#         for ent in res:
#             data = {
#                 "id": ent.id,
#                 "username": ent.username,
#                 "email": ent.email,
#                 "password": ent.password,
#                 "role": ent.role, 
#                 "name": ent.name,
#                 "update": ent.id
#             }
#             temp.append(data)

#         return jsonify({
#             "data":temp,
#         }),200
#     else:
#         return jsonify({
#             "message":"You don\'t have access",
#         }),400 

# Fetch Entries
@app.route('/entries', methods=['GET'])
@jwt_required()
@cross_origin()
def fetch_entries():
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    # Send page number from params 
    try:
        text=request.args.get('text')
    except:
        text=""
    try:
        page = request.args.get('page')
        page= int(page)
        page_number = page
        
    except:
        page = request.args.get('page',1,type=int)
        page_number = 1 
    
    if text=="" or not text:
        # print("text:",text)
        try:
            pagination = db.session.query(entry).paginate(page, per_page=10)
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            pagination = db.session.query(entry).paginate(page, per_page=10)
        db.session.close()
    else:
        # print("text-2nd:",text)
        search = "%{}%".format(text)
        try:
            pagination = db.session.query(entry).filter(entry.model_name.like(search)).paginate(page, per_page=10)
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            pagination = db.session.query(entry).filter(entry.model_name.like(search)).paginate(page, per_page=10)
        db.session.close()

    # db.session.close()
    temp = []
    for ent in pagination.items:
        # print((ent.issue_date))
        try:
            issue_date = ent.issue_date.strftime('%Y-%m-%d')

        except:
            issue_date = None
        # print(issue_date)
        if not ent.pdf_file:
            pdf_file = None
        else:
            pdf_file = "Found"
        data = {
            "id": ent.id,
            "model_name": ent.model_name,
            "report_number": ent.report_number,
            "issue_date": issue_date,
            "contact_number": ent.contact_number, 
            "country_of_origin": ent.country_of_origin,
            "lab_name": ent.lab_name,
            "manufacturer_name": ent.manufacturer_name,
            "update": ent.id,
            "pdf_file": pdf_file,
            "download": ent.id,
            "user_id": ent.user_id

        }
        temp.append(data)
    paginat = []

    for number in pagination.iter_pages():
        paginat.append(number)
    print(page_number)
    # flash("Bidding Successfuly updated","success")
    return jsonify({
        
        "data":temp,
        "prev_num": pagination.prev_num,
        "next_num": pagination.next_num,
        "pagination_page":page,
        "paginat":paginat,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,

    }),200




# # Fetch Single User
# @app.route('/users/<int:user_id>', methods=['GET'])
# @jwt_required()
# @cross_origin()
# def fetch_user(user_id):
#     jti = get_jwt()["jti"]
    
#     if check_token_in_blacklist(jti):
#         return jsonify(msg="Token expired"),401
#     res = db.session.query(user).filter_by(id=user_id).first()
#     db.session.close()

#     if res is None:
#         return jsonify(msg="User not found"),404
#     else:
#         print(res.id)
#         data = {
#                 "id": res.id,
#                 "email": res.email,
#                 "username": res.username,
#                 "name": str(res.name),
#                 "role": res.role, 
#                 "update": res.id

#             }
#         json_response = json.dumps(data)
#         response = Response(json_response,content_type='application/json')

#         return response,200

# Fetch Single User
@app.route('/users/<int:user_id>', methods=['GET'])
def fetchUser(user_id):
    try:
        res = db.session.query(user).filter_by(id=user_id).first()
    except:
        db.session.remove()
        db.session.close()
        db.session.remove()
        res = db.session.query(user).filter_by(id=user_id).first()

    db.session.close()

    if res is None:
        return redirect(url_for("users_"))
    else:
        
        data = {
                "id": res.id,
                "email": res.email,
                "username": res.username,
                "name": str(res.name),
                "role": res.role

            }
        json_response = json.dumps(data)
        response = Response(json_response,content_type='application/json')

        return response,200


# Fetch Single Entry
# @app.route('/entries/<int:entry_id>', methods=['GET'])
# @jwt_required()
# @cross_origin()
# def fetch_entry(entry_id):
#     jti = get_jwt()["jti"]
    
#     if check_token_in_blacklist(jti):
#         return jsonify(msg="Token expired"),401
#     res = db.session.query(entry).filter_by(id=entry_id).first()
#     db.session.close()

#     if res is None:
#         return jsonify(msg="Entry not found"),404
#     else:
#         print(res.id)
#         file_data_base64 = base64.b64encode(res.pdf_file).decode('utf-8')
#         data = {
#                 "id": res.id,
#                 "model_name": res.model_name,
#                 "report_number": res.report_number,
#                 "issue_date": str(res.issue_date),
#                 "contact_number": res.contact_number, 
#                 "country_of_origin": res.country_of_origin,
#                 "lab_name": res.lab_name,
#                 "manufacturer_name": res.manufacturer_name,
#                 "pdf_file": file_data_base64,
#                 "user_id": res.user_id

#             }
#         json_response = json.dumps(data)
#         response = Response(json_response,content_type='application/json')
#         response.headers['Content-Disposition'] = 'attachment; filename="report.pdf"'

#         return response,200


# Fetch Single Entry
@app.route('/entries/<int:entry_id>', methods=['GET'])
def fetch_single_entry(entry_id):
    if 'email' in session:
        if session['role'] == 1 or session['role'] == 2:
            try:
                res = db.session.query(entry).filter_by(id=entry_id).first()
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                res = db.session.query(entry).filter_by(id=entry_id).first()

            db.session.close()

            if res is None:
                return jsonify(msg="Entry not found"),404
            else:
                # print(res.id)
                # file_data_base64 = base64.b64encode(res.pdf_file).decode('utf-8')
                pdf_file_exist=False
                if res.pdf_file is None or not res.pdf_file:
                    pdf_file_exist = False
                else:
                    pdf_file_exist = True
                    
                data = {
                        "id": res.id,
                        "model_name": res.model_name,
                        "report_number": res.report_number,
                        "issue_date": str(res.issue_date),
                        "contact_number": res.contact_number, 
                        "country_of_origin": res.country_of_origin,
                        "lab_name": res.lab_name,
                        "manufacturer_name": res.manufacturer_name,
                        "pdf_file_exist": pdf_file_exist,
                        "pdf_file": res.id,
                        "user_id": res.user_id

                    }
                json_response = json.dumps(data)
                response = Response(json_response,content_type='application/json')
                return response,200


# Fetch Roles
@app.route('/roles', methods=['GET'])
@jwt_required()
@cross_origin()
def fetch_roles():
    jti = get_jwt()["jti"]
    # print(jti)
    
    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    current_user = get_jwt_identity()
    if current_user["role"] == 1 or current_user["role"] == 2:
        try:
            res = db.session.query(role).all()
        except:
            db.session.remove()
            db.session.close()
            db.session.remove()
            res = db.session.query(role).all()
            
        db.session.close()
        temp = []
        for rol in res:
            data = {
                "id": rol.id,
                "role": rol.name,
            }
            temp.append(data)

        
        return jsonify({
            "data":temp,
        }),200
    else:
        return jsonify({
             "message": "You don\'t have access"
        }),400


# # Functionality: signup
@app.route('/add-user', methods=['POST'])
def signup():
  
    if session["role"] == 2:
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            name = request.form['name']
            role = int(request.form['role'])

            try:
                res = db.session.query(user).filter_by(email = email).first()
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                res = db.session.query(user).filter_by(email = email).first()
            db.session.close()
            if res is None: 
                if password == confirm_password:
                    password = generate_password_hash(password)
                    # add encrpyted password
                    common_user=  user(email,username,name,password,role)
                    db.session.add(common_user)
                    db.session.commit()
                    db.session.close()
                    return redirect(url_for("users_"))

                else:
                    flash("Password doesn't matched","danger")
                    return redirect(url_for("users_"))
            else:
                flash("Email already exist","danger")
                return redirect(url_for("users_"))
    else:
        return redirect(url_for("index"))
            
        
    

# Add user - Done
# Update user - done
# View users - done


# Functionality: signin
@app.route('/signin', methods=['POST'])
@cross_origin()
def signin():
   
        # if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']  
            # passing data email and password to login api 
            try:
                res = db.session.query(user).filter_by(email = email).first()
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                res = db.session.query(user).filter_by(email = email).first()
            # checking in the database if the email and pass is present or not 
            db.session.close()
            if res is None: 
                # If not then returning message with the 401 unauthorized status code  
                return jsonify({
                     "message": "Email or password is invalid"
                }),401
            
            if  check_password_hash(res.password,password):
                
                try:

                    access_token = create_access_token({"id":res.id,
                                                        "role": res.role,
                                                        "email":res.email,
                                                        "username": res.username,
                                                        "name": res.name})
               

                    response = jsonify({"msg": "login successful","token": access_token})
                    
                    return response,200

                except Exception as e:
                    return {
                        "error": "Something went wrong",
                        "message": str(e)
                    }, 500
    

            return jsonify({
                     "message": "Email or password is invalid"
            }),401
        
    

@app.route("/logout", methods=["DELETE"])
@cross_origin()
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    # print(jti)

    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    
    blacklist.add(jti)
    return jsonify(msg="logout successful"),200

@app.route('/download-report/<entry_id>', methods=['GET'])
@cross_origin()
@jwt_required()
def download_report(entry_id):
    jti = get_jwt()["jti"]
    # print(jti)

    if check_token_in_blacklist(jti):
        return jsonify(msg="Token expired"),401
    
    try:
        upload = db.session.query(entry).filter_by(id=entry_id).first()
    except:
        db.session.remove()
        db.session.close()
        db.session.remove()
        upload = db.session.query(entry).filter_by(id=entry_id).first()
    if upload is None:
        return redirect(url_for("index"))
    else:
        return send_file(BytesIO(upload.pdf_file), download_name="report.pdf", as_attachment=True )
  

@app.route('/download/<entry_id>', methods=['GET'])
def download(entry_id):
  
        try:
            upload = db.session.query(entry).filter_by(id=entry_id).first()
        except Exception as e:
            db.session.remove()
            db.session.close()
            db.session.remove()
            upload = db.session.query(entry).filter_by(id=entry_id).first()

        if upload is None:
            # report not found page load here

            return redirect(url_for("index"))
        else:
            pdf_file = upload.pdf_file
            try:
                response = Response(pdf_file, content_type='application/pdf')
                response.headers['Content-Disposition'] = 'inline; filename=report.pdf'
                response.headers['Content-Length'] = len(pdf_file)
                print(len(pdf_file))
            except Exception as e:
                print("Error:", e)

            return response




@app.route("/dashboard", methods=["GET"])
def dashboard():

        if 'email' in session:
            try:
                text=request.args.get('text')
            except:
                text=""
            try:
                page = request.args.get('page')
                page= int(page)
                
            except:
                page = request.args.get('page',1,type=int)
            
            if text=="" or not text:
                # print("text:",text)
                try:
                    pagination = db.session.query(entry).paginate(page, per_page=10)
                except:
                    db.session.remove()
                    db.session.close()
                    db.session.remove()
                    pagination = db.session.query(entry).paginate(page, per_page=10)
                    
            else:
                # print("text-2nd:",text)
                search = "%{}%".format(text)
                try:
                    pagination = db.session.query(entry).filter(entry.model_name.like(search)).paginate(page, per_page=10)
                except:
                    db.session.remove()
                    db.session.close()
                    db.session.remove()
                    pagination = db.session.query(entry).filter(entry.model_name.like(search)).paginate(page, per_page=10)
            db.session.remove()
            db.session.close()
            # Pass number of pages 
            
            return render_template("index.html",pagination=pagination)
        else:
            return redirect(url_for("index"))

# Users

@app.route("/users", methods=["GET"])
def users_():
    
        if 'email' in session:
            try:
                page = request.args.get('page')
                page= int(page)
                
            except:
                page = request.args.get('page',1,type=int)
            try:
                pagination = db.session.query(user).paginate(page, per_page=10)
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                pagination = db.session.query(user).paginate(page, per_page=10)

            # Pass number of pages 
            
            return render_template("users.html",pagination=pagination)
        else:
            return redirect(url_for("index"))

   

@app.route("/",methods=["GET","POST"])
def index():
    if request.method=="POST":
            email = request.form["email"]
            password = request.form["password"]
            try:
                res = db.session.query(user).filter_by(email = email).first()
            except:
                db.session.remove()
                db.session.close()
                db.session.remove()
                res = db.session.query(user).filter_by(email = email).first()

            db.session.close()
            if res is None: 
                flash("Email or password is invalid","danger")
                return render_template("signin.html",email = email,password=password)
            
            if  check_password_hash(res.password,password):
                
                try:

                    session['id'] = res.id
                    session['email'] = res.email
                    session['role'] = res.role
                    session['username']=res.username
                    session['name'] = res.name

                    return redirect(url_for("dashboard"))

                except Exception as e:
                    flash("Email or password is invalid","danger")
                    return render_template("signin.html",email = email,password=password)
    

            flash("Email or password is invalid","danger")
            return render_template("signin.html",email = email,password=password)
    else:
        if 'email' in session:
            return redirect(url_for("dashboard"))
        else:
            return render_template("signin.html",email="",password="")
        
@app.route("/logout",methods=["GET"])
def logout_user():
    session.clear()
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host="0.0.0.0")
    # app.run(debug=True)
