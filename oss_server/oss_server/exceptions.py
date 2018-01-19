from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class TransactionError(ValidationError):
    pass
