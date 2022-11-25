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


COS_ENDPOINT="https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID="OVhg-B9OTj0Iwjjo1iioS9k-qKY6wahPUGzElt8at-EX"
COS_INSTANCE_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/0644cd8c36ef4b70aed577434e50bbc4:b5d94bd0-cad9-4822-9c64-f953cb105e72::"


cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

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

@app.route('/ManageStock', methods = ['POST', "GET"])
def ManageStock():
    try:
        if not session.get("USERID"):
            return redirect("/login")
        userid = session.get("USERID")
        query = f"select * from stock where retailerid = {userid}"
        stmt = ibm_db.prepare(conn, query)
        ibm_db.execute(stmt)
        stocks = []
        available = []
        while True:
            obj = ibm_db.fetch_tuple(stmt)
            if obj :
                stocks.append(obj)
                if int(obj[7]) > 300 :
                    available.append(1)
                elif int(obj[7]) > 50:
                    available.append(0)
                else:
                    available.append(-1)
            else:
                break
        # files = cos.Bucket('imsfr').objects.all()
        # files_names = []
        # for file in files:
        #     files_names.append(file.key)
        #     # print(file)
        #     # print("Item: {0} ({1} bytes).".format(file.key, file.size))
        return render_template('ManageStock.html',stocks = zip(stocks,available))
        
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
        return render_template('Dashboard.html')
    except Exception as e:
        print("Unable to retrieve bucket contents: {0}".format(e))
        return render_template('Dashboard.html')

@app.route('/addStock',methods=['POST'])
def upload():
    if request.method == 'POST':
        sname = request.form.get("addproductName")
        mdate = request.form.get("manDate")
        edate = request.form.get("expDate")
        mrp = request.form.get("mrp")
        qty = request.form.get("qty")
    if sname and mdate and edate and mrp and qty:
        if not session.get("USERID"):
            return redirect("/login")
        userid = session.get("USERID")
        query = f"select max(ID)+1 as SID from STOCK where RETAILERID = {userid}"
        stmt = ibm_db.prepare(conn, query)
        ibm_db.execute(stmt)
        obj = ibm_db.fetch_assoc(stmt)
        try:
            StockID=int(obj['SID'])
        except:
            StockID = 1001
        
        f = request.files['addProductImage']
        Stock_img_name=f"img_{userid}_{StockID}"
        try:
            part_size = 1024 * 1024 * 5

            file_threshold = 1024 * 1024 * 15

            transfer_config = ibm_boto3.s3.transfer.TransferConfig(
                    multipart_threshold=file_threshold,
                    multipart_chunksize=part_size
                )

            content = f.read()
            cos.Object('imsfr', Stock_img_name).upload_fileobj(
                        Fileobj=io.BytesIO(content),
                        Config=transfer_config
                    )

        except ClientError as be:
                # print("CLIENT ERROR: {0}\n".format(be))
                return redirect(url_for('login'))

        except Exception as e:
                # print("Unable to complete multi-part upload: {0}".format(e))
                return redirect(url_for('login'))

        query = f"insert into STOCK values({StockID},'{sname}','{mdate}','{edate}',{mrp},'{Stock_img_name}',{userid},{qty})"
        stmt = ibm_db.prepare(conn, query)
        ibm_db.execute(stmt)
        return redirect(url_for('ManageStock'))
        

        try:
            query = f"select * from stock where retailerid = {userid}"
            stmt = ibm_db.prepare(conn, query)
            ibm_db.execute(stmt)
            obj = ibm_db.fetch_assoc(stmt)
            print(obj)
            files = cos.Bucket('imsfr').objects.all()
            files_names = []
            for file in files:
                files_names.append(file.key)
                # print(file)
                # print("Item: {0} ({1} bytes).".format(file.key, file.size))
            return render_template('ManageStock.html',files=files_names)
            
        except ClientError as be:
            # print("CLIENT ERROR: {0}\n".format(be))
            return render_template('login.html')
        except Exception as e:
            # print("Unable to retrieve bucket contents: {0}".format(e))
            return render_template('login.html')

@app.route('/getStockDetails',methods=['POST'])
def getDetails():
    if not session.get("USERID"):
        return redirect("/login")
    userid = session.get("USERID")
    if request.method == 'POST':
        pid = request.form.get("pid")
        query = f"select * from stock where ID = {pid} and retailerid = {userid}"
        stmt = ibm_db.prepare(conn, query)
        ibm_db.execute(stmt)
        stock = ibm_db.fetch_assoc(stmt)
        print(stock)
        return redirect(url_for('ManageStock'),getStock = stock)


if __name__ == '__main__':
    app.run(debug=True)