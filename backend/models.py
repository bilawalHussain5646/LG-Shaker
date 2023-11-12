
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

# User Role table
class role(db.Model):
    id = db.Column(db.INTEGER, primary_key=True,nullable=False)
    role = db.Column(db.String(250),nullable=False)
    
    def __init__(self, role):
        self.role = role


# Users of the website
class user(db.Model):
    id = db.Column(db.INTEGER, primary_key=True,nullable=False)
    email = db.Column(db.String(250),nullable=False)
    username = db.Column(db.String(250),nullable=False)
    name = db.Column(db.String(250),nullable=False)
    password = db.Column(db.String(250),nullable=False)
    role = db.Column(db.Integer, db.ForeignKey('role.id'),nullable=False)

    def __init__(self, email,username,name,password,role):
        self.email = email
        self.username=username
        self.name = name
        self.password = generate_password_hash(password)
        self.role = role

        def encrypt_password(self, password):
            """Encrypt password"""
            return generate_password_hash(password)

        def login(self, email, password):
            """Login a user"""
            user = self.get_by_email(email)
            if not user or not check_password_hash(user["password"], password):
                return
            user.pop("password")
            return user
# Entry table
class entry(db.Model):
    id = db.Column(db.INTEGER, primary_key=True,nullable=False)
    model_name = db.Column(db.String(250),nullable=False)
    report_number = db.Column(db.String(250),nullable=False)
    issue_date = db.Column(db.Date(),nullable=False)
    contact_number = db.Column(db.String(250),nullable=False)
    country_of_origin = db.Column(db.String(250),nullable=False)
    lab_name = db.Column(db.String(250),nullable=False)
    manufacturer_name = db.Column(db.String(250),nullable=False)      
    pdf_file = db.Column(db.LargeBinary,nullable=False) 
    qr_code = db.Column(db.LargeBinary,nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)

    def __init__(self, model_name,report_number,issue_date,contact_number,country_of_origin,lab_name,manufacturer_name,pdf_file,user_id,qr_code):
        self.model_name = model_name
        self.report_number = report_number
        self.issue_date=issue_date
        self.contact_number = contact_number
        self.country_of_origin = country_of_origin
        self.lab_name = lab_name
        self.manufacturer_name = manufacturer_name
        self.pdf_file = pdf_file
        self.user_id = user_id
        self.qr_code = qr_code



        


