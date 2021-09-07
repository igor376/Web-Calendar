from flask import Flask, abort
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, reqparse, inputs, fields, marshal_with
from datetime import date
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

events_json = {
    "id": fields.Integer,
    "event": fields.String,
    "date": fields.String,
    "start_time": fields.String,
    "end_time": fields.String
}


class EventsDb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.VARCHAR, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'id={self.id} {self.date} events="{self.event}"'


db.create_all()


class Events(Resource):
    @marshal_with(events_json)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("start_time", type=inputs.date)
        parser.add_argument("end_time", type=inputs.date)
        args = parser.parse_args()
        if args["start_time"] is not None and args["end_time"] is not None:
            events = EventsDb.query.all()
            answer = []
            for event in events:
                if args["start_time"].strftime("%Y-%m-%d") <= str(event.date) <= args["end_time"].strftime("%Y-%m-%d"):
                    answer.append(event)
            return answer
        else:
            events = EventsDb.query.all()
            return events

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event', type=str, help='The event name is required!', required=True)
        parser.add_argument('date', type=inputs.date,
                            help='The event date with the correct format is required! The correct format is YYYY-MM-DD!',
                            required=True)
        args = parser.parse_args()
        db.session.add(EventsDb(event=args["event"], date=args["date"]))
        db.session.commit()
        return {
            "message": "The event has been added!",
            "event": f'{args["event"]}',
            "date": f'{date.strftime(args["date"], "%Y-%m-%d")}'
        }


class EventsToday(Resource):
    @marshal_with(events_json)
    def get(self):
        events = EventsDb.query.filter_by(date=date.today()).all()  #
        return events


class EventById(Resource):
    @marshal_with(events_json)
    def get(self, event_id):
        event = get_events(event_id)
        return event

    def delete(self, event_id):
        event = get_events(event_id)
        db.session.delete(event)
        db.session.commit()
        return {
            "message": "The event has been deleted!"
        }


def get_events(event_id):
    event = EventsDb.query.filter_by(id=event_id).first()
    if event is None:
        abort(404, "The event doesn't exist!")
    return event


api.add_resource(Events, '/event')
api.add_resource(EventsToday, '/event/today')
api.add_resource(EventById, '/event/<int:event_id>')
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
