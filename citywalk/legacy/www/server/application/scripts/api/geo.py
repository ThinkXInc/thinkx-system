#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/geo.py
# 
# geo service apis
#
# APIs:
#   - /v1/geo/address/ja/getbypostalcode
#
#

from api.responses.api_errors import InvalidZipCodeFormatError, AddressNotFoundError
from flask import Blueprint
from models.address import Address


blueprint_geo = Blueprint('geo', __name__)


@blueprint_geo.route('/v1/geo/address/ja/getbypostalcode', methods=['POST'])
def get_address_ja_by_postalcode():
    """Get japanese address by postal code

    params:
        - postalcode (str)  # ex. 107-0052, 1070052
    returns:
        - address  # address
    """

    # validate postal code format
    # NOTE: raise InvalidZipCodeFormatError if invalid
    zipcode = ''

    # find address
    address = Address.findOne({'zipcode': zipcode})
    if not address:
        raise AddressNotFoundError(zipcode)

    # returns address object
    return address.resonse_json()