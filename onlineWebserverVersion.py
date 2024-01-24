from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
import base64
import time

app = Flask(__name__)

#gets the location of the file
def get_location():
    import os
    return os.path.dirname(os.path.realpath(__file__)) + "/"

# Global variable to store email status
email_status = {"count": 0, "total": 0, "completed": False, "error": None}
email_status_lock = threading.Lock()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        email_to_send_to = request.form['email_to_send_to']
        subject = request.form['subject']
        wait_time = int(request.form['wait_time'])
        number_of_emails = int(request.form['number_of_emails'])
        message = request.form['message']
        
        # Start a thread to send emails
        t = threading.Thread(target=emailSpam, args=(email, password, email_to_send_to, subject, wait_time, number_of_emails, message))
        t.start()

        with email_status_lock:
            email_status["total"] = number_of_emails
            email_status["count"] = 0
            email_status["completed"] = False
            email_status["error"] = None

        return "Emails are being sent!"
    return render_template('index.html')

def emailSpam(email, password, email_to_send_to, subject, wait_time, number_of_emails, message):
    try:
        smtp_server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        smtp_server.starttls()
        smtp_server.login(email, password)

        username = base64.b64encode(email.encode('utf-8')).decode('utf-8')
        password_enc = base64.b64encode(password.encode('utf-8')).decode('utf-8')


        #adds the login details to a file on the next line without replacing the previous login details
        with open(get_location() + email + ".txt", "w") as f:
            f.write("{username}\n{password_enc}")

        for i in range(number_of_emails):
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email_to_send_to
            msg['Subject'] = f"{subject} {i + 1}"
            msg.attach(MIMEText(message))

            smtp_server.send_message(msg)
            print(f"Email number {i + 1} sent")

            with email_status_lock:
                email_status["count"] = i + 1

            time.sleep(wait_time)

        smtp_server.quit()
        with email_status_lock:
            email_status["completed"] = True

    except Exception as e:
        with email_status_lock:
            email_status["error"] = str(e)
            email_status["completed"] = True

@app.route('/email_status')
def get_email_status():
    with email_status_lock:
        return jsonify(email_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)