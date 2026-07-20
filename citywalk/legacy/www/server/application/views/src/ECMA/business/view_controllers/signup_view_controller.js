'use strict'
/**
 * @fileoverview business/view_controllers/signup_view_controller.js
 * SignupView controller class.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/
 

/**
 * Data model for SignupView.
 */
class SignupDataModel extends InputPageViewDataModel {
    // page 1
    organization_name
    organization_type
    business_description
    country // ISO3611-1 country code eg. 'JA'
    // page 2
    zipcode
    city
    province
    address1
    address2
    tel_country_code // ISO3611-1 dial eg. '81'
    tel
    lat
    lng
    // page 3
    first_name
    last_name
    email
    password
    password_confirm

    constructor(defaults = {}) {
        super(defaults);
        // TODO:
        //  inherit constructor in child class by 
        //  super(defaults);
        //  then call Object.assign in the constructor of InputPageViewDataModel
        Object.assign(this, defaults);
    }
}

/**
 * SignupViewController class.
 * 
 * This is a subclass of InputPageViewController class.
 * 
 * [API and validations]
 *   Validations are performed on both the view and the server.
 * 
 *   The API is required to return the response as below.
 *      - success 
 *          200 status
 *      - error
 *          any status and the error object as,
 *          'errors': {
 *                   'field_name': 'error_message',
 *                   'field_name2': 'error_message2',
 *                  ..}
 * 
 *   The request to /signup validates all fields.
 *   If it returns success, the signup process is done.
 * 
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {2-dim array} pages - [[page 0 list of components], [page 1 ],..]
 * @param {2-dim array} requiredFields - [[page 0 list of fieldName], [page 1 ],..]
 * @param {dict} alertMessages - {'fieldName': 'message'}
 * @param {class} dataModelClass - data model to be submitted
 * @param {array} validations - {'componentId': [errorType, "error message key", [arg1, arg2,..]]}
 * @param {dict} locale - locale json
 * @param {string} lang - initial language e.g. ja
 * @constructor
 */
class SignupViewController extends InputPageViewController {
    __next_button_1_id__ = 'signupViewPage1NextButton';
    __next_button_2_id__ = 'signupViewPage2NextButton';
    __next_button_3_id__ = 'signupViewPage3NextButton';
    __back_button_2_id__ = 'signupViewPage2BackButton';
    __back_button_3_id__ = 'signupViewPage3BackButton';
    __alert_ids__ = [
        'signupViewPage1AlertMessage',
        'signupViewPage2AlertMessage',
        'signupViewPage3AlertMessage'
    ]

    constructor(
            _id, pages, requiredFields, alertMessages, dataModelClass,
            validations, locale, lang, cookieExcludes) {
        super(
            _id, pages, requiredFields, alertMessages, dataModelClass,
            validations, locale, lang, cookieExcludes);
    }

    /**
     * Called when the view is fully loaded.
     * @override @implements
     * 
     */
    _viewLoaded() {
        console.log(`${this.__id__} view is fully loaded.`);
    }

    /**
     * Callback handler when a TextField is unfocused.
     * @override @implements
     * 
     * @param {TextField} textField 
     */
    _textFieldUnFocus(textField, value) {
        super._textFieldUnFocus(textField, value);
        // NOTE: remove this function if unnecessary
    }

    /**
     * Callback handler when a DropdownButton is selected.
     * @override @implements
     * 
     * @param {DropdownButton} dropdownButton 
     */
    _dropdownButtonSelected(dropdownButton, selected) {
        super._dropdownButtonSelected(dropdownButton, selected);
        // NOTE: remove this function if unnecessary
    }

    /**
     * Callback handler when a PositionMap.pointerCoordinate is updated.
     * @interface
     * 
     * @param {Coordinate} newCoordinate 
     */
    _positionMapPointerCoordinateUpdated(positionMap, newCoordinate) {
        super._positionMapPointerCoordinateUpdated(positionMap, newCoordinate);
        // NOTE: seems to be unnecessary.
        // Remove here if there's no problem.
        // // set newCoordinate to this.values
        // this._setValuesForKeys(
        //     {
        //         'lat': newCoordinate.lat,
        //         'lng': newCoordinate.lng
        //     }
        // )
    }

    /**
     * Called when a value was changed.
     * @override @implements
     * 
     * Called when a TextField is input changed or,
     * Called when a DropdownButton is selected.
     * 
     * @param {TextField/DropdownButton} component
     * @param {string} value
     */
    _valueChanged(component, value) {
        super._valueChanged(component, value);
        // show alert on the component when something's wrong
        this._validateComponent(component, value);
    }

    /**
     * Run validation for a single component.
     * @override @implements
     * 
     * @param {TextField/DropdownButton} component 
     * @param {text/number} value 
     * @returns {text/bool} error message if an error found. if no, returns true.
     */
    _validateComponent(component, value) {
        super._validateComponent(component, value);
    }

    /**
     * Called when a field fires onblur event.
     * @override @implements
     * 
     * Called when _textFieldUnFocus or _dropdownButtonSelected is called.
     * 
     * @param {TextField/DropdownButton} component
     * @param {string} value
     */
    _unfocused(component, value) {
        super._unfocused(component, value);
        switch (component.__id__) {
            // page 0
            case 'signupViewOrganizationNameTextField':
            case 'signupViewOrganizationTypeDropdownButton':
            case 'signupViewOrganizationBusinessDescriptionTextField':
            case 'signupViewCountryDropdownButton':
                break;
            // page 1
            case 'signupViewZipcodeTextField':
            case 'signupViewProvinceTextField':
            case 'signupViewCityTextField':
            case 'signupViewAddress1TextField':
                this._updateCoordinateFromAddressFields(component, value);
                break;
            case 'signupViewAddress2TextField':
            case 'signupViewTelCountryCodeDropdownButton':
            case 'signupViewTelTextField':
                break;
            // page 2
            case 'signupViewMemberFirstNameTextField':
            case 'signupViewMemberLastNameTextField':
            case 'signupViewEmailTextField':
            case 'signupViewPasswordTextField':
            case 'signupViewPasswordConfirmTextField':
                break;
        }
    }

    /**
     * Observe address fields.
     */
    _updateCoordinateFromAddressFields(updatedComponent, newValue) {
        switch (updatedComponent.__id__) {
            case 'signupViewZipcodeTextField':
            case 'signupViewProvinceTextField':
            case 'signupViewCityTextField':
            case 'signupViewAddress1TextField':
                // if all values are filled, get coordinate by geocoding API
                const requirements = ['zipcode', 'province', 'city', 'address1'];
                if (
                    requirements.every((key) => {
                        return this._values[key] != null;
                    })) {
                        const country = this._values['country'];
                        const province = this._values['province'];
                        const city = this._values['city'];
                        const address1 = this._values['address1'];
                        if (country == null) {
                            console.error('[observeAddressFields] country must not be null.')
                        }
                        geocodeAddressToCoordinate(
                            country, province, city, address1,
                            (coordinate) => {
                                // Coordinate object gotten
                                console.log(coordinate);
                                // set new coordinate to positionMap 
                                let positionMap = this._componentById('signupViewPositionMap')
                                positionMap.mapCoordinate = coordinate
                                positionMap.pointerCoordinate = coordinate
                                positionMap.updateMapPointer(coordinate)
                                // update values
                                //this._setValuesForKeys(
                                //    {
                                //        'lat': coordinate.lat,
                                //        'lng': coordinate.lng,
                                //    })
                            },
                            (error) => {
                                console.log(error);
                            });
                    } else {
                        console.log(`some value of ${requirements} are missing.`)
                    }
            default:
                break;
        }
    }

    /**
     * Callback handler when the NextButton is tapped.
     * @override @implements
     * 
     * @param {NextButton} nextButton 
     */
    _nextButtonTapped(nextButton) {
        super._nextButtonTapped(nextButton);
        console.log(`${nextButton.__id__} tapped.`)
        // start loading
        this._loading(true);
        //this.page = this.page + 1 // DEBUG: 
        //this._loading(false); // DEBUG:
        // validate each field
        const errors = this._validateForPage(this.page);
        if (errors.length > 0) {
            console.table(errors);
            this._loading(false);
            return
        } else {
            // all validation passed
            switch (this.page) {
                case 0:
                    this.page = 1;
                    this._loading(false);
                    break;
                case 1:
                    this.page = 2;
                    this._loading(false);
                    break;
                case 2:
                    //window.location.href = '/business/home';
                    console.log('------> Request Payload');  // DEBUG:
                    console.table(this._values);
                    console.log(`[Request data] ${this._values.json()}`);
                    console.log('<------ Request Payload');  // DEBUG:
                    this._submit();
                    //this._loading(false);
                    break;
                case 3:
                    //this._submit();
                    break;
            }
        }
    }

    /**
     * Submit data.
     * 
     */
    _submit() {
        // HTTP POST /signup?page={this.page}
        const url = `${app.routes.SIGNUP}`;

        // send data
        this._post(
            url, 
            (res)=>{
                // success object returned.
                if (!('error' in res)) {
                    // the success response should be like:
                    // {
                    //   'saved_data': user.response_json(),
                    //   'user_id': user_id,
                    //   'success': {
                    //       'code': 201,
                    //       'message': 'new user created.'
                    // }
                    console.log(`[success] ${url} => ${res.success.code} ${res.success.message}`);
                    this._setAlertMessage(this.__alert_ids__[this.page], '');

                    setTimeout(()=>{ this._loading(false); }, 1000);
                    // go to the finish page
                    this.page = 3;
                    // reset cookie strage
                    this._resetValuesInCookie();

                // error object returned.
                } else {
                    // the error response should be like:
                    // {
                    //   'saved_data': user.response_json(),
                    //   'error': {
                    //     'key': 'user_id',
                    //     'code': ErrorCode.BAD_REQUEST.value,
                    //     'reason': 'BAD_REQUEST',
                    //     'message': f'{user_id} is invalid as user_id.'
                    // }
                    console.log(`[error] ${url} => ${res.error.code} ${res.error.reason}`);

                    // handle by error types
                    if ('errors' in res) {
                        // validation error
                        console.log(`${res.errors.length} errors found.`);
                        this._setAlertMessage(this.__alert_ids__[this.page], '');
                        res.errors.forEach((error) => {
                            console.warn(`[key] ${error.key} [message] ${error.message}`);
                            // turn on alert
                            let component = this._componentByFieldName(error.key)
                            console.log(component)
                            component.alert(true, message);
                        })
                    } else {
                        // request error
                        let message = res.error.message; 
                        this._setAlertMessage(this.__alert_ids__[this.page], message);
                    }
                }
            },
            // request error
            (res)=> {
                console.warn('↑↑↑↑ API request error');
                setTimeout(()=>{ this._loading(false); }, 1000);
            })

    }

    /**
     * Callback handler when the BackButton is tapped.
     * @override @implements
     * 
     * @param {BackButton} backButton 
     */
    _backButtonTapped(backButton) {
        super._backButtonTapped(backButton);
        if (backButton.__id__ == this.__back_button_2_id__) {
            console.log(`${this.__back_button_2_id__} tapped.`)
            this.page = 0;
        }
        if (backButton.__id__ == this.__back_button_3_id__) {
            console.log(`${this.__back_button_3_id__} tapped.`)
            this.page = 1;
        }
    }

    /**
     * Callback handler when TextField input changed.
     * @override @implements
     * 
     * @param {TextField} textField 
     * @param {string} value
     */
    _textFieldInputValueChanged(textField, value) {
        super._textFieldInputValueChanged(textField, value);
        // update values
    }

    /**
     * Start loading action.
     * @override @implements
     * 
     * @param {DOM element} $loading
     */
    _startLoading($loading) {
        toggleGradientLoader($loading, true);
    }

    /**
     * Stop loading action.
     * @override @implements
     * 
     * @param {DOM element} $loading
     */
    _stopLoading($loading) {
        toggleGradientLoader($loading, false);
    }


    /**
     * Set AlertMessage.message.
     * @override @implements
     * 
     * @param {string} alertMessageId
     */
    _setAlertMessage(alertMessageId, message) {
        super._setAlertMessage(alertMessageId, message);
    }
}