# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
# This file controls email validation settings.
# =============================================================================


# =============================================================================
# BLACKLISTED EMAIL DOMAINS
# =============================================================================
# Email addresses ending with these domains will be rejected.
# This helps prevent misuse with official/government email addresses.
# Format: List of domain endings (e.g., '.gov', '.mil')

BLACKLISTED_EMAIL_DOMAINS = [
    # Government domains
    '.gov',
    '.gov.uk',
    '.gov.au',
    '.gov.ca',
    '.gov.in',
    '.gov.br',
    '.government.nl',

    # Military domains
    '.mil',

    # Educational domains (optional - uncomment if needed)
    # '.edu',
    # '.ac.uk',

    # Temporary/Disposable email services
    '@lnovic.com',
    '@tempmail.com',
    '@temp-mail.org',
    '@guerrillamail.com',
    '@guerrillamail.org',
    '@guerrillamail.net',
    '@sharklasers.com',
    '@grr.la',
    '@10minutemail.com',
    '@10minutemail.net',
    '@10minmail.com',
    '@mailinator.com',
    '@mailinator.net',
    '@mailinater.com',
    '@throwaway.email',
    '@throwawaymail.com',
    '@fakeinbox.com',
    '@trashmail.com',
    '@trashmail.net',
    '@dispostable.com',
    '@mintemail.com',
    '@tempinbox.com',
    '@emailondeck.com',
    '@yopmail.com',
    '@yopmail.fr',
    '@yopmail.net',
    '@cool.fr.nf',
    '@jetable.fr.nf',
    '@nospam.ze.tc',
    '@nomail.xl.cx',
    '@mega.zik.dj',
    '@speed.1s.fr',
    '@courriel.fr.nf',
    '@moncourrier.fr.nf',
    '@monemail.fr.nf',
    '@monmail.fr.nf',
    '@getnada.com',
    '@tempail.com',
    '@mohmal.com',
    '@discard.email',
    '@discardmail.com',
    '@spamgourmet.com',
    '@mytrashmail.com',
    '@mailnesia.com',
    '@maildrop.cc',
    '@mailcatch.com',
    '@spamavert.com',
    '@spamfree24.org',
    '@spambox.us',
    '@kasmail.com',
    '@emkei.cz',
    '@anonymbox.com',
    '@fakemailgenerator.com',
    '@emailfake.com',
    '@crazymailing.com',
    '@tempmailo.com',
    '@emailtemporanea.com',
    '@emailtemporanea.net',
    '@mailtemp.info',
    '@tempmailaddress.com',
    '@burnermail.io',
    '@inboxkitten.com',
]


# =============================================================================
# ALLOWED EMAIL DOMAIN ENDINGS (TLDs)
# =============================================================================
# Only emails with these domain endings will be accepted.
# Common valid TLDs for email addresses.
# Set to empty list [] to allow any TLD.

ALLOWED_EMAIL_TLDS = [
    # Common TLDs
    '.com',
    '.net',
    '.org',
    '.io',
    '.co',
    '.info',
    '.biz',
    '.me',
    '.app',
    '.dev',
    '.xyz',
    '.online',
    '.site',
    '.tech',
    '.cloud',
    '.email',
    '.mail',

    # Country TLDs
    '.uk',
    '.us',
    '.ca',
    '.au',
    '.de',
    '.fr',
    '.es',
    '.it',
    '.nl',
    '.be',
    '.ch',
    '.at',
    '.se',
    '.no',
    '.dk',
    '.fi',
    '.pl',
    '.ru',
    '.jp',
    '.cn',
    '.kr',
    '.in',
    '.br',
    '.mx',
    '.ar',
    '.nz',
    '.za',
    '.sg',
    '.hk',
    '.tw',
    '.ie',
    '.pt',
    '.gr',
    '.cz',
    '.hu',
    '.ro',
    '.bg',
    '.hr',
    '.sk',
    '.si',
    '.lt',
    '.lv',
    '.ee',

    # Newer/popular TLDs
    '.co.uk',
    '.com.au',
    '.co.nz',
    '.co.in',
    '.com.br',
]
