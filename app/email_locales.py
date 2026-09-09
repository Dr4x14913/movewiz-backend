"""Dedicated, backend-only localization for the transactional emails.

These strings are intentionally kept separate from the frontend i18n bundles
(``movewiz-frontend/src/i18n/locales/*``), which carry far more than an email
needs (navigation, forms, popups, maps...). Keeping a small, self-contained set
here means the wording and structure of the emails can evolve independently of
the UI copy.

The frontend sends the user's chosen locale as ``language`` on each relevant
request. :func:`normalize_lang` coerces that value to a supported locale and
falls back to English when it is missing or unsupported, so a missing/unknown
language can never break email rendering.
"""

DEFAULT_LANG = 'en'

EMAIL_LOCALES = {
    'en': {
        'subjects': {
            'eventCreated': '[Movewiz] Your event has been created',
            'newParticipant': '[Movewiz] A new participant has joined',
            'registrationConfirmed': '[Movewiz] Your registration is confirmed',
            'newMessage': '[Movewiz] New message about "{event_name}"',
        },
        'event_creation': {
            'header': 'Your event is ready',
            'intro': 'Thanks for creating your event. Here are the details and your access links.',
            'details': 'Event details',
            'labelEventName': 'Event name',
            'labelDate': 'Date',
            'labelAddress': 'Address',
            'labelLatitude': 'Latitude',
            'labelLongitude': 'Longitude',
            'labelReadUrl': 'Read-only link',
            'labelEditUrl': 'Edit link',
            'openEvent': 'Open the event (read-only)',
            'editEvent': 'Edit the event',
            'comments': 'Details',
            'footer': 'Share your links to invite other participants.',
        },
        'new_participant': {
            'header': 'New participant',
            'intro': '{firstName} has just joined the event.',
            'labelEventName': 'Event',
            'details': 'Participant details',
            'labelFirstName': 'First name',
            'labelLastName': 'Last name',
            'labelRole': 'Role',
            'labelLatitude': 'Latitude',
            'labelLongitude': 'Longitude',
            'labelEmail': 'Email',
            'labelPhone': 'Phone',
            'viewEvent': 'View event',
            'hiddenEmail': 'Hidden email',
            'comments': 'Comments',
            'footer': 'Open the event to see all participants.',
        },
        'participant_registered': {
            'header': 'Registration confirmed',
            'greeting': 'Hi {firstName} {lastName},',
            'intro': 'You are now registered for the event below.',
            'details': 'Event details',
            'labelEventName': 'Event name',
            'labelDate': 'Date',
            'labelAddress': 'Address',
            'labelRole': 'Your role',
            'editTitle': 'Edit your registration',
            'editText': 'You can update your details at any time with this link:',
            'editButton': 'Edit my registration',
            'footer': 'See you at the event!',
        },
        'contact': {
            'header': 'New message',
            'intro': 'You received a message about your carpool.',
            'from': 'From',
            'footer': 'This is an automated notification from Movewiz.',
        },
        'mode': {
            'driver': 'Driver',
            'passenger': 'Passenger',
        },
    },
    'fr': {
        'subjects': {
            'eventCreated': '[Movewiz] Votre événement a été créé',
            'newParticipant': '[Movewiz] Un nouveau participant a rejoint l\'événement',
            'registrationConfirmed': '[Movewiz] Votre inscription est confirmée',
            'newMessage': '[Movewiz] Nouveau message au sujet de « {event_name} »',
        },
        'event_creation': {
            'header': 'Votre événement est prêt',
            'intro': 'Merci d\'avoir créé votre événement. Voici les détails et vos liens d\'accès.',
            'details': 'Détails de l\'événement',
            'labelEventName': 'Nom de l\'événement',
            'labelDate': 'Date',
            'labelAddress': 'Adresse',
            'labelLatitude': 'Latitude',
            'labelLongitude': 'Longitude',
            'labelReadUrl': 'Lien en lecture seule',
            'labelEditUrl': 'Lien de modification',
            'openEvent': 'Ouvrir l\'événement (lecture seule)',
            'editEvent': 'Modifier l\'événement',
            'comments': 'Précisions',
            'footer': 'Partagez vos liens pour inviter d\'autres participants.',
        },
        'new_participant': {
            'header': 'Nouveau participant',
            'intro': '{firstName} vient de rejoindre l\'événement.',
            'labelEventName': 'Événement',
            'details': 'Détails du participant',
            'labelFirstName': 'Prénom',
            'labelLastName': 'Nom',
            'labelRole': 'Rôle',
            'labelLatitude': 'Latitude',
            'labelLongitude': 'Longitude',
            'labelEmail': 'E-mail',
            'labelPhone': 'Téléphone',
            'viewEvent': 'Voir l\'événement',
            'hiddenEmail': 'E-mail masqué',
            'comments': 'Commentaires',
            'footer': 'Ouvrez l\'événement pour voir tous les participants.',
        },
        'participant_registered': {
            'header': 'Inscription confirmée',
            'greeting': 'Bonjour {firstName} {lastName},',
            'intro': 'Vous êtes maintenant inscrit à l\'événement ci-dessous.',
            'details': 'Détails de l\'événement',
            'labelEventName': 'Nom de l\'événement',
            'labelDate': 'Date',
            'labelAddress': 'Adresse',
            'labelRole': 'Votre rôle',
            'editTitle': 'Modifier votre inscription',
            'editText': 'Vous pouvez modifier vos informations à tout moment via ce lien :',
            'editButton': 'Modifier mon inscription',
            'footer': 'À bientôt à l\'événement !',
        },
        'contact': {
            'header': 'Nouveau message',
            'intro': 'Vous avez reçu un message concernant votre covoiturage.',
            'from': 'De',
            'footer': 'Notification automatique envoyée par Movewiz.',
        },
        'mode': {
            'driver': 'Conducteur',
            'passenger': 'Passager',
        },
    },
}


def normalize_lang(value):
    """Return a supported locale, falling back to the default.

    Accepts the raw ``language`` value coming from the request (case-insensitive)
    and returns :data:`DEFAULT_LANG` for anything missing or unsupported.
    """
    if isinstance(value, str) and value.lower() in EMAIL_LOCALES:
        return value.lower()
    return DEFAULT_LANG


def get_locale(lang):
    """Return the full locale bundle for ``lang`` (default-safe)."""
    return EMAIL_LOCALES[normalize_lang(lang)]


def strings(lang, email_type):
    """Return the dict of localized strings for one email type.

    Templates receive this dict as ``t`` and read values like ``{{ t.header }}``.
    """
    return get_locale(lang)[email_type]


def subject(lang, key):
    """Return a localized email subject line for ``key``.

    Some subjects contain ``{...}`` placeholders (e.g. ``newMessage`` includes
    ``{event_name}``); the caller is responsible for ``.format(...)``-ing those.
    """
    return get_locale(lang)['subjects'][key]
