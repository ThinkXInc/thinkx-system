# -*- coding: utf-8 -*-
#
# general/exceptions.py
#


class InvalidFormat(Exception):
    pass


class TextTooShort(Exception):
    pass


class TextTooLong(Exception):
    pass


class InvalidEmailFormat(Exception):
    pass


class InvalidPasswordFormat(Exception):
    pass


class ValueOutOfRange(Exception):
    pass


class EmptyFile(Exception):
    pass


class FileTooLarge(Exception):
    pass

class InvalidType(Exception):
    pass