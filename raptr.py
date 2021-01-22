import os
from datetime import date,datetime
from flask import Flask, escape, request,render_template,url_for,flash,redirect,send_from_directory
from forms import RegistrationForm, LoginForm,summary_url,get_summary
from werkzeug.utils import secure_filename
from extract_text import convert_pdf_to_txt
from summarizer import generate_summary

#SQL Database

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt 
from flask_login import LoginManager,UserMixin,login_user,login_required,current_user,logout_user

 
#URL Summarization

from spacy_summarizer import text_summarizer
from gensim.summarization import summarize
import time
import spacy
nlp = spacy.load('en_core_web_sm')

# Web Scraping Pkg
from bs4 import BeautifulSoup
# from urllib.request import urlopen
import urllib.request as ur


#Global variables

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
ALLOWED_EXTENSIONS = {'pdf','txt'}

file_g =""

app = Flask(__name__)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config["FILE_UPLOADS"] = UPLOAD_FOLDER
app.config["FILE_DOWNLOADS"] = DOWNLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view ='login2'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    documents = db.relationship('Documents', backref = "author", lazy =True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Documents(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}', '{self.content}', '{self.summary}')"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_text(url):
	page = ur.urlopen(url)
	soup = BeautifulSoup(page)
	fetched_text = ' '.join(map(lambda p:p.text,soup.find_all('p')))
	return fetched_text


document = [
    {

    }
]


@app.route('/raptr')
@app.route('/home',methods =['GET','POST'])
@login_required
def home():
    form = summary_url()
    return render_template('home.html',form = form)


@app.route('/documents', methods = ['GET', 'POST'])
@login_required
def documents():
    docs = Documents.query.all()
    return render_template('documents.html', documents = docs)   

@app.route('/summary/<int:post_id>', methods = ['GET', 'POST'] )
@login_required
def summary(post_id):
    post = Documents.query.get_or_404(post_id)
    return render_template('summary.html', post = post)


    '''
    filepath = r'D:/College/Project/Raptr_Flask\downloads\DeepFaceDrawing.pdf.txt'
    with open(filepath, "r",encoding='utf-8' ) as f:
        content = f.read()
    
    return render_template('summary.html', document = doc , summary = content)

    '''
    #s_file = documents[1]('title')
    #base = os.path.splitext(filename)[0]
    #file = os.rename(filename, base + '.pdf.txt')
    #with open(file, "r",encoding='utf-8' ) as f:
        #content = f.read()

    #return render_template('summary.html', summary = content , filename = s_file, form = form)

@app.route("/<int:post_id>/delete", methods=["POST"])
@login_required
def delete(post_id):
    post = Documents.query.get_or_404(post_id)
    if post.author == current_user:
        db.session.delete(post)
        db.session.commit()
        flash(f'Document deleted!','Success')
        return redirect(url_for('documents'))


@app.route('/url_summary',methods=['GET','POST'])
@login_required
def url_summary():
    form = summary_url()
    if request.method == 'POST':
        raw_url = form.url.data
        rawtext = get_text(raw_url)
        final_summary = text_summarizer(rawtext)
    return render_template('home.html',final_summary = final_summary, form = form)


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/upload', methods =['GET','POST'])
@login_required
def upload():
    if request.method == 'POST':

        if 'file' not in request.files:
            print('No file attached ')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            print('No file selected')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['FILE_UPLOADS'], filename))
            process_file(os.path.join(app.config['FILE_UPLOADS'],filename),filename)
            add_to_list(filename)
           #return redirect(url_for('download_file', filename=filename))

    return render_template('upload.html',title = 'Upload')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file(path,filename):
    text = convert_pdf_to_txt(path)
    filepath = 'D:/College/Project/Raptr_Flask/downloads/' + filename +'.txt'
    with open(filepath, 'w',encoding='utf-8') as t:
        t.write(text)
        t.close()
    document = Documents(title = filename, date_posted = date.today(), content = "", summary = text, user_id = current_user.get_id())
    db.session.add(document)
    db.session.commit()
    flash(f'Document uploaded and summarized    ','Success')

def add_to_list(filename):
    document.append({'title':filename,'date':date.today()})


@app.route('/downloads/<filename>', )
def download_file(filename):
    return send_from_directory(app.config['FILE_DOWNLOADS'], filename, as_attachment=True)


@app.route('/')
@app.route('/login2', methods = ['GET', 'POST'])
def login2():
    form = LoginForm()
    if form.validate_on_submit():
        user =User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessful','danger')
    return render_template('login2.html', title = 'Login', form = form)


@app.route('/register2', methods = ['GET', 'POST'])
def register2():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_pwd )
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Please Log In', 'success')
        return redirect(url_for('login2'))
    return render_template('register2.html', title = 'Register', form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login2'))



if __name__ == '__main__':
    app.run(debug=True)






