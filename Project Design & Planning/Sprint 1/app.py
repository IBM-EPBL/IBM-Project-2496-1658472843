from asyncio.windows_events import NULL
import base64
from collections import UserDict
import tkinter  as tk 
from tkinter import * 
import io
from PIL import Image, ImageTk
from threading import activeCount
from turtle import st
from flask import Flask,render_template,request, session, redirect,url_for
import ibm_db
import re
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import PIL
import ibm_boto3
from ibm_botocore.client import Config, ClientError

app = Flask(__name__)
app.secret_key = 'a'
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=b0aebb68-94fa-46ec-a1fc-1c999edb6187.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=31249;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=xbh29234;PWD=Hdy6hbDtvv4SomNt;",'','')
@app.route('/')

def homer():
    return render_template('Login.html')
    
@app.route('/Dashboard', methods = ['POST', "GET"])
def login():
    if request.method == 'POST':
        userid = request.form.get("userid")
        password = request.form.get("passwd")

        if(userid!="" and password!=""):
            sql = "select CONTACT from retailer where ID = ?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, userid)
            ibm_db.execute(stmt)
            obj = ibm_db.fetch_assoc(stmt)
            try:
                passwd_contact=int(obj['CONTACT'])
                actual_contact = int(password)
            except:
                passwd_contact=0
                actual_contact = -1
            if (passwd_contact!=0) and (passwd_contact == actual_contact):
                session['USERID'] = userid
                return render_template('Dashboard.html')
    return render_template('Login.html')

@app.route('/Login', methods = ['POST', "GET"])
def signup():
    if request.method == 'POST':
        name = request.form.get("name")
        contact = request.form.get("contact")
        mailid = request.form.get("mailid")
        company = request.form.get("company")
        agency = request.form.get("agencyname")

        if(name!="" and contact !="" and mailid !="" and company != "" and agency !=""):
            stmt = ibm_db.prepare(conn, 'select max(ID)+1 as ID from retailer')
            ibm_db.execute(stmt)
            obj = ibm_db.fetch_assoc(stmt)
            nextID = 0
            print(obj)
            try:
                nextID = int(obj['ID'])
            except:
                nextID = 1001
            sql = f"insert into Retailer values({nextID},'{name}',{contact},'{mailid}','{company}','{agency}')"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.execute(stmt)
            return render_template('login.html',msg = 'Account created Successfully')
    return render_template('Login.html')



if __name__ == '__main__':
    app.run(debug=True)