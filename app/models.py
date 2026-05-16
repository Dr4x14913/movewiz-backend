from .extensions import db


class Event(db.Model):
    __tablename__ = 'events'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstName  = db.Column(db.String(255))
    lastName   = db.Column(db.String(255))
    email      = db.Column(db.String(255))
    eventName  = db.Column(db.String(255))
    datePicker = db.Column(db.String(32))
    address    = db.Column(db.Text)
    latitude   = db.Column(db.Numeric(10, 8))
    longitude  = db.Column(db.Numeric(10, 8))
    readToken  = db.Column(db.String(255))
    editToken  = db.Column(db.String(255))
    comments   = db.Column(db.Text)

    participants = db.relationship('Participant', backref='event', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'eventName': self.eventName,
            'datePicker': self.datePicker,
            'address': self.address,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'readToken': self.readToken,
            'comments': self.comments,
        }


class Participant(db.Model):
    __tablename__ = 'participants'

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstName        = db.Column(db.String(255))
    lastName         = db.Column(db.String(255))
    email            = db.Column(db.String(255))
    showEmail        = db.Column(db.Boolean)
    registrationDate = db.Column(db.String(32))
    mode             = db.Column(db.String(255))
    latitude         = db.Column(db.Numeric(10, 8))
    longitude        = db.Column(db.Numeric(10, 8))
    eventId          = db.Column(db.Integer, db.ForeignKey('events.id'))
    comments         = db.Column(db.Text)
    phoneNumber      = db.Column(db.String(20))
    notifyMe         = db.Column(db.Boolean)
    contactToken     = db.Column(db.String(255), nullable=True)
    editToken        = db.Column(db.String(255), nullable=True)
    
    def get_event(self) -> Event | None:
        return Event.query.filter_by(id=self.eventId).first()

    def to_dict(self, force_show_email=False):
        return {
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email if self.showEmail or force_show_email else "****",
            'showEmail': self.showEmail,
            'registrationDate': self.registrationDate,
            'mode': self.mode,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'eventId': self.eventId,
            'comments': self.comments,
            'phoneNumber': self.phoneNumber,
            'notifyMe': self.notifyMe,
            'contactToken': self.contactToken,
        }
