from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///delay.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Pre-set password for data reset (change this to a secure value)
RESET_PASSWORD = "your_password_here"

class DelayEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String(50), nullable=False)
    
    @property
    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60.0  # Duration in minutes
        return None



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_delay():
    data = request.get_json()
    reason = data.get('reason')
    if reason not in ["out body", "out 1-dot battery", "out of 2 dot battery", "out of 3 dot battery"]:
        return jsonify({"error": "Invalid reason"}), 400
    
    # Prevent starting a new event if one is already active
    active_event = DelayEvent.query.filter_by(end_time=None).first()
    if active_event:
        return jsonify({"error": "There is already an active delay event"}), 400

    new_event = DelayEvent(reason=reason, start_time=datetime.utcnow())
    db.session.add(new_event)
    db.session.commit()
    return jsonify({"message": "Delay started", "event_id": new_event.id})

@app.route('/end', methods=['POST'])
def end_delay():
    active_event = DelayEvent.query.filter_by(end_time=None).first()
    if not active_event:
        return jsonify({"error": "No active delay event found"}), 400

    active_event.end_time = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Delay ended", "event_id": active_event.id, "duration_minutes": active_event.duration})

@app.route('/data', methods=['GET'])
def get_data():
    events = DelayEvent.query.all()
    data = []
    for event in events:
        data.append({
            "id": event.id,
            "start_time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S") if event.end_time else None,
            "reason": event.reason,
            "duration_minutes": event.duration
        })
    return jsonify(data)

@app.route('/download', methods=['GET'])
def download_data():
    events = DelayEvent.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Start Time", "End Time", "Reason", "Duration (minutes)"])
    for event in events:
        cw.writerow([
            event.id,
            event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            event.end_time.strftime("%Y-%m-%d %H:%M:%S") if event.end_time else "",
            event.reason,
            event.duration if event.duration is not None else ""
        ])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, attachment_filename='delay_data.csv')

@app.route('/reset', methods=['POST'])
def reset_data():
    data = request.get_json()
    password = data.get('password')
    if password != RESET_PASSWORD:
        return jsonify({"error": "Invalid password"}), 403

    num_deleted = DelayEvent.query.delete()
    db.session.commit()
    return jsonify({"message": f"Reset successful, deleted {num_deleted} events."})

@app.route('/stats', methods=['GET'])
def get_stats():
    # Aggregate finished delay events by date and reason
    events = DelayEvent.query.filter(DelayEvent.end_time != None).all()
    stats = {}
    total_duration = 0
    for event in events:
        date_str = event.start_time.strftime("%Y-%m-%d")
        if date_str not in stats:
            stats[date_str] = {
                "out body": 0,
                "out 1-dot battery": 0,
                "out of 2 dot battery": 0,
                "out of 3 dot battery": 0
            }
        if event.duration:
            stats[date_str][event.reason] += event.duration
            total_duration += event.duration
    return jsonify({"daily_stats": stats, "total_duration_minutes": total_duration})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')

