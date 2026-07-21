'use strict'
/**
 * @fileoverview business/view_controllers/input_page_view_controller.js
 * InputPageView controller class.
 * 
 * This class is the super class for SignupViewController, SignupViewController, etc.
 * The views are composed of view components below.
 * 
 *  - TextField from textfield.js (text input)
 *  - DropdownButton from dropdown_button.js (select with table)
 *  - RadioButton from radio_button.js (select with radio buttons) *todo
 *  - Title
 *  - Description
 *  - FieldTitle *todo
 *  - FieldDescription *todo
 *  - AlertText
 *  - NextButton
 *  - BackButton
 * 
 * The subclasses of InputPageViewController mainly work on the validation of each form values. 
 * 
 * This class provides with common functions below.
 *  1. The value is retained in the cookie at each page transition
 *  2. The URL is rewritten in JS for each screen transition.
 *  3. So that the value is not lost when the browser reloads or backs.
 * 
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/

const RegexType = Object.freeze({
    email: /^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/i,
    password: /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z]{8,}$/,
    postalcode: /^(?:[A-Z0-9]+([- ]?[A-Z0-9]+)*)?$/,
    tel: /^[\+]?[(]?[0-9]{2,3}[)]?[-\s\.]?[0-9]{4,6}[-\s\.]?[0-9]{4,6}$/im,
})


const ValidationErrorType = Object.freeze({
    required: 0,
    length: 1,
    format: 2,
    notcorrespond: 3
})


/**
 * InputPageViewController DataModel class.
 * 
 * @param {dict} defaults default key:value of fields retrieved from _restoreValuesFromCookie()
 * @constructor 
 */
class InputPageViewDataModel {

    // TODO:
    //  inherit constructor in child class by 
    //  super(defaults);
    // 
    // NOTE:
    //  Object.assign(this, defaults);
    //  doesn't refer to the child object.

    //constructor(defaults = {}) {
    //    Object.assign(this, defaults);
    //}
 
    /**
     * Convert object to json.
     * 
     * @returns {json} convert to json string
     */
    json() {
        return JSON.stringify(this);
    }

}



/**
 * InputPageViewController class.
 * 
 * <code>
 *   class User {
 *      first_name = null;
 *      last_name = null;
 *      country = null;
 *      constractor(first_name, last_name, country) {
 *        this.first_name = first_name;
 *        this.last_name = last_name;
 *        this.country = country;
 *      }
 *   }
 *   class SignupViewController extends InputPageViewController {
 *      constractor(_id, pages, dataModelClass) {
 *        super(_id, pages, dataModelClass)
 *      }
 *   }
 *   let vc = SignupViewController(
 *     'SignupView',
 *     [
 *        # Page 1
 *        [
 *          new Title('signupViewPage1Title', 'You are welcome.'),
 *          new Description('signupViewPage1Description', 'Welcome to this useful website.'),
 *          new FieldTitle('signupViewNameTitle', 'Your Name Here'),
 *          new TextField('sugnupViewFirstNameTextField', TextFieldType.singleline,
 *                        'First Name', 'first_name', 'Satoshi', 100, 1, false),
 *          new TextField('sugnupViewLastNameTextField', TextFieldType.singleline,
 *                        'Last Name', 'last_name', 'Nakamoto', 100, 1, false),
 *          new FieldTitle('signupViewCountryTitle', 'Your Country'),
 *          new FieldDescription('signupViewCountryTitle',
 *                               '"Your Counrty" means where you were born.'),
 *          new DropdownButton(
 *               'countrySelectButton', 'Your Country', 'Please select your country.',
 *               'country',
 *               DropdownMenuType.list, 
 *               DropdownMenuDisplayPositionType.upper,
 *               [
 *                   new ListMenu('Afganistan', 0),
 *                   new ListMenu('Belarus', 1),
 *                   new ListMenu('China', 2),
 *                   new ListMenu('Denmark', 3),
 *                   ...
 *               ]);
 *        ],
 *        # Page 2
 *        [
 *          new Title('signupViewPage2Title', 'You are welcome again.'),
 *          ...
 *        ],
 *        ...
 *     ],
 *     User
 *   )
 * 
 * 
 *   // write these on signup.html
 *   <section id={_id} class=inputPageView>
 *     // page 1
 *     <div id=signupViewPage1Title class=inputPageViewPageTitle>...</div>
 *     <div id=signupViewPage1Description class=inputPageViewPageDescription>...</div>
 *     <div id=signupViewFirstNameTextField class=textField>...</div>
 *     <div id=signupViewLastNameTextField class=textField>...</div>
 *     // page 2
 *     <div id=signupViewPage2Title class=inputPageViewPageTitle>...</div>
 *     ...
 *   </section>
 *
 *   // After the initialization, InputPageViewController finally generates 
 *   <section id={_id} class=inputPageView>
 *     <!-- ↓↓↓ these DOM elements are dinamically created ↓↓↓ -->
 *     <div class=inputPageViewContainer>
 *       <ul class=inputPageViewPages>
 *         <li class=inputPageViewPage data-pageIndex=0>
 *           <div id=signupViewPage1Title class=inputPageViewPageTitle>...</div>
 *           <div id=signupViewPage1Description class=inputPageViewPageDescription>...</div>
 *           <div id=signupViewFirstNameTextField class=textField>...</div>
 *           <div id=signupViewLastNameTextField class=textField>...</div>
 *           ...
 *         </li>
 *         <li class=inputPageViewPage data-page-index=1>
 *           <div id=signupViewPage2Title class=inputPageViewPageTitle>...</div>
 *         </li>
 *       </ul>
 *     </div>
 *     <!-- ↑↑↑ these DOM elements are dinamically created ↑↑↑ -->
 *   </section>
 * 
 * </code>
 * 
 * Usages:
 *  1. Set values of fields
 *      eg.
 *      newValues['name'] = name
 *      this.values = newValues  // automatically store into the cookie strage
 * 
 *      this.setValueForKey('name') = name  // direct insert
 *      x this.values['name'] = name  // not allowed to modify a property directly
 * 
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {list} pages - 2-dimentional array of components. (see the sample above)
 * @param {data model} dataModelClass - data model class to be submit to the server.
 * @param {array} validations - {'componentId': [errorType, "error message key", [arg1, arg2,..]]}
 * @param {dict} locale - locale json
 * @param {string} lang - initial language e.g. ja
 * @property @private
 * @property @public
 * @interface _nextButtonTapped(nextButton)
 * @method @private
 * @method @public
 * @constructor
 */
class InputPageViewController {
    __id__ = null;
    __number_of_pages__ = null;
    __data_model__ = null;
    __loading_element_id__ = "input_page_view_controller_loading";
    __cookie_excludes__ = []; 

    _page = null;
    _values = {};

    _components = [];
    _pageComponents = [];  // [[comp 0 in page 0, comp 1 in page 0, ..], [..],..]
    _pageErrors = [];  // [[[component, 'error message'], []],..]
    _validations = [];  // {'componentId': [errorType, "error message key", [arg1, arg2,..]]}

    _locale = null;
    _lang = null;

    constructor(_id, pages, dataModelClass, defaults, validations, locale, lang, cookieExcludes=[]) {
        this.__id__ = _id;

        // setup page components
        if (pages.length == 0) {
            console.error(`${this.__id__} requires a list of pages with components.`)
        }
        pages.forEach((components, i) => {
            if (components.length == 0) {
                console.error(`${this.__id__} page ${i} requires at least 1 component.`)
            }
        })
        this._setElements(pages);

        // set events
        this._setEventHandlers();

        // data model
        this.__data_model__ = dataModelClass;
        this.__cookie_excludes__ = cookieExcludes;
        //this._resetValuesInCookie(); // DEBUG:
        if (defaults == null) {
           defaults = this._restoreValuesFromCookie();
        } else {
            this._setValuesToFields(defaults);
        }
        console.table(defaults);
        this._values = new dataModelClass(defaults);
        console.table(this._values);
        console.log(`data model for ${this.__id__} initialized`);

        // errors
        this._pageErrors = Array(pages.length);

        // validations
        this._validations = validations;
        console.log(this._validations)

        // locale
        this._locale = locale;
        this._lang = lang;
        console.log(locale);
        console.log(lang);
        if (this._locale == null) {
            console.warn(`no locale json data found.`);
        } else {
            console.log('locale json data found');
        }
        if (this._lang == null) {
            console.warn(`no language information is given.`);
        } else {
            console.log(`initial language is set as ${lang}`);
        }
    }

    /**
     * page setter.
     * 
     * Display only the page in current state.
     */
    set page(page) {
        const previousPage = this._page;
        console.log(`page changed ${previousPage} -> ${page}`)
        this._page = page;
        // display only the page in current state.
        let $pages = this.$inputPageView.querySelectorAll('.inputPageViewPage')
        $pages.forEach(($page, i) => {
            if (parseInt($page.dataset.pageIndex) == this._page) {
                $page.classList.add('show');
                $page.style.display = "flex";
                $page.style.flexDirection = "column";
            } else {
                $page.classList.remove('show');
                $page.style.display = "none";
            }
        })
        if (!(isNaN(this._page))) {
            // call interface
            this._pageChanged(this._page);
            // update browser's url
            this._updatePageNumberInBrowswerURL(this._page);
        }
    }

    /**
     * page getter.
     */
    get page() {return this._page}

    /**
     * values setter
     * 
     * NOTICE: 
     * when modify a property in values,
     * use `setValueForKey(key, value)`
     * , instead values[key] = value
     */
    set values(values) {
        const previous = this._values;
        this._values = values;
        console.log(`values changed`);
        console.table(this._values);

        // sync with cookie storage
        this._setValuesToCookies(this._values);
    }

    /**
     * values getter 
     */
    get values() {return this._values}

    /**
     * errors setter
     */
    set errors(errors) {
        const previous = this._errors;
        this._errors = errors;
        console.log(`errors changed`);
        console.table(this._errors);
    }

    /**
     * errors getter 
     */
    get errors() {return this._errors}


    /**
     * DOM nodes as variables.
     */
    _setElements(pages) {
        this.$inputPageView = document.getElementById(this.__id__);
        if (this.$inputPageView == null) {
            console.warn(
                `<section id=${this.__id__} class=inputPageView></section> is necessary in HTML.`);
        }

        // create loading
        let $loading = document.createElement('div');
        $loading.id = this.__loading_element_id__;
        $loading.style.height = '7px';
        $loading.style.width = '100%';
        this.$inputPageView.prepend($loading);
        this.$loading = $loading;
        console.log('loading element created.')

        // create container
        let $container = document.createElement('div');
        $container.id = 'inputPageViewContainer';
        $container.classList.add($container.id);
        this.$inputPageView.appendChild($container);

        // create pages
        console.log(`${pages.length} pages detected.`)
        let $pages = document.createElement('ul');
        $pages.classList.add('inputPageViewPages');
        pages.forEach((components, i) => {
            console.log(`${this.__id__} page ${i} has ${components.length} components.`);

            // create page DOM element
            let $page = document.createElement('li');
            $page.id = `${this.__id__}Page${i}`;
            $page.classList.add('inputPageViewPage');
            $page.dataset.pageIndex = i;

            // set components
            components.forEach((component, j) => {
                if (component.constructor.name == "Wrapper") {
                    let $wrapper = document.createElement('div');
                    $wrapper.id = component.__id__;
                    $wrapper.classList.add('wrapper');
                    $page.appendChild($wrapper)
                    component.components.forEach((componentInWrapper, k) => {
                        this._setPageComponent(componentInWrapper, $wrapper, i, k)
                    })
                } else {
                    this._setPageComponent(component, $page, i, j);
                }
            });
            $pages.appendChild($page);
        });
        $container.appendChild($pages);
    }

    /**
     * Set page component.
     * 
     * @param {object} component 
     * @param {DOM} $parent 
     * @param {number} pageIndex 
     * @param {number} componentIndex 
     */
    _setPageComponent(component, $parent, pageIndex, componentIndex) {
        let _id = component.__id__;
        if (_id == null) {
            console.error(`page ${pageIndex} component ${componentIndex}: no __id__ is set in the instance.`)
        }
        let $elem = document.getElementById(_id);
        if ($elem == null) {
            console.error(`<div id=${_id}> is nucessary in HTML.`);
        }
        $parent.appendChild($elem);

        // set button event
        if (component.constructor.name == "NextButton") {
            this._setNextButtonEventHandler(component);
        }
        if (component.constructor.name == "BackButton") {
            this._setBackButtonEventHandler(component);
        }

        // set form event
        if (component.constructor.name == "TextField") {
            this._setTextFieldEventHandler(component);
        }
        if (component.constructor.name == "DropdownButton") {
            this._setDropdownButtonEventHandler(component);
        }
        if (component.constructor.name == "RadioButton") {
            this._setValueChangeEventHandler(component);
        }
        if (component.constructor.name == "PositionMap") {
            this._setPositionMapEventHandler(component);
        }

        // keep components in the ViewController instance
        this._components.push(component);
        // keep components in matrix with rows as pages
        if (componentIndex == 0) {
            this._pageComponents.push([]);
        }
        this._pageComponents[pageIndex].push(component);

    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
        window.addEventListener('load', (event) => {
            console.log('** the whole page has been loaded. **');
            _this._viewLoaded();
        })
        window.addEventListener('hashchange', (event) => {
            console.log('hashchange event detected');
            console.log(`url changed. -> ${PageControl.getRelativePath()}`)
            const page = Browswer.getValueFromHash('page', 'int');
            _this.page = page;
        }, false);
    }

    /**
     * update a property of _values
     */
    _setValueForKey(key, value) {
        let values = this._values 
        values[key] = value
        this.values = values
    }

    /**
     * update multiple properties of _values
     * 
     * @param {dict} newValues
     */
    _setValuesForKeys(newValues) {
        let values = this._values 
        Object.keys(newValues).forEach((key) => {
            values[key] = newValues[key]
        })
        this.values = values
    }

    /**
     * Update url ?page= in browser's addressbar.
     * 
     * @param {number} page new page number
     */
    _updatePageNumberInBrowswerURL(page) {
        //browser.updateValueInSearchParams('page', String(page), true);
        if (isNaN(page)) {
            console.error(`invalid page number ${page} of type ${typeof page}`);
            return
        }
        PageControl.updateValueInHash('page', String(page), true);
    }

    /**
     * Set values to Cookie strage.
     * 
     * @description __id__ is prefixed to the save key.  {this.__id__}__{field_name}
     * @param {dict} values {key1: value1, ..} usually this._values
     * @param {number} expires when the cookie will be removed. [days]
     * @param {bool} secure if the cookie transmission requires a secure protocol (https)
     * @param {string} sameSite whether a cookie is sent along with cross-site requests
     */
    _setValuesToCookies(values, expires=3, secure=true, sameSite='strict') {
        const prefix = this.__id__;
        // set all values
        Object.keys(values).forEach((key) => {
            const name = `${prefix}__${key}`
            const value = this._values[key]
            if (value != null && !(this.__cookie_excludes__.includes(key))) {
                // set value if not null
                Cookies.set(
                    name, value,
                    {expires: expires, secure: secure, sameSite: sameSite});
            } else {
                // remove if the value is null
                Cookies.remove(name);
            }
        })
        console.log('cookies saved');
        console.log(Cookies.get());
    }

    /**
     * Get values from Cookie.
     * 
     * @returns {dict} field values {field_name1: value1, ..}
     */
    _getValuesFromCookies() {
        const prefix = this.__id__;
        let valuesInCookie = {};
        this._components.forEach((component) => {
            if (component instanceof TextField || component instanceof DropdownButton) {
                const name = `${prefix}__${component.__field_name__}`;
                const value = Cookies.get(name);
                if (value != null) {
                    valuesInCookie[component.__field_name__] = Cookies.get(name);
                }
            }
            if (component instanceof PositionMap) {
                const name_lat = `${prefix}__${component.__field_name_lat__}`;
                const name_lng = `${prefix}__${component.__field_name_lng__}`;
                const value_lat = Cookies.get(name_lat);
                const value_lng = Cookies.get(name_lng);
                if (value_lat != null) {
                    valuesInCookie[component.__field_name_lat__] = Cookies.get(name_lat);
                }
                if (value_lng != null) {
                    valuesInCookie[component.__field_name_lng__] = Cookies.get(name_lng);
                }
            }
        })
        console.log('-------- cookie strage ------');
        console.table(valuesInCookie);
        return valuesInCookie
    }

    /**
     * Restore values onto components from Cookie.
     * 
     * @returns {dict} values object restored from cookie storage.
     */
    _restoreValuesFromCookie() {
        const valuesInCookie = this._getValuesFromCookies();
        console.table(valuesInCookie);

        // set values to compoents
        this._setValuesToFields(valuesInCookie);

        // store to this._values
        this._storeValues(valuesInCookie);

        return valuesInCookie
    }

    /**
     * Set field values to components from dataModel.
     * 
     * @param {DataModel} dataModel 
     */
    _setValuesToFields(dataModel) {
        // set values to compoents
        this._components.forEach((component) => {
            if (component instanceof TextField || component instanceof DropdownButton) {
                if (!component.__field_name__ in dataModel) {
                    console.warn(`no ${component.__field_name__} field in cookie.`);
                    return
                }
                if (dataModel[component.__field_name__] == null) {
                    console.log(`value of ${component.__field_name__} in cookie is null.`);
                    return
                }
                // set value to fields by the class type
                if (component instanceof TextField) {
                    component.text = dataModel[component.__field_name__];
                }
                if (component instanceof DropdownButton) {
                   component.selectedValue = dataModel[component.__field_name__];
                }
            }
            if (component instanceof PositionMap) {
                if (!component.__field_name_lat__ in dataModel) {
                    console.warn(`no ${component.__field_name_lat__} field in cookie.`);
                    return
                }
                if (!component.__field_name_lng__ in dataModel) {
                    console.warn(`no ${component.__field_name_lng__} field in cookie.`);
                    return
                }
                if (dataModel[component.__field_name_lat__] == null) {
                    console.log(`value of ${component.__field_name_lat__} in cookie is null.`);
                    return
                }
                if (dataModel[component.__field_name_lng__] == null) {
                    console.log(`value of ${component.__field_name_lng__} in cookie is null.`);
                    return
                }
                // set value to fields by the class type
                component.mapCoordinate = new Coordinate(
                    dataModel[component.__field_name_lat__],
                    dataModel[component.__field_name_lng__])
                component.pointerCoordinate = new Coordinate(
                    dataModel[component.__field_name_lat__],
                    dataModel[component.__field_name_lng__])
            }
        })
    }

    
    /**
     * Store values to this._values from dataModel object.
     * 
     * @param {DataModel} dataModel - {'fieldName': val, ..}
     */
    _storeValues(dataModel) {
        // store to this._values
        Object.keys(dataModel).forEach((fieldName) => {
            this._values[fieldName] = dataModel[fieldName];
        });
    }

    /**
     * Initialize Cookie strage.
     * 
     */
    _resetValuesInCookie() {
        const prefix = this.__id__;
        this._components.forEach((component) => {
            if (component instanceof TextField || component instanceof DropdownButton) {
                const name = `${prefix}__${component.__field_name__}`;
                Cookies.remove(name);
                console.log(`${name} removed from cookie.`);
            }
            if (component instanceof PositionMap) {
                const nameLat = `${prefix}__${component.__field_name_lat__}`;
                const nameLng = `${prefix}__${component.__field_name_lng__}`;
                Cookies.remove(nameLat);
                Cookies.remove(nameLng);
                console.log(`${nameLat} removed from cookie.`);
                console.log(`${nameLng} removed from cookie.`);
            }
        })
    }

    /**
     * Set eventListener for the NextButton element.
     * 
     * @param {NextButton} button 
     */
    _setNextButtonEventHandler(button) {
        console.log(`set eventHandler to ${button.__id__}`);
        const _this = this;
        button.$button.addEventListener('click', (e) => {
            _this._nextButtonTapped(button);
        })
    }

    /**
     * Set eventListener for the BackButton element.
     * 
     * @param {BackButton} button 
     */
    _setBackButtonEventHandler(button) {
        console.log(`set eventHandler to ${button.__id__}`);
        const _this = this;
        button.$button.addEventListener('click', (e) => {
            _this._backButtonTapped(button);
        })
    }

    /**
     * Set eventListener for TextField.
     * 
     * @param {TextField} textField
     */
    _setTextFieldEventHandler(textField) {
        console.log(`set eventHandler to ${textField.__id__}`);
        const _this = this;
        textField.$textArea.addEventListener('blur', (e) => {
            _this._textFieldUnFocus(textField, textField.text);
        })
        textField.$textArea.addEventListener('input', (e) => {
            _this._textFieldInputValueChanged(textField, textField.text);
        })
    }

    /**
     * Set eventListener for DropdownButton.
     * 
     * @param {DropdownButton} dropdownButton 
     */
    _setDropdownButtonEventHandler(dropdownButton) {
        console.log(`set eventHandler to ${dropdownButton.__id__}`);
        const _this = this;
        dropdownButton.$dropdownButton.addEventListener('selected', (e) => {
            const value = e.detail.value;
            _this._dropdownButtonSelected(dropdownButton, value);
        })
    }

    /**
     * Set evenetListener for PositionMap.
     * 
     * @param {PositionMap} positionMap
     */
    _setPositionMapEventHandler(positionMap) {
        console.log(`set eventHandelr to ${positionMap.__id__}`);
        const _this = this;
        positionMap.$positionMap.addEventListener('pointerCoordinateUpdated', (e) => {
            const positionMapId = e.detail.__id__;
            const newCoordinate = e.detail.coordinate;
            _this._positionMapPointerCoordinateUpdated(positionMap, newCoordinate);

        })

    }

    /**
     * @interface
     * 
     * Called when the whole page has been loaded.
     * 
     */
    _viewLoaded() {
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Called when page changed.
     * @param {Int} page
     */
    _pageChanged(page) {
        // NOTE: override this function
    }


    /**
     * @interface
     * 
     * Called when the next button is tapped.
     * 
     * @param {NextButton} button 
     */
    _nextButtonTapped(nextButton) {
        console.log(`button ${nextButton.__id__} tapped.`);
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Called when the back button is tapped.
     * 
     * @param {BackButton} backButton 
     */
    _backButtonTapped(backButton) {
        console.log(`button ${backButton.__id__} tapped.`);
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Called when a TextField input changed.
     * 
     * @param {TextField} textField 
     * @param {string} value
     */
    _textFieldInputValueChanged(textField, value) {
        console.log(`textField ${textField.__id__} input with value ${value}.`);
        this._valueChanged(textField, value);
        // NOTE: override this function
        this._setValueForKey(textField.__field_name__, value)
    }

    /**
     * @interface
     * 
     * Called when a TextField is blur(unfocus).
     * 
     * @param {TextField} textField 
     * @param {string} value
     */
    _textFieldUnFocus(textField, value) {
        console.log(`textField ${textField.__id__} onblur with value ${value}.`);
        this._unfocused(textField, value);
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Called when a DropdownButton is selected.
     * 
     * @param {DropdownButton} dropdownButton
     * @param {string} value
     */
    _dropdownButtonSelected(dropdownButton, value) {
        console.log(`dropdownButton ${dropdownButton.__id__} selected with value ${value}.`);
        this._unfocused(dropdownButton, value);
        this._valueChanged(dropdownButton, value);
        // NOTE: override this function
        this._setValueForKey(dropdownButton.__field_name__, value)
    }


    /**
     * @interface
     * 
     * Called when a PositionMap.pointerCoordinate is updated.
     * 
     * @param {Coordinate} newCoordinate 
     */
    _positionMapPointerCoordinateUpdated(positionMap, newCoordinate) {
        console.log(`positionMap ${positionMap.__id__}.pointerCoordinate updated with value ${newCoordinate.lat} ${newCoordinate.lng}`);
        const keyLat = `${positionMap.__field_name_lat__}`;
        const keyLng = `${positionMap.__field_name_lng__}`;
        this._setValuesForKeys(
            {
                [keyLat]: newCoordinate.lat,
                [keyLng]: newCoordinate.lng
            }
        )
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Called when a TextField is input changed or,
     * Called when a DropdownButton is selected.
     * 
     * @param {TextField/DropdownButton} component
     * @param {string} value
     */
    _valueChanged(component, value) {
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Called when a TextField is blur(unfocus) or,
     * Called when a DropdownButton is selected.
     * 
     * @param {TextField/DropdownButton} component
     * @param {string} value
     */
    _unfocused(component, value) {
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Show page alert message.
     * 
     * @param {AlertMessage} alertMessage
     * @param {string} message 
     */
    _setAlertMessage(alertMessageId, message) {
        let alertMessage = this._componentById(alertMessageId);
        if (alertMessage == null) {
            console.error(`AlertMessage component id:${alertMessageId} not found in PageViewController.components`);
        } else {
            console.log(`show alert message ${message} on ${alertMessage.__id__}`);
            alertMessage.message = message;
        }
        // NOTE: override this function
    }

    /**
     * @interface
     * 
     * Run validation for a single component.
     * 
     * @param {TextField/DropdownButton} component 
     * @param {text/number} value 
     * @returns {text/bool} error message if an error found. if no, returns true.
     */
    _validateComponent(component, value) {
        // this._validations =
        //  {'componentId': 
        //         [errorType, "error message", [arg1, arg2,..]]
        //  }
        let hasError = false;
        Object.keys(this._validations).forEach((key) => {
            if (component.__id__ == key) {
                const errorSettings = this._validations[key];

                for (let i = 0; i < errorSettings.length; i++) {
                    const type = errorSettings[i][0]
                    const msg = errorSettings[i][1]
                    const args = (errorSettings[i].length > 2) ? errorSettings[i][2] : [] 

                    switch (type) {
                        case ValidationErrorType.required:
                            if (!this._validateNotNull(value) || value == '') {
                                component.alert(true, msg);
                                hasError = true;
                                return hasError;
                            } 
                        break;
                        case ValidationErrorType.length:
                            if (!this._validateLength(value, args[0], args[1])) {
                                component.alert(true, msg);
                                hasError = true;
                                return hasError;
                            }
                        break;
                        case ValidationErrorType.emailFormat:
                            if (!this._validateFormat(value, RegexType.email)) {
                                component.alert(true, msg);
                                hasError = true;
                                return hasError;
                            }
                        break;
                        case ValidationErrorType.passwordFormat:
                            if (!this._validateFormat(value, RegexType.password)) {
                                component.alert(true, msg)
                                hasError = true;
                                return hasError;
                            }
                        break;
                        case ValidationErrorType.telFormat:
                            if (!this._validateFormat(value, RegexType.tel)) {
                                component.alert(true, msg)
                                hasError = true;
                                return hasError;
                            }
                        break;
                        case ValidationErrorType.postalcodeFormat:
                            if (!this._validateFormat(value, RegexType.postalcode)) {
                                component.alert(true, msg)
                                hasError = true;
                                return hasError;
                            }
                        break;
                    }
                }
            }
            if (!hasError) {
                component.alert(false);
            }
            return hasError
        })
        //switch (component.__id__) {
        //    case 'signupViewOrganizationNameTextField':
        //        if (!super._validateNotNull(value) || value == '') {
        //            const msg = 'this field is required.'
        //            component.alert(true, 'this field is required.');
        //            return msg
        //        } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
        //            const msg = `length must be 1~${component.__max_text_count__}`;
        //            component.alert(true, msg);
        //            return msg
        //        } else {
        //            component.alert(false);
        //            return true
        //        };
        //        break;
        //    case 'signupViewOrganizationTypeDropdownButton':
        //        if (!super._validateNotNull(value) || value == '') {
        //            const msg = 'this field is required.'
        //            component.alert(true, msg);
        //            return msg
        //        } else {
        //            component.alert(false);
        //            return true
        //        };
        //        break;
        //    case 'signupViewOrganizationBusinessDescriptionTextField':
        //        if (!super._validateNotNull(value) || value == '') {
        //            const msg = 'this field is required.';
        //            component.alert(true, msg);
        //            return msg
        //        } else if (!super._validateLength(value, 1, component.__max_text_count__)) {
        //            const msg = `length must be 1~${component.__max_text_count__}`;
        //            component.alert(true, );
        //            return msg
        //        } else {
        //            component.alert(false);
        //            return true
        //        };
        //        break;
        //    case 'signupViewCountryDropdownButton':
        //        if (!super._validateNotNull(value) || value == '') {
        //            const msg = 'this field is required.'
        //            component.alert(true, msg);
        //            return msg
        //        } else {
        //            component.alert(false);
        //            return true
        //        };
        //        break;
        //    // page 2
        //    case 'signupViewZipcodeTextField':
        //        if (!super._validateNotNull(value) || value == '') {
        //            const msg = 'this field is required.';
        //            component.alert(true, msg);
        //            return msg
        //        } else if (!super._validateFormat(value, RegexType.postalcode)) {
        //            const msg = 'Invalid postal code format. e.g. 123-4567.';
        //            component.alert(true, msg);
        //            return msg
        //        } else {
        //            component.alert(false);
        //            return true
        //        };
        //        break;
 
    }

    /**
     * Run validation for a page.
     * 
     * @description _validateComponent(component, value) must be implemented.
     * 
     * @param {number} page 
     * @returns {Array} a 2-dim list of all errors found in the page.
     * [[component, 'error message'], ..}
     */
    _validateForPage(page) {
        let errors = [];
        this._pageComponents[page].forEach((component, j) => {
            if (component instanceof TextField || component instanceof DropdownButton) {
                const result = this._validateComponent(
                    component, this._values[component.__field_name__]);
                // if result is not true but the error message, add to the errors dict.
                if (result == false) {
                    errors.push([component, result]);
                }
            }
        });
        // set error object if an error found, otherwise []
        if (errors.length == 0) {
            this._pageErrors[page] = [];
        } else {
            this._pageErrors[page] = errors;
        }
        return errors
    }

    /**
     * Log out pageErrors
     */
    _printPageErrors() {
        console.log('------------- page errors ----------------')
        this._pageErrors.forEach((pageError, i) => {
            console.log(`page ${i} `);
            pageError.forEach((row) => {
                const name = row[0].__field_name__; 
                const message = row[1];
                console.log(`${name} : ${message}`)
            })
        });
    }

    /**
     * Alert for pageErrors
     * [DEPRECATED]
     * 
     * @param {Array} errors this._pageErrors
     * @param {function} callback
     */
    _alertPageErrors(errors, callback = ()=>{}) {
        if (errors.length > 0) {
            // display alert 
            errors.forEach((error, i) => {
                const component = error[0];
                const message = error[1];
                component.alert(true, message);
            })
            callback();
            return true
        } else {
            callback();
            return false
        };
    }

    /**
     * Validator for text length.
     * 
     * @param {string} text
     * @param {number} min 
     * @param {number} max 
     * @returns {boolean} isValid
     */
    _validateLength(text, min, max) {
        if (text.length > max) {
            // TODO: message from locale json
            console.log(`value length must be maximum ${max} but ${text.length}`);
            return false
        }
        if (text.length < min) {
            // TODO: message from locale json
            console.log(`value length must be minimum ${min} but ${text.length}`);
            return false
        }
        return true
    }

    /**
     * Validator method for text format.
     * 
     * @param {string} text 
     * @param {RegexType} regexType - RegexType enum {email|password}
     * @returns {boolean} isValid
     */
    _validateFormat(text, regexType) {
        // TODO: enable to be simpilfied?
        // TODO: message from locale json
        switch (regexType) {
            // email
            case RegexType.email:
                return String(text)
                    .toLowerCase()
                    .match(RegexType.email)
                    ? true
                    : console.warn(`${text} is invalid email format.`); false;
                break;
            // password
            case RegexType.password:
                return String(text)
                    .match(RegexType.password)
                    ? true
                    : console.warn(`invalid password format.`); false;
                break;
            // postalcode
            case RegexType.postalcode:
                return String(text)
                    .match(RegexType.postalcode)
                    ? true
                    : console.warn(`${text} is invalid postalcode format.`); false;
                break;
            // tel
            case RegexType.tel:
                return String(text)
                    .match(RegexType.tel)
                    ? true
                    : console.warn(`${text} is invalid tel format.`); false;
                break;
            default:
                console.error(`RegexType ${RegexType} is unrecognized.`);
                break;
        }
    }

    /**
     * Validator method for not null.
     * 
     * @param {*} value 
     * @returns {boolean} isValid
     */
    _validateNotNull(value) {
        if (value == null) {return false}
        else {return true}
    }

    /**
     * HTTP POST to submit data.
     * 
     * @param {string} url
     * @param {function} onsuccess
     * @param {function} onfailed
     */
    _post(url, onsuccess, onfailed) {
        fetch(
            url,
            {
                method: 'POST',
                headers: {
                    //'Content-Type': 'application/x-www-form-urlencoded',
                    'Content-Type': 'application/json',
            },
            // DataModel object as this._values
            body: this._values.json()
        })
        .then(response => response.json())
        .then(data => {
            console.info(`${url} response received:`, data);
            onsuccess(data);
        })
        .catch((error) => {
            console.info(`${url} request failed:`, error);
            onfailed(error);
        })
    }

    /**
     * Toggle loading.
     * 
     * This function only place or remove <div id=this.__loading_element_id__>.
     * 
     * @param {bool} isLoading
     */
    _loading(isLoading) {
        if (isLoading) {
            this._startLoading(this.$loading);
        } else {
            this._stopLoading(this.$loading);
        }
    }

    /**
     * @interface
     * 
     * @param {DOM element} $loading
     */
    _startLoading($loading) {
    }

    /**
     * @interface
     * 
     * @param {DOM element} $loading
     */
    _stopLoading($loading) {
    }

    /**
     * @interface
     * 
     * @param {string} newUrl 
     */
    _goTo(newUrl) {
        document.location.href = newUrl;
    }

    /**
     * Returns an input component by fieldName.
     * 
     * @param {string} fieldName 
     */
    _componentByFieldName(fieldName) {
        let result;
        this._components.forEach((component) => {
            console.log(component.__field_name__)
            if (component.__field_name__ == fieldName) {
                return component
            }
        })
        if (result == null) {
            console.warn(`input component ${fieldName} not found in component list.`)
        } else {
            return result;
        }
    }

    /**
     * Returns an component by id.
     * 
     * @param {string} __id__
     */
    _componentById(__id__) {
        let result;
        this._components.forEach((component) => {
            if (component.__id__ == __id__) {
                result = component
            }
        })
        if (result == null) {
            console.warn(`component ${__id__} not found in component list.`)
        } else {
            return result;
        }
    }
}

/* TODO: separate file */

/**
 * Title class for InputPageViewController.
 * 
 * <code>
 * 
 *   // HTML
 *   <h2 id=signupViewPage1Title class=inputPageViewPageTitle></h2>
 * 
 *   // JavaScript
 *   new InputPageViewController(
 *     ...,
 *     [
 *       ...
 *       new Title('signupViewPage1Title', 'Welcome');
 *       ...
 *     ],
 *     ...
 *   )
 * </code>
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {text} text - inner text
 * @constructor
 */
class Title {
    __id__
    constructor(_id, text) {
        this.__id__ = _id;
        this._setElements(text);
    }

    /**
     * DOM nodes as variables.
     */
    _setElements(text) {
        this.$title = document.getElementById(this.__id__);
        if (this.$title == null) {
            console.warn(
                `<h2 id=${this.__id__} class=inputPageViewPageTitle></h2> is necessary in HTML.`);
        }
        this.$title.innerText = text;
    }
}
 

/**
 * Description class for InputPageViewController.
 * 
 * <code>
 * 
 *   // HTML
 *   <p id=signupViewPage1Description class=inputPageViewPageDescription></h2>
 * 
 *   // JavaScript
 *   new InputPageViewController(
 *     ...,
 *     [
 *       ...
 *       new Description('signupViewPage1Description', 'Here is the description of the page.');
 *       ...
 *     ],
 *     ...
 *   )
 * </code>
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {text} text - inner text
 * @constructor
 */
class Description {
    __id__
    constructor(_id, text) {
        this.__id__ = _id;
        this._setElements(text);
    }

    /**
     * DOM nodes as variables.
     */
    _setElements(text) {
        this.$description = document.getElementById(this.__id__);
        if (this.$description == null) {
            console.warn(
                `<p id=${this.__id__} class=inputPageViewPageDescription></p> is necessary in HTML.`);
        }
        this.$description.innerText = text;
    }
}
 

/**
 * Button class for InputPageViewController.
 * 
 * <code>
 * 
 *   // HTML
 *   <button id=signupViewPage1NextButton class=nextButton></h2>
 * 
 *   // JavaScript
 *   new InputPageViewController(
 *     ...,
 *     [
 *       ...
 *       new NextButton('signupViewPage1NextButton', 'next');
 *       ...
 *     ],
 *     ...
 *   )
 * </code>
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {text} text - inner text
 * @constructor
 */
class NextButton {
    __id__
    constructor(_id, text) {
        this.__id__ = _id;
        this._setElements(text);
    }

    /**
     * DOM nodes as variables.
     */
    _setElements(text) {
        this.$button = document.getElementById(this.__id__);
        if (this.$button == null) {
            console.warn(
                `<button id=${this.__id__} class=nextButton></button> is necessary in HTML.`);
        }
        this.$button.innerText = text;
    }
}


/**
 * Button class for InputPageViewController.
 * 
 * <code>
 * 
 *   // HTML
 *   <button id=signupViewPage2BackButton class=backButton></button>
 * 
 *   // JavaScript
 *   new InputPageViewController(
 *     ...,
 *     [
 *       ...
 *       new BackButton('signupViewPage2BackButton', '←');
 *       ...
 *     ],
 *     ...
 *   )
 * </code>
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {text} text - inner text
 * @constructor
 */
class BackButton {
    __id__
    constructor(_id, text) {
        this.__id__ = _id;
        this._setElements(text);
    }

    /**
     * DOM nodes as variables.
     */
    _setElements(text) {
        this.$button = document.getElementById(this.__id__);
        if (this.$button == null) {
            console.warn(
                `<button id=${this.__id__} class=backButton></button> is necessary in HTML.`);
        }
        this.$button.innerText = text;
    }
}


/**
 * AlertMessage class for InputPageViewController.
 * 
 * <code>
 * 
 *   // HTML
 *   <div id=signupViewPage1AlertMessage class=AlertMessage></div>
 * 
 *   // JavaScript
 *   new InputPageViewController(
 *     ...,
 *     [
 *       ...
 *       new AlertMessage('signupViewPage2AlertMessage');
 *       ...
 *     ],
 *     ...
 *   )
 * </code>
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {text} text - inner text
 * @constructor
 */
class AlertMessage {
    __id__

    _message = null;

    constructor(_id) {
        this.__id__ = _id;
        this._setElements();
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$container = document.getElementById(this.__id__);
        
        this.$message = document.createElement('p');
        this.$message.id = this.__id__ + '_message';
        this.$message.classList.add('AlertMessage__message');

        if (this.$message == null) {
            console.warn(
                `<p id=${this.__id__} class=AlertMessage__message></p> is necessary in HTML.`);
        }

        this.$container.appendChild(this.$message);
    }

    /**
     * message setter.
     */
    set message(message) {
        this._message = message;
        console.log(`${this.__id__} message set: ${message}`);
        // set message
        this.$message.innerText = message;
    }

    /**
     * message getter.
     */
    get message() {return this._message;}
}

/**
 * Wrapper class for InputPageViewController.
 * 
 * <code>
 * 
 *   // HTML
 *   <div id= class=></button>
 * 
 *   // JavaScript
 *   new InputPageViewController(
 *     ...,
 *     [
 *       ...
 *       new Wrapper(
 *             'firstLastNameWrapper',
 *             [
 *                new TextField('firstName'),
 *                new TextField('lastName')
 *             ]
 *        );
 *       ...
 *     ],
 *     ...
 *   )
 * </code>
 * @param {string} _id - The DOM id where this view is inserted.
 * @param {Array} components - view components
 * @constructor
 */
class Wrapper {
    __id__
    components
    constructor(_id, components) {
        this.__id__ = _id;
        this.components = components;
        this._setElements();
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        // NOTE: <div class=wrapper> is created in the constructor of 
        // InputPageViewController after this function is called.
        //this.$wrapper = document.getElementById(this.__id__);
        //if (this.$wrapper == null) {
        //    console.warn(
        //        `<div id=${this.__id__} class=wrapper></div> is necessary in HTML.`);
        //}
    }
}