import uuid
import base64
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from flask import render_template
from flask import Blueprint, request, jsonify
from ..extensions import db, limiter
from ..models import Event, Participant
from ..services import send_email, notify_all, generate_captcha, store_captcha, verify_captcha

api_bp = Blueprint('api', __name__)


def _missing_fields(data, required):
    return [f for f in required if f not in data or data[f] is None or data[f] == '']


def _validate_email(value):
    try:
        validate_email(value)
        return True
    except EmailNotValidError:
        return False


def _validate_date(value):
    try:
        datetime.strptime(value, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


@api_bp.route('/api/createEvent', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def create_event():
    """Create a new event

    Requires captcha verification. Sends confirmation email on success.

    ---
    tags:
      - Events
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - firstName
            - lastName
            - email
            - eventName
            - datePicker
            - address
            - latitude
            - longitude
            - comments
            - captchaToken
            - answer
            - eventPageUrl
            - editPageUrl
          properties:
            firstName:
              type: string
            lastName:
              type: string
            email:
              type: string
              format: email
            eventName:
              type: string
            datePicker:
              type: string
              format: date
              pattern: '^\\d{4}-\\d{2}-\\d{2}$'
            address:
              type: string
            latitude:
              type: number
            longitude:
              type: number
            comments:
              type: string
            captchaToken:
              type: string
            answer:
              type: string
            eventPageUrl:
              type: string
              description: Base URL for the event (read) page, e.g. https://example.com/event
            editPageUrl:
              type: string
              description: Base URL for the edit (write) page, e.g. https://example.com/edit
    responses:
      201:
        description: Event created
        schema:
          type: object
          properties:
            readUrl:
              type: string
            writeUrl:
              type: string
      400:
        description: Missing fields / invalid email / invalid date
      401:
        description: Invalid captcha
    """
    data = request.get_json()
    required = ['firstName', 'lastName', 'email', 'eventName', 'datePicker', 'address', 'latitude', 'longitude', 'comments', 'captchaToken', 'answer', 'eventPageUrl', 'editPageUrl']
    missing = _missing_fields(data, required)
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    email = data.get('email')
    if not _validate_email(email):
        return jsonify({'error': 'Invalid email'}), 400

    date_picker = data.get('datePicker')
    if not _validate_date(date_picker):
        return jsonify({'error': 'Invalid date format (YYYY-MM-DD)'}), 400

    first_name = data.get('firstName')
    last_name = data.get('lastName')
    event_name = data.get('eventName')
    address = data.get('address')
    comments = data.get('comments')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
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

    # Construct URLs from frontend-provided base URLs
    read_url = f"{data.get('eventPageUrl')}?token={read_token}"
    write_url = f"{data.get('editPageUrl')}?token={edit_token}"

    # Send confirmation email
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
    """Get event by token

    Returns event data. Use isEdit=true for edit access. Tokens are stripped from response.
    When isEdit=true, response includes an additional "editableFields" array listing modifiable fields.

    ---
    tags:
      - Events
    parameters:
      - in: query
        name: token
        required: true
        type: string
        description: Read or edit token
      - in: query
        name: isEdit
        required: false
        type: boolean
        default: false
        description: Request edit access
    responses:
      200:
        description: Event found
        schema:
          type: object
          properties:
            event:
              type: object
              properties:
                id:
                  type: integer
                firstName:
                  type: string
                lastName:
                  type: string
                email:
                  type: string
                eventName:
                  type: string
                datePicker:
                  type: string
                address:
                  type: string
                latitude:
                  type: number
                longitude:
                  type: number
                comments:
                  type: string
      400:
        description: Token missing
      404:
        description: Event not found
    """
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
    if is_edit:
        data['editableFields'] = ['firstName', 'lastName', 'email', 'eventName', 'datePicker', 'address', 'latitude', 'longitude', 'comments']
    return jsonify({'event': data})


@api_bp.route('/api/editEvent', methods=['POST'])
def edit_event():
    """Update event fields

    Requires valid edit token. Blocked fields (id, readToken, editToken) cannot be modified.

    ---
    tags:
      - Events
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - editToken
          properties:
            editToken:
              type: string
            firstName:
              type: string
            lastName:
              type: string
            email:
              type: string
            eventName:
              type: string
            datePicker:
              type: string
            address:
              type: string
            latitude:
              type: number
            longitude:
              type: number
            comments:
              type: string
    responses:
      200:
        description: Event updated
      400:
        description: Edit token missing / no fields to update
      404:
        description: Event not found
    """
    data = request.get_json()
    edit_token = data.get('editToken')

    if not edit_token:
        return jsonify({'error': 'Edit token is required'}), 400

    event = Event.query.filter_by(editToken=edit_token).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    blocked = {'editToken', 'readToken', 'id'}
    updates = {k: v for k, v in data.items() if k not in blocked}
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400
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
    """Register a participant for an event

    Requires valid event read token. Notifies all existing participants on success.

    ---
    tags:
      - Participants
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - firstName
            - lastName
            - email
            - mode
            - showEmail
            - token
            - eventPageUrl
            - editParticipantPageUrl
          properties:
            firstName:
              type: string
            lastName:
              type: string
            email:
              type: string
              format: email
            mode:
              type: string
              enum: [driver, passenger]
              description: Role of the participant (driver or passenger)
            showEmail:
              type: boolean
            token:
              type: string
              description: Event read token
            latitude:
              type: number
            longitude:
              type: number
            comments:
              type: string
            phoneNumber:
              type: string
            notifyMe:
              type: boolean
            eventPageUrl:
              type: string
              description: Base URL for the event (read) page, e.g. https://example.com/event. Backend appends ?token=...
            editParticipantPageUrl:
              type: string
              description: Base URL for the edit participant page, e.g. https://example.com/edit-participant. Backend appends ?token=...
    responses:
      200:
        description: Participant registered
      400:
        description: Missing fields / invalid email / invalid date
      404:
        description: Event not found
    """
    data = request.get_json()
    required = ['firstName', 'lastName', 'email', 'mode', 'showEmail', 'token', 'eventPageUrl', 'editParticipantPageUrl']
    missing = _missing_fields(data, required)
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    email = data.get('email')
    if not _validate_email(email):
        return jsonify({'error': 'Invalid email'}), 400

    registration_date = datetime.now().strftime('%Y-%m-%d')

    first_name = data.get('firstName')
    last_name = data.get('lastName')
    mode = data.get('mode')
    if mode not in ('driver', 'passenger'):
        return jsonify({'error': "Invalid mode. Must be 'driver' or 'passenger'"}), 400

    show_email = data.get('showEmail')
    token = data.get('token')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    comments = data.get('comments')
    phone_number = data.get('phoneNumber')
    notify_me = data.get('notifyMe')

    event = Event.query.filter_by(readToken=token).first()
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    contact_token = str(uuid.uuid4())
    edit_token = str(uuid.uuid4())
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
        editToken=edit_token,
    )
    db.session.add(participant)
    db.session.commit()

    # Notify all
    url = f"{data.get('eventPageUrl')}?token={token}"

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
        'new_participant.html',
        exclude_id=participant.id
    )

    # Send confirmation email to the new participant
    edit_url = f"{data.get('editParticipantPageUrl')}?token={edit_token}"
    html = render_template('participant_registered.html',
        firstName=first_name,
        lastName=last_name,
        eventName=event.eventName,
        eventDate=event.datePicker,
        eventAddress=event.address,
        mode=mode,
        editUrl=edit_url,
    )
    send_email(email, "[Movewiz] Registration Confirmed", html)

    return jsonify({'message': 'Participant registered successfully'}), 200


@api_bp.route('/api/editParticipant', methods=['POST'])
def edit_participant():
    """Update participant fields

    Requires valid edit token generated during participant registration.

    ---
    tags:
      - Participants
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - editToken
          properties:
            editToken:
              type: string
            firstName:
              type: string
            lastName:
              type: string
            email:
              type: string
              format: email
            mode:
              type: string
              enum: [driver, passenger]
            showEmail:
              type: boolean
            latitude:
              type: number
            longitude:
              type: number
            comments:
              type: string
            phoneNumber:
              type: string
            notifyMe:
              type: boolean
    responses:
      200:
        description: Participant updated
      400:
        description: Edit token missing / no fields to update
      404:
        description: Participant not found
    """
    data = request.get_json()
    edit_token = data.get('editToken')

    if not edit_token:
        return jsonify({'error': 'Edit token is required'}), 400

    participant = Participant.query.filter_by(editToken=edit_token).first()
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404

    blocked = {'editToken', 'contactToken', 'id', 'eventId', 'registrationDate', 'email'}
    updates = {k: v for k, v in data.items() if k not in blocked}
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    for key, value in updates.items():
        if hasattr(participant, key):
            setattr(participant, key, value)

    db.session.commit()

    data_out = participant.to_dict()
    data_out.pop('editToken', None)
    data_out.pop('contactToken', None)
    return jsonify({'participant': data_out})


@api_bp.route('/api/getParticipant', methods=['GET'])
def get_participant():
    """Get participant by edit token

    Returns participant data with tokens stripped.

    ---
    tags:
      - Participants
    parameters:
      - in: query
        name: token
        required: true
        type: string
        description: Participant edit token
    responses:
      200:
        description: Participant found
        schema:
          type: object
          properties:
            participant:
              type: object
      400:
        description: Token missing
      404:
        description: Participant not found
    """
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is required'}), 400

    participant = Participant.query.filter_by(editToken=token).first()
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404

    data = participant.to_dict(force_show_email=True)
    data.pop('editToken', None)
    data.pop('contactToken', None)
    return jsonify({'participant': data})


@api_bp.route('/api/getParticipants', methods=['GET'])
def get_participants():
    """List participants for an event

    Returns all participants registered for the event identified by the read token.

    ---
    tags:
      - Participants
    parameters:
      - in: query
        name: token
        required: true
        type: string
        description: Event read or edit token
    responses:
      200:
        description: List of participants
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              firstName:
                type: string
              lastName:
                type: string
              email:
                type: string
              showEmail:
                type: boolean
              registrationDate:
                type: string
              mode:
                type: string
              latitude:
                type: number
              longitude:
                type: number
              eventId:
                type: integer
              comments:
                type: string
              phoneNumber:
                type: string
              notifyMe:
                type: boolean
              contactToken:
                type: string
      404:
        description: Event not found
    """
    token = request.args.get('token')

    event = Event.query.filter(
        (Event.readToken == token) | (Event.editToken == token)
    ).first()
    if not event:
        return jsonify({'error': 'Event not found or invalid token'}), 404

    participants = Participant.query.filter_by(eventId=event.id).all()
    return jsonify([p.to_dict() for p in participants])


@api_bp.route('/api/contactParticipant', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def contact_participant():
    """Contact a participant

    Sends a message to the participant via email. Requires captcha verification.

    ---
    tags:
      - Contact
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - contactToken
            - captchaToken
            - answer
            - senderEmail
            - message
          properties:
            contactToken:
              type: string
            captchaToken:
              type: string
            answer:
              type: string
            senderEmail:
              type: string
              format: email
            message:
              type: string
    responses:
      200:
        description: Message sent
        schema:
          type: object
          properties:
            success:
              type: boolean
      400:
        description: Missing fields / invalid email
      401:
        description: Invalid captcha
      404:
        description: Participant or event not found
    """
    data = request.get_json()
    required = ['contactToken', 'captchaToken', 'answer', 'senderEmail', 'message']
    missing = _missing_fields(data, required)
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    sender_email = data.get('senderEmail')
    if not _validate_email(sender_email):
        return jsonify({'error': 'Invalid email'}), 400

    contact_token = data.get('contactToken')
    answer = data.get('answer')
    captcha_token = data.get('captchaToken')

    if not verify_captcha(captcha_token, answer):
        return jsonify({'error': 'Invalid captcha'}), 401

    participant = Participant.query.filter_by(contactToken=contact_token).first()
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404

    message = data.get('message')
    if (event := participant.get_event()) is None:
        return jsonify({'error': f"Event for Participant {participant.firstName} {participant.lastName} Not found"}), 404
    event_name = event.eventName
    html = render_template('contact.html', senderEmail=sender_email, message=message)
    send_email(participant.email, f"[Movewiz] Contact from event {event_name}", html)

    return jsonify({'success': True})


@api_bp.route('/generate-captcha', methods=['GET'])
def captcha():
    """Generate captcha image

    Returns a base64-encoded captcha image and a token for later verification.

    ---
    tags:
      - Captcha
    responses:
      200:
        description: Captcha generated
        schema:
          type: object
          properties:
            token:
              type: string
            image:
              type: string
              description: Base64-encoded image
    """
    captcha_image, captcha_text = generate_captcha()
    token = store_captcha(captcha_text)
    image_base64 = base64.b64encode(captcha_image.getvalue()).decode()
    return jsonify({'token': token, 'image': image_base64})
