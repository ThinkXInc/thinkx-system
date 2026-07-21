'use strict'
/**
 * @fileoverview business/view_controllers/home_view_controller.js
 * HomeView controller class.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/


/**
 * HomeViewController class.
 * 
 * @constructor
 */
class HomeViewController {
    __view_id__ = 'homeView'

    // main menu
    __create_guides_menu_id__ = 'createGuidesMenu'
    __register_items_menu_id__ = 'registerItemsMenu'
    __sales_data_menu_id__ = 'salesDataMenu'
    __manage_reservations_menu_id__ = 'manageReservationsMenu'
    __store_menu_id__ = 'storeMenu'
    __user_analysis_menu_id__ = 'userAnalysisMenu'
    __settings_menu_id__ = 'settingsMenu'

    // header menu
    __organization_menu_id__ = 'organizationMenu'
    __organization_member_menu_id__ = 'organizationMenu'


    constructor() {
        this._setElements()
        this._initObservers()
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        // menu buttons
        this.$createGuidesMenu = document.getElementById(this.__create_guides_menu_id__);
        if (this.$createGuidesMenu == null) {
            console.warn(
                `<li id=${this.__create_guides_menu_id__}></li> is necessary in HTML.`);
        }
        this.$registerItemsMenu = document.getElementById(this.__register_items_menu_id__);
        if (this.$registerItemsMenu == null) {
            console.warn(
                `<li id=${this.__register_items_menu_id__}></li> is necessary in HTML.`);
        }
        this.$manageReservationsMenu = document.getElementById(this.__manage_reservations_menu_id__);
        if (this.$manageReservationsMenu == null) {
            console.warn(
                `<li id=${this.__manage_reservations_menu_id__}></li> is necessary in HTML.`);
        }
        this.$salesDataMenu = document.getElementById(this.__sales_data_menu_id__);
        if (this.$salesDataMenu == null) {
            console.warn(
                `<li id=${this.__sales_data_menu_id__}></li> is necessary in HTML.`);
        }
        this.$storeMenu = document.getElementById(this.__store_menu_id__);
        if (this.$storeMenu == null) {
            console.warn(
                `<li id=${this.__store_menu_id__}></li> is necessary in HTML.`);
        }
        this.$userAnalysisMenu = document.getElementById(this.__user_analysis_menu_id__);
        if (this.$userAnalysisMenu == null) {
            console.warn(
                `<li id=${this.__user_analysis_menu_id__}></li> is necessary in HTML.`);
        }
        this.$settingsMenu = document.getElementById(this.__settings_menu_id__);
        if (this.$settingsMenu == null) {
            console.warn(
                `<li id=${this.__settings_menu_id__}></li> is necessary in HTML.`);
        }

        // header menu
        this.$organizationMenu = document.getElementById(this.__organization_menu_id__);
        if (this.$organizationMenu == null) {
            console.warn(
                `<li id=${this.__organization_menu_id__}></li> is necessary in HTML.`);
        }
        this.$organizationMemberMenu = document.getElementById(this.__organization_member_menu_id__);
        if (this.$organizationMemberMenu == null) {
            console.warn(
                `<li id=${this.__organizationMember_menu_id__}></li> is necessary in HTML.`);
        }





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
            if (url.includes('#intro')) {
                // show introduction
                console.log('ready to show introduction..')
                let introductionViewController = new IntroductionViewController();
                introductionViewController.createView(_this.__view_id__);
            } else {

            }
        });

        // menu click event
        function clickAndGo(e, path) {
            console.log(`${e.currentTarget.id} clicked`)
            PageControl.goTo(path)
        }
        this.$createGuidesMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/createguide')
        })
        this.$registerItemsMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/createitem')
        })
        this.$manageReservationsMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/reservations')
        })
        this.$salesDataMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/salesdata')
        })
        this.$storeMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/store')
        })
        this.$userAnalysisMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/analisys')
        })
        this.$settingsMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/settings')
        })
        // header menu click event
        this.$organizationMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/settings#organization')
        })
        this.$organizationMemberMenu.addEventListener('click', (e) => {
            clickAndGo(e, '/business/settings#member')
        })

    }
 
}
 