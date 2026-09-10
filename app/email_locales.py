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
            'eventCreated': '[Movewiz] Your carpool has been created',
            'newParticipant': '[Movewiz] A new participant has joined your carpool',
            'registrationConfirmed': '[Movewiz] Your registration is confirmed',
            'newMessage': '[Movewiz] New message about "{event_name}"',
        },
        'event_creation': {
            'header': 'Your carpool is ready',
            'greeting': 'Hello,',
            'intro': 'Thanks for creating the carpool {eventName}. Here are the details and your access links.',
            'details': 'Carpool details',
            'labelEventName': 'Carpool name',
            'labelDate': 'Date',
            'labelAddress': 'Address',
            'linksTitle': 'Your access links',
            'openEvent': 'View the carpool',
            'editEvent': 'Edit the carpool',
            'comments': 'Details',
            'footer': 'Share your links to invite other participants.\n\nBest regards,\nThe MoveWiz team',
        },
        'new_participant': {
            'header': 'New participant',
            'greeting': 'Hello,',
            'intro': 'A new participant, {firstName} {lastName}, has just signed up to join the carpool {eventName}.',
            'details': 'Participant details',
            'labelFirstName': 'First name',
            'labelLastName': 'Last name',
            'labelRole': 'Role',
            'labelEmail': 'Email',
            'labelPhone': 'Phone',
            'viewIntro': 'To see the map with all participants:',
            'viewEvent': 'View the map',
            'hiddenEmail': 'Hidden email',
            'comments': 'Comments',
            'footer': 'Best regards,\nThe MoveWiz team',
        },
        'participant_registered': {
            'header': 'Registration confirmed',
            'greeting': 'Hi {firstName} {lastName},',
            'intro': 'Your registration for the carpool below is confirmed.',
            'details': 'Carpool details',
            'labelEventName': 'Carpool name',
            'labelDate': 'Date',
            'labelAddress': 'Address',
            'labelRole': 'Your role',
            'editTitle': 'Edit your registration',
            'editText': 'You can update your details at any time with this link:',
            'editButton': 'Edit my registration',
            'footer': 'See you soon!\n\nBest regards,\nThe MoveWiz team',
        },
        'contact': {
            'header': 'New message',
            'greeting': 'Hello,',
            'intro': 'You received a new message about your carpool.',
            'from': 'From',
            'footer': 'Best regards,\nThe MoveWiz team',
        },
        'mode': {
            'driver': 'Driver',
            'passenger': 'Passenger',
        },
    },
    'fr': {
        'subjects': {
            'eventCreated': '[Movewiz] Votre covoiturage a été créé',
            'newParticipant': '[Movewiz] Un nouveau participant a rejoint votre covoiturage',
            'registrationConfirmed': '[Movewiz] Votre inscription est confirmée',
            'newMessage': '[Movewiz] Nouveau message au sujet de « {event_name} »',
        },
        'event_creation': {
            'header': 'Votre covoiturage est prêt',
            'greeting': 'Bonjour,',
            'intro': 'Merci d\'avoir créé le covoiturage {eventName}. Voici les détails et vos liens d\'accès.',
            'details': 'Détails du covoiturage',
            'labelEventName': 'Nom du covoiturage',
            'labelDate': 'Date',
            'labelAddress': 'Adresse',
            'linksTitle': 'Vos liens d\'accès',
            'openEvent': 'Voir le covoiturage',
            'editEvent': 'Modifier le covoiturage',
            'comments': 'Précisions',
            'footer': 'Partagez vos liens pour inviter d\'autres participants.\n\nCordialement,\nL\'équipe MoveWiz',
        },
        'new_participant': {
            'header': 'Nouveau participant',
            'greeting': 'Bonjour,',
            'intro': 'Un nouveau participant, {firstName} {lastName}, vient de s\'inscrire pour participer au covoiturage {eventName}.',
            'details': 'Détails du participant',
            'labelFirstName': 'Prénom',
            'labelLastName': 'Nom',
            'labelRole': 'Rôle',
            'labelEmail': 'E-mail',
            'labelPhone': 'Téléphone',
            'viewIntro': 'Pour voir la carte de localisation des participants :',
            'viewEvent': 'Voir la carte',
            'hiddenEmail': 'E-mail masqué',
            'comments': 'Commentaires',
            'footer': 'Cordialement,\nL\'équipe MoveWiz',
        },
        'participant_registered': {
            'header': 'Inscription confirmée',
            'greeting': 'Bonjour {firstName} {lastName},',
            'intro': 'Votre inscription au covoiturage ci-dessous est confirmée.',
            'details': 'Détails du covoiturage',
            'labelEventName': 'Nom du covoiturage',
            'labelDate': 'Date',
            'labelAddress': 'Adresse',
            'labelRole': 'Votre rôle',
            'editTitle': 'Modifier votre inscription',
            'editText': 'Vous pouvez modifier vos informations à tout moment avec ce lien :',
            'editButton': 'Modifier mon inscription',
            'footer': 'À bientôt !\n\nCordialement,\nL\'équipe MoveWiz',
        },
        'contact': {
            'header': 'Nouveau message',
            'greeting': 'Bonjour,',
            'intro': 'Vous avez reçu un nouveau message concernant votre covoiturage.',
            'from': 'De',
            'footer': 'Cordialement,\nL\'équipe MoveWiz',
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
