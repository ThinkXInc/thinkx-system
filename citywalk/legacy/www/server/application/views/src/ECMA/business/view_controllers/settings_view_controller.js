'use strict'
/**
 * @fileoverview business/view_controllers/settings_view_controller.js
 * SettingsView controller class.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/

/**
 * Data model for SignupView.
 */
class SettingsDataModel extends InputPageViewDataModel {
    // basics

    // organization
    organization_name
    organization_type
    business_description
    country // ISO3611-1 country code eg. 'JA'
    zipcode
    city
    province
    address1
    address2
    tel_country_code // ISO3611-1 dial eg. '81'
    tel
    lat
    lng

    // organization member
    first_name
    last_name
    email

    constructor(defaults = {}) {
        super(defaults);
        // TODO:
        //  inherit constructor in child class by 
        //  super(defaults);
        //  then call Object.assign in the constructor of InputPageViewDataModel
        Object.assign(this, defaults);
    }

    /**
     * Initialize from session objects.
     * 
     * @param {Organization} organization 
     * @param {OrganizationMember} organizationMember 
     * @returns 
     */
    static fromSession(organization, organizationMember) {
        let d = {};
        // organization
        Object.keys(organization).forEach((key) => {
            if (key == 'name') {
                d['organization_name'] = organization.name;
            } else if (key == 'type') {
                d['organization_type'] = organization.type;
            } else {
                d[key] = organization[key]
            }
        })
        // organization member
        Object.keys(organizationMember).forEach((key) => {
            d[key] = organizationMember[key];
        })
        return new SettingsDataModel(d);

    }
}

/**
 * Settings submit URLs Enum.
 */
const SettingsSubmitType = Object.freeze({
    basics: '/settings/basic/update',
    organization: '/organization/update',
    organization_member: '/organization_member/update',
});


/**
 * SettingsViewController class.
 * 
 * This is a subclass of InputPageViewController class.
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
class SettingsViewController extends InputPageViewController {
    __view_id__ = 'settingsView'
    __main_container_id__ = 'settingsViewMainContainer'
    __center_container_id__ = 'settingsViewCenterContainer'
    __left_container_id__ = 'settingsViewLeftContainer'
    __input_page_view_container_id__ = 'inputPageViewContainer'
    __page_navigation_view_id__ = 'settingsViewPageNavigationView'
    __page_navigation_view_locale_key_home__ = 'page_navigation_view_home';
    __page_navigation_view_locale_key_settings__ = 'page_navigation_view_settings';
    __tab_basics_id__ = 'settingsViewNavigationMenuTabBasics';
    __tab_organization_id__ = 'settingsViewNavigationMenuTabOrganization';
    __tab_organization_member_id__ = 'settingsViewNavigationMenuTabOrganizationMember';
    __tab_icon_src_genral__ = '/img/icons/knight.png';
    __tab_icon_src_organization__ = '/img/icons/rook.png';
    __tab_icon_src_organization_member__ = '/img/icons/queen.png';
    __tab_locale_key_genral_title__ = 'navigation_menu_title_basics';
    __tab_locale_key_organization_title__ = 'navigation_menu_title_organization';
    __tab_locale_key_organization_member_title__ = 'navigation_menu_title_organization_member';
 
    __next_button_1_id__ = 'settingsViewPage1NextButton';
    __next_button_2_id__ = 'settingsViewPage2NextButton';
    __next_button_3_id__ = 'settingsViewPage3NextButton';
    __back_button_2_id__ = 'settingsViewPage2BackButton';
    __back_button_3_id__ = 'settingsViewPage3BackButton';
    __alert_ids__ = [
        'settingsViewPageBasicsAlertMessage',
        'settingsViewPageOrganizationAlertMessage',
        'settingsViewPageOrganizationMemberAlertMessage'
    ]

    constructor(
            _id, pages, requiredFields, alertMessages, dataModelClass,
            validations, locale, lang, cookieExcludes) {
        super(
            _id, pages, requiredFields, alertMessages, dataModelClass,
            validations, locale, lang, cookieExcludes);
        this._makeView();
        this._initObservers()
    }

    /**
     * Make PageNavigationView
     * 
     * [notice] call after creating settingsViewCenterContainer
     * 
     */
    _makePageNavigationView() {
        this.$pageNavigationView = document.createElement('div')
        this.$pageNavigationView.id = this.__page_navigation_view_id__;
        this.$pageNavigationView.classList.add('pageNavigationView');
        document.getElementById(this.__input_page_view_container_id__).prepend(this.$pageNavigationView);

        this.pageNavigationView = new PageNavigationView(this.__page_navigation_view_id__);

        this.pageNavigationView.pageRoutes = [
            new PageRoute(this._locale[this.__page_navigation_view_locale_key_home__][this._lang], '/'),
            new PageRoute(this._locale[this.__page_navigation_view_locale_key_settings__][this._lang], '/'),
        ]
        this.pageNavigationView.state = PageNavigationViewState.attop;
    }

    /**
     * Make Navigation Menu and Tabs DOM Elements
     */
    _makeNavigationMenu() {
        this.$settingsView = document.getElementById(this.__view_id__);

        // menu
        this.$menu = document.createElement('ul');
        this.$menu.id = `${this.__id__}NavigationMenu`;
        this.$menu.classList.add(this.$menu.id);

        // menu tab
        function createTab(
                key, $menu, iconImgSrc, locale, lang, localeKey) {
            let $label = document.createElement('span'); 
            $label.classList.add('label');
            $label.innerText = locale[localeKey][lang];
            let $icon = document.createElement('img');
            $icon.classList.add('icon');
            $icon.src = iconImgSrc;
            $icon.srcset = iconImgSrc.replace('.', '@2x.');
            let $tab = document.createElement('li');
            $tab.id = `${$menu.id}Tab${key}`;
            $tab.classList.add(`${$menu.id}Tab`);
            $tab.classList.add($tab.id);
            $tab.appendChild($icon);
            $tab.appendChild($label);
            $menu.appendChild($tab);
            return $tab;
        }

        this.$tabBasics = createTab('Basics', this.$menu, this.__tab_icon_src_genral__,
            this._locale, this._lang, this.__tab_locale_key_genral_title__);
        this.$tabOrganization = createTab('Organization', this.$menu, this.__tab_icon_src_organization__,
            this._locale, this._lang, this.__tab_locale_key_organization_title__);
        this.$tabOrganizationMember = createTab('OrganizationMember', this.$menu, this.__tab_icon_src_organization_member__,
            this._locale, this._lang, this.__tab_locale_key_organization_member_title__);

        this.$settingsView.appendChild(this.$menu);
    }



    /**
     * Make view
     */
    _makeView() {
        // make navigation menu
        this._makeNavigationMenu();

        // main container
        let $mainContainer = document.createElement('div');
        $mainContainer.id = this.__main_container_id__;
        $mainContainer.classList.add('mainContainer');
        this.$settingsView.appendChild($mainContainer);

        // organize elements (left)
        let $leftContainer = document.createElement('div');
        $leftContainer.id = this.__left_container_id__;
        $leftContainer.classList.add('leftContainer');
        $mainContainer.appendChild($leftContainer);
        $leftContainer.appendChild(this.$menu);

        // organize elements (center)
        let $centerContainer = document.createElement('div');
        $centerContainer.id = this.__center_container_id__;
        $centerContainer.classList.add('centerContainer');
        $mainContainer.appendChild($centerContainer);
        //this.__alert_ids__.forEach((id) => {
        //    $centerContainer.prepend(
        //        document.getElementById(id))
        //})
        $centerContainer.appendChild(
            document.getElementById('inputPageViewContainer'))

        // pageNavigationView
        this._makePageNavigationView();
    }

    /**
     * Initialize observers.
     */
    _initObservers() {
        const _this = this;

        // load event
        window.addEventListener('load', (event) => {
            console.log('window on load')
            const url = PageControl.getUrl()
            if (url.includes('#organization')) {
                // open organization settings
            } else if (url.includes('#member')) {
                // open organization member settings

            } else {

            }
        });

        // tab
        this.$tabBasics.addEventListener('click', (e) => {
            _this.page = 0;
        })
        this.$tabOrganization.addEventListener('click', (e) => {
            _this.page = 1;
        })
        this.$tabOrganizationMember.addEventListener('click', (e) => {
            _this.page = 2;
        })

    }

    /**
     * Switch Tab Active.
     * 
     * @param {Int} page
     */
    _switchTabActive(page) {
        document.getElementById(this.__tab_basics_id__).classList.remove('active');
        document.getElementById(this.__tab_organization_id__).classList.remove('active');
        document.getElementById(this.__tab_organization_member_id__).classList.remove('active');
        switch(page) {
            case 0:
                document.getElementById(this.__tab_basics_id__).classList.add('active');
                break;
            case 1:
                document.getElementById(this.__tab_organization_id__).classList.add('active');
                break;
            case 2:
                document.getElementById(this.__tab_organization_member_id__).classList.add('active');
                break;
        }
    }


    /**
     * Called when page changed.
     * @override @implements
     * 
     * @param {Int} page
     */
    _pageChanged(page) {
        // NOTE: override this function
        this._switchTabActive(page);
        // update page navigation view
        this._updatePageNavigationView(page);
    }

    /**
     * Update pageNavigationView
     * 
     * @param {Int} page 
     */
    _updatePageNavigationView(page) {
        switch (page) {
            case 0:
                this.pageNavigationView.pageRoutes = [
                    new PageRoute(this._locale[this.__page_navigation_view_locale_key_home__][this._lang], '/business/home'),
                    new PageRoute(this._locale[this.__page_navigation_view_locale_key_settings__][this._lang], '/business/settings'),
                    new PageRoute(this._locale[this.__tab_locale_key_genral_title__][this._lang], '/business/settings#page=0'),
                ]
                break
            case 1:
                this.pageNavigationView.pageRoutes = [
                    new PageRoute(this._locale[this.__page_navigation_view_locale_key_home__][this._lang], '/business/home'),
                    new PageRoute(this._locale[this.__page_navigation_view_locale_key_settings__][this._lang], '/business/settings'),
                    new PageRoute(this._locale[this.__tab_locale_key_organization_title__][this._lang], '/business/settings#page=1'),
                ]
                break
            case 2:
                this.pageNavigationView.pageRoutes = [
                    new PageRoute(this._locale[this.__page_navigation_view_locale_key_home__][this._lang], '/business/home'),
                    new PageRoute(this._locale[this.__page_navigation_view_locale_key_settings__][this._lang], '/business/settings'),
                    new PageRoute(this._locale[this.__tab_locale_key_organization_member_title__][this._lang], '/business/settings#page=2'),
                ]
                break;
        }
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
        switch (component.__id__) {
            // basics

            // organization
            case 'settingsViewOrganizationNameTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.'
                    component.alert(true, 'this field is required.');
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewOrganizationTypeDropdownButton':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.'
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewOrganizationBusinessDescriptionTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, );
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewCountryDropdownButton':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.'
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewZipcodeTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true,);
                    return msg
                } else if (!super._validateFormat(value, RegexType.postalcode)) {
                    const msg = 'Invalid postal code format. e.g. 123-4567.';
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewCityTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewProvinceTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewAddress1TextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewAddress2TextField':
                if (!super._validateLength(value, 0, component.__max_text_count__)) {
                    const msg = `length must be ~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewTelCountryCodeDropdownButton':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.'
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewTelTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateFormat(value, RegexType.tel)) {
                    const msg = 'Invalid tel code format. e.g. 03-4567-3333.';
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;

            // organization member 
            case 'settingsViewMemberFirstNameTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewMemberLastNameTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
                    const msg = `length must be 1~${component.__max_text_count__}`;
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewEmailTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateFormat(value, RegexType.email)) {
                    const msg = 'Invalid email format. e.g. name@domain.com.';
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewPasswordTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (!super._validateFormat(value, RegexType.password)) {
                    const msg = 'Password must be more than 8charactors with alphabet and numbers.';
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
            case 'settingsViewPasswordConfirmTextField':
                if (!super._validateNotNull(value) || value == '') {
                    const msg = 'this field is required.';
                    component.alert(true, msg);
                    return msg
                } else if (value != this._values['password']) {
                    const msg = 'Password is not corresponding';
                    component.alert(true, msg);
                    return msg
                } else {
                    component.alert(false);
                    return true
                };
                break;
        }
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
            // basic

            // organization
            case 'settingsViewOrganizationNameTextField':
            case 'settingsViewOrganizationTypeDropdownButton':
            case 'settingsViewOrganizationBusinessDescriptionTextField':
            case 'settingsViewCountryDropdownButton':
            case 'settingsViewZipcodeTextField':
            case 'settingsViewProvinceTextField':
            case 'settingsViewCityTextField':
                break;
            case 'settingsViewAddress1TextField':
                this._updateCoordinateFromAddressFields(component, value);
                break;
            case 'settingsViewAddress2TextField':
            case 'settingsViewTelCountryCodeDropdownButton':
            case 'settingsViewTelTextField':
                break;
            // organization member
            case 'settingsViewMemberFirstNameTextField':
            case 'settingsViewMemberLastNameTextField':
            case 'settingsViewEmailTextField':
            case 'settingsViewPasswordTextField':
            case 'settingsViewPasswordConfirmTextField':
                break;
        }
    }

    /**
     * Observe address fields.
     */
    _updateCoordinateFromAddressFields(updatedComponent, newValue) {
        switch (updatedComponent.__id__) {
            case 'settingsViewZipcodeTextField':
            case 'settingsViewProvinceTextField':
            case 'settingsViewCityTextField':
            case 'settingsViewAddress1TextField':
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
                                let positionMap = this._componentById('settingsViewPositionMap')
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
        const hasError = this._alertPageErrors(errors);
        if (hasError) {
            this._loading(false);
            return
        } else {
            // all validation passed
            //window.location.href = '/business/home';
            console.log('------> Request Payload');  // DEBUG:
            console.table(this._values);
            console.log(`[Request data] ${this._values.json()}`);
            console.log('<------ Request Payload');  // DEBUG:
 
            switch (this.page) {
                case 0:
                    this._submit(SettingsSubmitType.basics);
                    break;
                case 1:
                    this._submit(SettingsSubmitType.organization);
                    break;
                case 2:
                    this._submit(SettingsSubmitType.organization_member);
                    break;
            }
        }
    }

    /**
     * Submit data.
     * 
     * @param {SettingsSubmitType} submitTo
     */
    _submit(submitTo) {
        let url = submitTo;

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
 

