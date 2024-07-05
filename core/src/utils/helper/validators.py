import re

from src.utils.config.environment import ENV

EMAIL_RE = re.compile(r'^[\w.-]+@[\w.-]+\.[\w.-]{2,4}$')


def validate_email(mail: str) -> str:
    if re.match(EMAIL_RE, mail):
        domain = mail.split("@")[1]
        if domain not in ENV.EMAIL_DOMAIN_WHITELIST:
            raise ValueError("email provider not whitelisted")
        return mail
    else:
        raise ValueError("bad syntax")


def validate_password(password: str) -> str:
    if re.search('[0-9]', password) is None:
        raise ValueError("password must contain a number")
    elif re.search('[A-Z]', password) is None:
        raise ValueError("password must contain a captial letter")
    elif re.search('[a-z]', password) is None:
        raise ValueError("password must contain a lower letter")
    elif re.search('[!@#$%^&*(),.?":{}|<>]', password) is None:
        raise ValueError(
            "password must contain at least one special character")
    return password
