import uuid
import base64

from flask import Blueprint, request, jsonify
from ..extensions import db, limiter
from ..models import Event, Participant
from ..services import send_email, notify_all, generate_captcha, store_captcha, verify_captcha

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/createEvent', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def create_event():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    event_name = data.get('eventName')
    date_picker = data.get('datePicker')
    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    comments = data.get('comments')
    answer = data.get('answer')
    captcha_token = data.get('captchaToken')

    if not verify_captcha(captcha_token, answer):
        return jsonify({'error': 'Invalid captcha'}), 401

    read_token = str(uuid.uuid4())
    edit_token = str(uuid.uuid4())

    event = Event(
        firstName=first_name,
        lastName=last_name,
        email=email,
        eventName=event_name,
        datePicker=date_picker,
        address=address,
        latitude=latitude,
        longitude=longitude,
        readToken=read_token,
        editToken=edit_token,
        comments=comments,
    )
    db.session.add(event)
    db.session.commit()

    # Construct URLs from frontend origin
    frontend_origin = data.get('frontendOrigin', '').rstrip('/')
    read_url = f"{frontend_origin}/event?token={read_token}"
    write_url = f"{frontend_origin}/edit?token={edit_token}"

    # Send confirmation email
    from flask import render_template
    html = render_template('event_creation.html',
        eventName=event_name,
        eventAddress=address,
        latitude=latitude,
        longitude=longitude,
        eventDate=date_picker,
        eventComments=comments,
        publicUrl=read_url,
        privateUrl=write_url,
    )
    send_email(email, "[Movewiz] New Event Created", html)

    return jsonify({'readUrl': read_url, 'writeUrl': write_url}), 201


@api_bp.route('/api/getEvent', methods=['GET'])
def get_event():
    token = request.args.get('token')
    is_edit = request.args.get('isEdit', 'false').lower() == 'true'

    if not token:
        return jsonify({'error': 'Token is required'}), 400

    token_type = 'editToken' if is_edit else 'readToken'
    event = Event.query.filter(getattr(Event, token_type) == token).first()

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Don't expose tokens to the client
    data = event.to_dict()
    data.pop('readToken', None)
    data.pop('editToken', None)
    return jsonify({'event': data})


@api_bp.route('/api/editEvent', methods=['POST'])
def edit_event():
    data = request.get_json()
    edit_token = data.get('editToken')

    if not edit_token:
        return jsonify({'error': 'Edit token is required'}), 400

    event = Event.query.filter_by(editToken=edit_token).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Update fields
    updates = {k: v for k, v in data.items() if k != 'editToken'}
    for key, value in updates.items():
        if hasattr(event, key):
            setattr(event, key, value)

    db.session.commit()

    data = event.to_dict()
    data.pop('readToken', None)
    data.pop('editToken', None)
    return jsonify({'event': data})


@api_bp.route('/api/registerParticipant', methods=['POST'])
def register_participant():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    mode = data.get('mode')
    show_email = data.get('showEmail')
    token = data.get('token')
    registration_date = data.get('registrationDate')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    comments = data.get('comments')
    phone_number = data.get('phoneNumber')
    notify_me = data.get('notifyMe')

    event = Event.query.filter_by(readToken=token).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    contact_token = str(uuid.uuid4())
    participant = Participant(
        firstName=first_name,
        lastName=last_name,
        email=email,
        registrationDate=registration_date,
        mode=mode,
        showEmail=show_email,
        eventId=event.id,
        latitude=latitude,
        longitude=longitude,
        comments=comments,
        phoneNumber=phone_number,
        notifyMe=notify_me,
        contactToken=contact_token,
    )
    db.session.add(participant)
    db.session.commit()

    # Notify all
    from flask import render_template
    frontend_origin = data.get('frontendOrigin', '').rstrip('/')
    url = f"{frontend_origin}/event?token={token}"

    notify_all(
        event.id,
        event.email,
        "[Movewiz] A new participant joined the event!",
        {
            'eventName': event.eventName,
            'firstName': first_name,
            'lastName': last_name,
            'mode': mode,
            'email': email if show_email else "Hidden email",
            'latitude': latitude,
            'longitude': longitude,
            'comments': comments,
            'phoneNumber': phone_number,
            'url': url,
        },
        'new_participant.html'
    )

    return jsonify({'message': 'Participant registered successfully'}), 200


@api_bp.route('/api/getParticipants', methods=['GET'])
def get_participants():
    token = request.args.get('token')

    event = Event.query.filter_by(readToken=token).first()
    if not event:
        return jsonify({'error': 'Event not found or invalid token'}), 404

    participants = Participant.query.filter_by(eventId=event.id).all()
    return jsonify([p.to_dict() for p in participants])


@api_bp.route('/api/contactParticipant', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def contact_participant():
    data = request.get_json()
    contact_token = data.get('contactToken')
    answer = data.get('answer')
    captcha_token = data.get('captchaToken')
    sender_email = data.get('senderEmail')
    message = data.get('message')
    event_name = data.get('eventName')

    if not verify_captcha(captcha_token, answer):
        return jsonify({'error': 'Invalid captcha'}), 401

    participant = Participant.query.filter_by(contactToken=contact_token).first()
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404

    from flask import render_template
    html = render_template('contact.html', senderEmail=sender_email, message=message)
    send_email(participant.email, f"[Movewiz] Contact from event {event_name}", html)

    return jsonify({'success': True})


@api_bp.route('/generate-captcha', methods=['GET'])
def captcha():
    captcha_image, captcha_text = generate_captcha()
    token = store_captcha(captcha_text)
    image_base64 = base64.b64encode(captcha_image.getvalue()).decode()
    return jsonify({'token': token, 'image': image_base64})
