from flask import Flask, render_template, request, jsonify, send_file
import dns.resolver
import re
import csv
import io

app = Flask(__name__)

# Validate email format
def is_valid_syntax(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Check for disposable domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "10minutemail.com", "guerrillamail.com", "temp-mail.org"
}

def is_disposable(email):
    domain = email.split('@')[-1].lower()
    return domain in DISPOSABLE_DOMAINS

# MX Record check
def has_mx_record(email):
    domain = email.split('@')[-1]
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except Exception:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    emails = request.json.get('emails', [])
    results = []

    for email in emails:
        valid_syntax = is_valid_syntax(email)
        disposable = is_disposable(email)
        mx_record = has_mx_record(email)
        is_valid = valid_syntax and not disposable and mx_record

        results.append({
            "email": email,
            "valid": is_valid,
            "syntax": valid_syntax,
            "disposable": disposable,
            "mx": mx_record
        })

    # Store in session memory
    global last_results
    last_results = results

    return jsonify(results)

@app.route('/download_csv')
def download_csv():
    global last_results
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Email", "Is Valid", "Valid Syntax", "Disposable", "Has MX Record"])
    for r in last_results:
        cw.writerow([r["email"], r["valid"], r["syntax"], r["disposable"], r["mx"]])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', download_name='results.csv', as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    content = file.read().decode('utf-8')
    emails = [line.strip() for line in content.splitlines() if line.strip()]
    return jsonify({ "emails": emails })

if __name__ == '__main__':
    app.run(debug=True)