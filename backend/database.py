from flask import Flask,render_template,request,url_for,redirect,Response,flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_sqlalchemy import SQLAlchemy




username = "hussain"
password = "mv6cQY-]B8L-"
host = "68.178.153.99" 
database = "xtreme_entries"

database_file = f'mysql://{username}:{password}@{host}/{database}'


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
app.config['JSON_SORT_KEYS'] = False
db = SQLAlchemy(app)
app.secret_key = "saso_microsite_skey"

# Secret Key

token_key = URLSafeTimedSerializer("BraggingRights")
# File Extension
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
