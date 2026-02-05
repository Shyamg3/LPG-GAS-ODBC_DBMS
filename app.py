from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import pyodbc

app = Flask(__name__)
app.secret_key = "student_fee_secret_key"

# ---------- Database Configuration ----------
DB_DSN = "LPG_LOCAL"     # Your ODBC DSN name              
DB_USER = "system"        # Oracle username               
DB_PASSWORD = "system123" # Oracle password
# --------------------------------------------

def get_db_connection():
    conn_str = f"DSN={DB_DSN};UID={DB_USER};PWD={DB_PASSWORD}"
    return pyodbc.connect(conn_str)

# ------------------ LOGIN ------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('userid')
        pwd = request.form.get('password')
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT PASSWORD FROM APP_USERS WHERE USER_ID = ?", (user,))
            row = cur.fetchone()
            conn.close()
        except Exception as e:
            return render_template('login.html', error=f"DB error: {e}")

        if row and row[0] == pwd:
            session['user'] = user
            return redirect(url_for('fee_form'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ------------------ PAGE ------------------
@app.route('/fee')
def fee_form():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('fee.html')

# ------------------ Generate fee_id ------------------
@app.route('/generate_fee_id', methods=['GET'])
def generate_fee_id():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT SEQ_FEE_ID.NEXTVAL FROM DUAL")
        nxt = cur.fetchone()[0]
        conn.close()
        return jsonify({'fee_id': int(nxt)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ------------------ Insert / Update student_buffer ------------------
@app.route('/save_to_buffer', methods=['POST'])
def save_to_buffer():
    try:
        data = request.get_json() or request.form.to_dict()

        def g(k):
            return data.get(k) or data.get(k.lower()) or data.get(k.upper())

        fee_id = g("fee_id")

        conn = get_db_connection()
        cur = conn.cursor()

        # Reject if already committed
        if fee_id:
            cur.execute("SELECT 1 FROM student_main WHERE fee_id = ?", (int(fee_id),))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Record already committed. Cannot modify."}), 400

        # Fetch form values
        student_id = int(g("student_id"))
        student_name = g("student_name")
        department = g("department")
        seat_type = g("seat_type")                     
        total_amount = float(g("total_amount"))
        paid_amount = float(g("paid_amount"))
        balance_amount = float(g("balance_amount"))
        check_id = g("check_id")
        due_date_raw = g("due_date")
        payment_date_raw = g("payment_date")

        due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
        payment_date = datetime.strptime(payment_date_raw, "%Y-%m-%d").date() if payment_date_raw else datetime.now().date()

        # Generate new fee_id
        if not fee_id:
            cur.execute("SELECT SEQ_FEE_ID.NEXTVAL FROM DUAL")
            fee_id = cur.fetchone()[0]

        # Check buffer presence
        cur.execute("SELECT 1 FROM student_buffer WHERE fee_id = ?", (int(fee_id),))
        in_buffer = cur.fetchone() is not None

        if in_buffer:
            cur.execute("""
                UPDATE student_buffer SET
                    student_id=?, student_name=?, department=?, seat_type=?,
                    total_amount=?, paid_amount=?, balance_amount=?, check_id=?,
                    due_date=?, payment_date=?
                WHERE fee_id=?
            """, (student_id, student_name, department, seat_type,
                  total_amount, paid_amount, balance_amount, check_id,
                  due_date, payment_date, int(fee_id)))
            msg = f"Updated student_buffer {fee_id}"
        else:
            cur.execute("""
                INSERT INTO student_buffer (
                    fee_id, student_id, student_name, department, seat_type,
                    total_amount, paid_amount, balance_amount, check_id,
                    due_date, payment_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (int(fee_id), student_id, student_name, department, seat_type,
                  total_amount, paid_amount, balance_amount, check_id,
                  due_date, payment_date))
            msg = f"Inserted ID {fee_id}"

        conn.commit()
        conn.close()
        return jsonify({"message": msg, "fee_id": int(fee_id)})

    except Exception as e:
        try: conn.rollback()
        except: pass
        return jsonify({"error": str(e)}), 500



# ------------------ Get single student record ------------------
@app.route('/get_record', methods=['GET'])
def get_record():
    fee_id = request.args.get("fee_id")
    if not fee_id:
        return jsonify({'error': 'fee_id required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM student_buffer WHERE fee_id = ?", (int(fee_id),))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Not found'}), 404

        record = {
            "fee_id": row[0],
            "student_id": row[1],
            "student_name": row[2],
            "department": row[3],
            "seat_type": row[4],
            "total_amount": row[5],
            "paid_amount": row[6],
            "balance_amount": row[7],
            "check_id": row[8],
            "due_date": row[9].strftime('%Y-%m-%d'),
            "payment_date": row[10].strftime('%Y-%m-%d') if row[10] else ""
        }
        return jsonify({'success': True, 'record': record})

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# ------------------ Previous Record ------------------
@app.route('/get_previous_record', methods=['GET'])
def get_previous_record():
    cid = request.args.get("current_id", type=int)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM (
                SELECT * FROM student_buffer
                WHERE fee_id < ?
                ORDER BY fee_id DESC
            ) WHERE ROWNUM = 1
        """, (cid,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'No previous record'}), 404

        return jsonify({
            "record": {
                "fee_id": row[0],
                "student_id": row[1],
                "student_name": row[2],
                "department": row[3],
                "seat_type": row[4],
                "total_amount": row[5],
                "paid_amount": row[6],
                "balance_amount": row[7],
                "check_id": row[8],
                "due_date": row[9].strftime('%Y-%m-%d'),
                "payment_date": row[10].strftime('%Y-%m-%d') if row[10] else ""
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ Next Record ------------------
@app.route('/get_next_record', methods=['GET'])
def get_next_record():
    cid = request.args.get("current_id", type=int)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM (
                SELECT * FROM student_buffer
                WHERE fee_id > ?
                ORDER BY fee_id ASC
            ) WHERE ROWNUM = 1
        """, (cid,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'No next record'}), 404

        return jsonify({
            "record": {
                "fee_id": row[0],
                "student_id": row[1],
                "student_name": row[2],
                "department": row[3],
                "seat_type": row[4],
                "total_amount": row[5],
                "paid_amount": row[6],
                "balance_amount": row[7],
                "check_id": row[8],
                "due_date": row[9].strftime('%Y-%m-%d'),
                "payment_date": row[10].strftime('%Y-%m-%d') if row[10] else ""
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ Delete ------------------
@app.route('/delete_from_database', methods=['DELETE'])
def delete_from_database():
    try:
        data = request.get_json()
        fid = data.get("fee_id")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM student_buffer WHERE fee_id = ?", (int(fid),))
        cur.execute("DELETE FROM student_main WHERE fee_id = ?", (int(fid),))

        conn.commit()
        conn.close()

        return jsonify({'message': f'Fee ID {fid} deleted.'})

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# ------------------ Commit All ------------------
@app.route('/commit_all', methods=['POST'])
def commit_all():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO student_main SELECT * FROM student_buffer")
        cur.execute("DELETE FROM student_buffer")
        conn.commit()
        conn.close()
        return jsonify({'message': 'All buffer records committed to main.'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# ------------------ View Tables ------------------
@app.route('/show_buffer')
def show_buffer():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM student_buffer ORDER BY fee_id")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()

        html = "<h3>STUDENT_BUFFER</h3><table border=1><tr>"
        html += "".join(f"<th>{c}</th>" for c in cols) + "</tr>"

        for r in rows:
            html += "<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>"

        html += "</table>"
        return html

    except Exception as e:
        return f"Error: {e}", 500



@app.route('/show_main')
def show_main():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM student_main ORDER BY fee_id")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()

        html = "<h3>STUDENT_MAIN</h3><table border=1><tr>"
        html += "".join(f"<th>{c}</th>" for c in cols) + "</tr>"

        for r in rows:
            html += "<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>"

        html += "</table>"
        return html

    except Exception as e:
        return f"Error: {e}", 500




if __name__ == '__main__':
    app.run(debug=True)
