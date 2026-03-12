from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from datetime import datetime
from flask import send_from_directory
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {"pdf"}
UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100),nullable=False)
    number = db.Column(db.String(15))
    role = db.Column(db.String(20))
    approved = db.Column(db.Boolean, default=False)
    cgpa = db.Column(db.Float)
    course = db.Column(db.String(50))
    branch = db.Column(db.String(50))
    skills = db.Column(db.String(200))
    resume = db.Column(db.String(200))


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    job_role = db.Column(db.String(100))
    job_description = db.Column(db.Text)
    eligibility = db.Column(db.String(200))
    requirements = db.Column(db.String(200))
    openings = db.Column(db.Integer)
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(20),default='pending') 
    company = db.relationship("User", backref="drives")

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"))
    status = db.Column(db.String(20), default='applied')   
    date = db.Column(db.String(50))
    drive = db.relationship("Drive")
    student = db.relationship("User")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        user = User.query.filter_by(email=email, password=password, role=role).first()

        if not role:
            flash("Please select role", "warning")
            return redirect(url_for("login"))
        
        if user: 
            session["user_id"] = user.id
            session["role"] = role

            if role == "admin":
                return redirect(url_for("admin"))
            
            elif role == "company":

                if(not user.approved):
                    flash("Company waiting for admin approval", "warning")
                    return redirect(url_for("login"))

                return redirect(url_for("chome"))
            
            else:
                return redirect(url_for("home"))

        else:
            flash("Invalid email or password","danger")
            return render_template("login.html",email=email)
    return render_template("login.html")

@app.route("/apply/<int:drive_id>")
def apply(drive_id):

    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "student":
        return redirect(url_for("home"))

    student_id = session["user_id"]
    drive = Drive.query.get(drive_id)

    if (not drive):
        flash("Drive not found", "warning")
        return redirect(url_for("home"))
    
    if drive.status != "approved":
        flash("Drive not available", "warning")
        return redirect(url_for("home"))

    existing = Application.query.filter_by(
        student_id=student_id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already Applied", "warning")
        return redirect(url_for("home"))

    application = Application(
        student_id=student_id,
        drive_id=drive_id,
        status="applied",
        date=datetime.now().strftime("%Y-%m-%d")
    )
    db.session.add(application)
    db.session.commit()
    flash("Application Submitted Successfully", "success")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role")
        approved = True if role == "student" else False
        user = User(
            name=request.form.get("name"),
            email=request.form.get("email"),
            password=request.form.get("password"),
            number=request.form.get("number"),
            role=role,
            approved=approved
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "student":
        return redirect(url_for("login"))
    
    drives = Drive.query.filter_by(status="approved").all()
    return render_template("home.html",drives=drives)


@app.route("/chome")
def chome():

    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "company":
        return redirect(url_for("login"))
    
    company_id = session["user_id"]
    drives = Drive.query.filter_by(company_id=company_id).all()

    applications = Application.query.join(Drive).filter(
        Drive.company_id == company_id
    ).all()

    return render_template("chome.html",drives=drives,applications=applications)


@app.route("/create_drive", methods=["POST"])
def create_drive():

    if session.get("role") != "company":
        return redirect(url_for("home"))

    drive = Drive(
        company_id=session["user_id"],
        job_role=request.form.get("job_role"),
        eligibility=request.form.get("eligibility"),
        requirements=request.form.get("requirements"),
        openings=request.form.get("openings"),
        deadline="N/A",
        status="pending"
    )

    db.session.add(drive)
    db.session.commit()

    flash("Drive Posted Successfully", "success")
    return redirect(url_for("chome"))

@app.route("/update_status/<int:app_id>/<status>")
def update_status(app_id, status):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "company":
        return redirect(url_for("login"))

    application = Application.query.get(app_id)

    if not application:
        flash("Application not found", "danger")
        return redirect(url_for("chome"))

    application.status = status
    db.session.commit()

    flash("Application status updated", "success")
    return redirect(url_for("chome"))

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    students = User.query.filter_by(role="student").count()
    companies = User.query.filter_by(role="company", approved=True).count()
    drives = Drive.query.filter_by(status="approved").count()
    applications = Application.query.count()

    pending_companies = User.query.filter_by(
        role="company",
        approved=False
    ).all()

    return render_template(
        "admin.html",
        students=students,
        companies=companies,
        drives=drives,
        applications=applications,
        pending_companies=pending_companies
        )


@app.route("/admin/companies")
def admin_companies():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    pending = User.query.filter_by(role="company", approved=False).all()
    approved = User.query.filter_by(role="company", approved=True).all()
    return render_templaxmcmvlDKVMlZ ,m te(
        "admin_companies.html",
        pending_companies=pending,
        approved_companies=approved
    )


@app.route("/approve_company/<int:id>")
def approve_company(id):
    company = User.query.get(id)
    company.approved = True
    db.session.commit()
    flash("Company Approved", "success")
    return redirect(url_for("admin_companies"))

@app.route("/delete_company/<int:id>")
def delete_company(id):
    company = User.query.get(id)
    db.session.delete(company)
    db.session.commit()
    flash("Company Removed", "danger")
    return redirect(url_for("admin_companies"))


@app.route("/admin/drives")
def admin_drives():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    drives = Drive.query.options(joinedload(Drive.company)).filter_by(status="pending").all()
    return render_template("admin_drives.html", drives=drives)

@app.route("/download_resume/<filename>")
def download_resume(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )

@app.route("/search")
def search():
    q = request.args.get("q")
    drives = Drive.query.filter(
        Drive.job_role.contains(q)
    ).all()
    return render_template(
        "home.html",
        drives=drives
    )

@app.route("/approve_drive/<int:id>")
def approve_drive(id):
    drive = Drive.query.get(id)
    drive.status = "approved"
    db.session.commit()
    flash("Drive Approved","success")
    return redirect(url_for("admin_drives"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "student":
        return redirect(url_for("login"))
    
    student_id = session["user_id"]
    applications = Application.query.filter_by(student_id=student_id).all()
    offers = Application.query.filter_by(student_id=student_id, status="selected").count()
    interviews = Application.query.filter_by(student_id=student_id, status="shortlisted").count()
    applied = Application.query.filter_by(student_id=student_id).count()
    drives = Drive.query.filter_by(status="approved").count()

    return render_template(
        "dashboard.html", 
        applications=applications,
        offers=offers,
        interviews=interviews,
        applied=applied,
        drives=drives
        )

@app.route("/profile", methods=["GET","POST"])
def profile():

    if "user_id" in session:
        user = User.query.get(session["user_id"])
    else:
        user = User.query.first()
    
    if session.get("role") != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        user.name = request.form.get("name")
        user.email = request.form.get("email")
        user.number = request.form.get("number")
        user.cgpa = request.form.get("cgpa")
        user.course = request.form.get("course")
        user.branch = request.form.get("branch")
        user.skills = request.form.get("skills")
        resume = request.files.get("resume")

        if resume and resume.filename != "":
            if allowed_file(resume.filename):
                filename = secure_filename(f"{user.id}_resume.pdf")
                filepath = os.path.join(app.config["UPLOAD_FOLDER"],filename)
                resume.save(filepath)
                user.resume = filename

        db.session.commit()
        return redirect(url_for("profile"))
    return render_template("profile.html",user=user)

@app.route("/cprofile")
def cprofile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("role") != "company":
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    return render_template("cprofile.html",user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin = User(
                name="Admin",
                email="admin@portal.com",
                password="admin123",
                number="0000000000",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True, use_reloader=False)