from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from functools import wraps
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from flask_wtf import FlaskForm, RecaptchaField
from wtforms.widgets import TextArea
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep

app=Flask(__name__)
app.secret_key= "Tweet_Parse"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root" 
app.config["MYSQL_PASSWORD"] = "rycb4r3_123" 
app.config["MYSQL_DB"] = "Tweet_Parse_App"
app.config["MYSQL_CURSORCLASS"] = "DictCursor" 
mysql = MySQL(app) 

class RegisterForm(Form):
    name = StringField("Name and Surname",validators=[validators.Length(min = 4,max = 25)]) 
    user = StringField("Username",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email Adress",validators=[validators.Email(message="Please Set A Email Adress")]) 
    password = PasswordField("Password",validators=[
        validators.DataRequired(message="Please Set a Password."),
        validators.EqualTo(fieldname = "confirm",message = "Your Passwords Does Not Match..")
    ])

class TweetForm(Form):
    Username = StringField("Username",validators=[validators.DataRequired(message="Set A Username")])
    Password = PasswordField("Password",validators=[validators.DataRequired(message="Set A Password")])
    Post = TextAreaField("Add Tweet",widget=TextArea(),validators=[validators.Length(min=1,max=999999,message="You Cannot Write More Less 280 Characters")])


@app.route("/",methods = ["GET","POST"])
def index():
    form = TweetForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.Username.data
        password = form.Password.data
        post = form.Post.data
        options = Options()
        options.add_argument('-headless')
        
        enter_tweet = post
        tweet_parse = enter_tweet.split(" ")
        tweet_parse_lenght = len(tweet_parse)
        tweet = ""
        browser = webdriver.Firefox(options=options)
        wait = WebDriverWait(browser, timeout=10)
        browser.get("https://twitter.com/login")
        
        kullanici_adi = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, 
        "/html/body/div[1]/div[2]/div/div/div[1]/form/fieldset/div[1]/input"))).send_keys(username)
        sleep(0.5)
        parola = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
         "js-password-field"))).send_keys(password)
        login_button = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH,
         "/html/body/div[1]/div[2]/div/div/div[1]/form/div[2]/button")))
        login_button.click()
        tweet_box = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID,
         "tweet-box-home-timeline")))

        for i in range(0,tweet_parse_lenght):
            tweet_parsed = tweet_parse[i]
            if len(tweet + " " +tweet_parsed) <= 276:
                tweet = tweet + " " +tweet_parsed
                tweet_box.click()
            else:
                tweet_box.send_keys(tweet + "...")
                entry_tweet = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH,
         "/html/body/div[2]/div[2]/div/div[2]/div[2]/div/form/div[3]/div[2]/button/span[1]")))
                entry_tweet.click()
                tweet = ""
        tweet_box.click()
        tweet_box.send_keys(tweet + "...")
        entry_tweet = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH,
         "/html/body/div[2]/div[2]/div/div[2]/div[2]/div/form/div[3]/div[2]/button/span[1]")))
        entry_tweet.click()
        tweet = ""

        sleep(5)
        browser.close()
        flash("Tweet Sent Successfully","success")
        return redirect(url_for("index"))
    else:
        return render_template("index.html",form = form)

@app.route("/register",methods = ["GET","POST"]) 
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate(): 
        name = form.name.data
        user = form.user.data 
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,user,email,password) VALUES(%s,%s,%s,%s)" 
        cursor.execute(sorgu,(name,user,email,password)) 
        mysql.connection.commit() 
        cursor.close()
        flash("Succesfull","success")
        return redirect(url_for("login"))
    else:  
        return render_template("register.html",form = form)

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        user_id  = form.user_id.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where user_id = %s"
        cursor.execute(sorgu,(user_id,))
        result = cursor.execute(sorgu,(user_id,))
        
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Login Successful","success")
                session["logged_in"] = True
                user_name = data["name"]
                session["name"] = user_name
                session["user_id"] = user_id
                return redirect(url_for("index"))
            else:
                flash("Password is Wrong","danger")
        else:
            flash("No Such User Can Be Found","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form=form)


if __name__ == "__main__":
    app.run(debug=True)
