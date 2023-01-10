from pgcrypto import EncryptedCharField
from phonenumber_field.modelfields import PhoneNumberField


class EncryptedPhoneNumberField(EncryptedCharField, PhoneNumberField):
    pass
