from .extensions import db


class Event(db.Model):
    __tablename__ = 'events'

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    firstName  = db.Column(db.String(255), nullable=True)
    lastName   = db.Column(db.String(255), nullable=True)
    email      = db.Column(db.String(255), nullable=True)
    eventName  = db.Column(db.String(255), nullable=False)
    datePicker = db.Column(db.String(128), nullable=False)
    address    = db.Column(db.Text, nullable=False)
    latitude   = db.Column(db.Numeric(10, 8), nullable=False)
    longitude  = db.Column(db.Numeric(10, 8), nullable=False)
    readToken  = db.Column(db.String(255), nullable=False)
    editToken  = db.Column(db.String(255), nullable=False)
    comments   = db.Column(db.Text, nullable=True)

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

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    firstName        = db.Column(db.String(255), nullable=False)
    lastName         = db.Column(db.String(255), nullable=False)
    email            = db.Column(db.String(255), nullable=False)
    showEmail        = db.Column(db.Boolean, nullable=False)
    registrationDate = db.Column(db.String(32), nullable=False)
    mode             = db.Column(db.String(255), nullable=False)
    latitude         = db.Column(db.Numeric(10, 8), nullable=False)
    longitude        = db.Column(db.Numeric(10, 8), nullable=False)
    address          = db.Column(db.Text, nullable=True)
    eventId          = db.Column(db.BigInteger, db.ForeignKey('events.id'), nullable=False)
    comments         = db.Column(db.Text, nullable=True)
    phoneNumber      = db.Column(db.String(20), nullable=False)
    notifyMe         = db.Column(db.Boolean, nullable=False)
    contactToken     = db.Column(db.String(255), nullable=False)
    editToken        = db.Column(db.String(255), nullable=False)
    
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
            'address': self.address,
            'eventId': self.eventId,
            'comments': self.comments,
            'phoneNumber': self.phoneNumber,
            'notifyMe': self.notifyMe,
            'contactToken': self.contactToken,
        }
