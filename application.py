from flask import Flask, redirect, render_template, request, session
from datetime import date 
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

import matplotlib
import matplotlib.pyplot as plt 
import numpy as np

with sqlite3.connect("budget.db") as con:
    cur = con.cursor()
    cur.execute('''CREATE TABLE  IF NOT EXISTS users (username text, password text, cash real, user_id INTEGER PRIMARY KEY)''')
    cur.execute('''CREATE TABLE  IF NOT EXISTS budget (date text, expense_name text, expense_amount real, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    con.commit()

matplotlib.use('Agg')
plt.rcdefaults()

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
today = date.today().strftime("%m/%d/%y")

user_id = ""

@app.route('/')
def index():
    if not user_id:
        return redirect("/login")
    else:
        with sqlite3.connect("budget.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            data = cur.fetchall()
            cash = data[0][2]
            con.commit()
            cur.execute("SELECT * FROM budget WHERE user_id = ?", (user_id,))
            budget_data = cur.fetchall()
            expense_names = []
            amount = []
            if budget_data:
                print(budget_data)
                for i in budget_data:
                    expense_names.append(i[1].upper())
                    amount.append(i[2])
                total = sum(amount)
                dollar_formatted = []
                for k in amount:
                    dollar_formatted.append(("$" + str(int(k))))
                formatted_amount = []
                for j in amount:
                    formatted_amount.append(j / total * 100)
                y = np.array(formatted_amount)
                pie, text = plt.pie(y, labels = dollar_formatted)
                plt.legend(pie, expense_names, bbox_to_anchor=(1.05, 1), loc="upper left")
                plt.savefig('static/images/plot.png', transparent=True)
                plt.close()
                return render_template("index.html", cash = cash, url = 'static/images/plot.png')
            else:
                plt.pie([100], labels = ["ENTER AN EXPENSE"])
                plt.savefig('static/images/default.png', transparent=True)
                plt.close()
                return render_template("index.html", cash = cash, url = 'static/images/default.png')

@app.route('/login', methods =["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        with sqlite3.connect('budget.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                data = cur.fetchall()
                if data and username == data[0][0] and check_password_hash(data[0][1], password):
                    global user_id 
                    user_id = data[0][3]
                    return redirect("/")
                else:
                    message = "Please enter a valid username and password"
                    return render_template("login.html", message = message)
    else:
        return render_template("login.html")

@app.route('/register', methods =["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password == confirmation:
            with sqlite3.connect('budget.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, password, cash) VALUES(?, ?, ?)", (username, generate_password_hash(password, method='sha256', salt_length=16), 0))
                con.commit()
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route('/income', methods=["GET", "POST"])
def income():
    if not user_id:
        return redirect("/login")
    if request.method == "POST":
        added_income = int(request.form.get("addCash"))
        print(added_income)
        with sqlite3.connect('budget.db') as con:
            cur = con.cursor()
            print(user_id)
            cur.execute("SELECT cash FROM users WHERE user_id = ?", (user_id,))
            data = cur.fetchall()
            prev_cash = data[0][0]
            new_income = prev_cash + added_income
            cur.execute("UPDATE users SET cash = ? WHERE user_id = ?", (new_income, user_id)) 
            con.commit()
        return redirect("/")
    else:
        return render_template("income.html")

@app.route('/expense', methods=["GET", "POST"])
def expense():
    if not user_id:
        return redirect("/login")
    if request.method == "POST":
        if "show_expense" in request.form:
            print("k")
            with sqlite3.connect('budget.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM budget WHERE user_id = ?", (user_id,)) 
                rows = cur.fetchall()
                con.commit()
            return render_template("expense-table.html", rows = rows)
        elif "submit" in request.form:
            expense_name = request.form.get("expenseName").upper()
            expense_amount = int(request.form.get("expenseAmount"))
            with sqlite3.connect('budget.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO budget (date, expense_name, expense_amount, user_id) VALUES(?, ?, ?, ?)", (today, expense_name, expense_amount, user_id))
                cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                data = cur.fetchall()
                prev_cash = data[0][2]
                new_income = prev_cash - expense_amount
                cur.execute("UPDATE users SET cash = ? WHERE user_id = ?", (new_income, user_id)) 
                cur.execute("SELECT * FROM budget WHERE user_id = ?", (user_id,)) 
                rows = cur.fetchall()
                con.commit()
            return render_template("expense-table.html", rows=rows)
    else:
        return render_template("expense.html")

@app.route('/logout')
def logout():
    global user_id
    if user_id:
        user_id = ""
        message = "You have successfully logged out!"
        return render_template('login.html', message = message)
    else:
        return redirect("/login")


if __name__ == '__main__':
    app.run()
