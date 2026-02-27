from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from reportlab.pdfgen import canvas

app = Flask(__name__)
DB = "database.db"

# -------------------------
# Database Helper Functions
# -------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    class TEXT,
                    guardian_mobile TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    month TEXT,
                    amount INTEGER,
                    status TEXT,
                    trxid TEXT
                )''')
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Initialize database
init_db()

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]
        student = query_db("SELECT * FROM students WHERE guardian_mobile=?", [mobile], one=True)
        if student:
            return redirect(f"/dashboard/{student[0]}")
        else:
            return "Invalid mobile number"
    return render_template("login.html")

@app.route("/dashboard/<int:student_id>")
def dashboard(student_id):
    student = query_db("SELECT * FROM students WHERE id=?", [student_id], one=True)
    fees = query_db("SELECT * FROM fees WHERE student_id=?", [student_id])
    return render_template("dashboard.html", student=student, fees=fees)

@app.route("/pay/<int:fee_id>", methods=["GET", "POST"])
def pay(fee_id):
    fee = query_db("SELECT * FROM fees WHERE id=?", [fee_id], one=True)
    if request.method == "POST":
        trxid = request.form["trxid"]
        query_db("UPDATE fees SET status='Paid', trxid=? WHERE id=?", [trxid, fee_id])
        return redirect(f"/receipt/{fee_id}")
    return render_template("pay.html", fee=fee)

@app.route("/receipt/<int:fee_id>")
def receipt(fee_id):
    fee = query_db("SELECT * FROM fees WHERE id=?", [fee_id], one=True)
    student = query_db("SELECT * FROM students WHERE id=?", [fee[1]], one=True)

    file_name = f"receipt_{fee_id}.pdf"
    c = canvas.Canvas(file_name)
    c.drawString(100, 750, "Madrasa Fee Receipt")
    c.drawString(100, 720, f"Student: {student[1]}")
    c.drawString(100, 700, f"Class: {student[2]}")
    c.drawString(100, 680, f"Month: {fee[2]}")
    c.drawString(100, 660, f"Amount: {fee[3]} Taka")
    c.drawString(100, 640, f"Status: {fee[4]}")
    c.drawString(100, 620, f"Transaction ID: {fee[5]}")
    c.save()

    return send_file(file_name, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
