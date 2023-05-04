from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
app = Flask(__name__)
#Kullanıcı giriş dekoratörü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session :
          return f(*args, **kwargs)
        else :
          flash("Bu sayfayı görüntülemek için giriş yapın","danger")
          redirect(url_for("login"))
    return decorated_function
#kullanıcı kayıt formu
class RegisterForm(Form): #5 alan olmalı
     name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25)])#text olarak 
     username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
     email = StringField("E-mail Adresi",validators=[validators.Email(message="Lütfen Geçerli Bir Mail Adresi Giriniz.")])
     password = PasswordField("Parola",validators=[validators.data_required(message="Lütfen Parola Giriniz"),validators.equal_to(fieldname="confirm",message="Parolanız Uyuşmuyor!")])
     confirm = PasswordField("Parola Doğrula")
class LoginForm(Form):
     username = StringField("Kullanıcı Adı")
     password = PasswordField("Parola")
class FileForm(Form):
     title = StringField("Dosya Başlığı",validators=[validators.length(min=5,max=100)])
     content = TextAreaField("Dosya İçeriği",validators = [validators.length(min=10)])
class ResumeForm(Form):
     text_input = StringField('Özgeçmiş girişi', validators=[DataRequired()])
     submit_button = SubmitField('Gönder')


app.secret_key = "veri" #uydurduk
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "veri"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql =  MySQL(app)
@app.route("/")
def index():
     return render_template("index.html")
@app.route("/about")
def about():
     return render_template("about.html")
@app.route("/files")
def files():
     cursor = mysql.connection.cursor()
     sorgu = "SELECT * FROM files"
     result = cursor.execute(sorgu)
     if result > 0 :
          files = cursor.fetchall()
          return render_template("files.html",files = files)
     else :
          return render_template("files.html")
@app.route("/dashboard")
@login_required
def dashboard():
     cursor = mysql.connection.cursor()
     sorgu = "SELECT * FROM files WHERE author = %s"
     result = cursor.execute(sorgu,(session["username"],))
     if result > 0:
          files = cursor.fetchall()
          return render_template("dashboard.html",files = files)
          
     else :
          render_template("dashboard.html")
     return render_template("dashboard.html")
@app.route("/register",methods = ["GET","POST"])
def register():
     form = RegisterForm(request.form)
     if request.method == "POST" and form.validate():
          name = form.name.data
          username = form.username.data
          email = form.email.data
          password =sha256_crypt.encrypt(form.password.data)
          cursor = mysql.connection.cursor()
          sorgu = "Insert into users(name,email,username,password) VALUES(%s, %s, %s, %s)"
          cursor.execute(sorgu, (name,email,username,password))
          mysql.connection.commit()
          cursor.close()
          flash("Başarıyla Kayıt Oldunuz","success")
          return redirect(url_for("login"))
     else:
          return render_template("register.html",form = form)
@app.route("/login",methods = ["GET","POST"])
def login():
     form = LoginForm(request.form)
     if request.method == "POST":
          username = form.username.data
          password_entered = form.password.data
          cursor = mysql.connection.cursor()
          sorgu = "Select * From users where username = %s"
          result = cursor.execute(sorgu,(username,))
          if result > 0 :
               data = cursor.fetchone()
               real_password = data["password"]
               if sha256_crypt.verify(password_entered,real_password):
                    flash("Başarıyla giriş yaptınız","success")
                    session["logged_in"]=True
                    session["username"] = username
                    return redirect(url_for("index"))
               else:
                    flash("Parolanızı yanlış girdiniz.","danger")
                    return redirect(url_for("login"))
          else:
               flash("Böyle bir kullanıcı bulunmuyor","danger")
               return redirect(url_for("login"))
          
     return render_template("login.html",form = form)
@app.route("/logout")
def logout():
     session.clear()
     return redirect(url_for("index"))
@app.route("/addfile",methods = ["GET","POST"])
def addfile():
     form = FileForm(request.form)
     if request.method == "POST" and form.validate():
          title = form.title.data
          content = form.content.data
          cursor = mysql.connection.cursor()
          sorgu = "INSERT INTO files(title,author,content) VALUES(%s,%s,%s)"
          cursor.execute(sorgu,(title,session["username"],content))
          mysql.connection.commit()
          cursor.close()
          flash("Dosya başarıyla eklendi","success")
          return redirect(url_for("dashboard"))
     return render_template("addfile.html",form = form)
# DETAY SAYFASI
@app.route("/file/<string:id>")
def file(id):
     cursor = mysql.connection.cursor()
     sorgu = "SELECT * FROM files where id = %s"
     result = cursor.execute(sorgu,(id,))
     if result > 0 :
           file = cursor.fetchone()
           return render_template("file.html",file = file)
     else:
          return render_template("file.html")
     
     
#Dosya Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
     cursor = mysql.connection.cursor()
     sorgu = "SELECT * FROM files WHERE author = %s AND id = %s"
     result = cursor.execute(sorgu,(session["username"],id))
     if result > 0 :
          sorgu2 = "DELETE FROM files where id = %s"
          cursor.execute(sorgu2,(id,))
          mysql.connection.commit()
          return redirect(url_for("dashboard"))
     else:
          flash("Bu işleme yetkiniz yok","danger")
          return redirect(url_for("index"))

@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
     if request.method ==  "GET" :
          cursor = mysql.connection.cursor()
          sorgu3 = "SELECT * FROM files WHERE id = %s and author = %s"
          result = cursor.execute(sorgu3,(id,session["username"]))
          if result == 0:
               flash("Böyle bir dosya yok veya bu işleme yetkiniz yok","danger")
               return redirect(url_for("index"))

          else :
               file = cursor.fetchone()
               form = FileForm()
               form.title.data = file["title"]
               form.content.data = file["content"]
               return render_template("update.html",form = form)
     else :
          form = FileForm(request.form)
          newTitle = form.title.data
          newContent = form.content.data
          sorgu4 = "Update files set title = %s , content = %s  where id = %s"
          cursor = mysql.connection.cursor()
          cursor.execute(sorgu4,(newTitle,newContent,id))
          mysql.connection.commit()
          flash("Dosya başarıyla güncellendi","success")
          return redirect(url_for("dashboard"))
#arama 
@app.route("/search",methods=["GET","POST"])  
def search():
     if request.method == "GET" :
          return redirect(url_for("index")) 
     else :
          keyword = request.form.get("keyword")
          cursor = mysql.connection.cursor()
          sorgu = "SELECT * FROM files where title like '%" + keyword + "%' "
          result = cursor.execute(sorgu)
          if result == 0 :
               flash("Aranan kelimeye uygun makale bulunamadı","warning")
               return redirect(url_for("files"))
          else :
               files = cursor.fetchall()
               return render_template("files.html",files = files)


@app.route("/users")
@login_required
def users():
     cursor = mysql.connection.cursor()
     sorgu = "SELECT * FROM users"
     result = cursor.execute(sorgu)
     if result > 0:
          users = cursor.fetchall()
          return render_template("users.html",users = users)
        
     else :
          return render_template("users.html")
     return render_template("users.html")
@app.route("/user/<string:id>")
def user(id):
     cursor = mysql.connection.cursor()
     sorgu = "SELECT * FROM users where id = %s"
     result = cursor.execute(sorgu,(id,))
     if result > 0 :
          user = cursor.fetchone()
          return render_template("user.html",user = user)
     else:
          return render_template("user.html")

 