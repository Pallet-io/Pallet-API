from django.core.exceptions import ValidationError


class TransactionError(ValidationError):
    pass
