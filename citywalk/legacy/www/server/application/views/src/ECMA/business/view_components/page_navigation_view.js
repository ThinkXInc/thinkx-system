'use strict'
/**
 * @fileoverview business/view_components/pagenavigation_view.js
 * PageNavigationView component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * PageNavigationView State Enum.
 */
const PageNavigationViewState = Object.freeze({
    athome: 0,  // no breadcrumbs
    attop: 1,  // no backbutton
    atpage: 2,
    onpagebackstart: 3,
    onpagebackdone: 4,
});


/**
 * PageRoute Data Model.
 */
class PageRoute {
    title = null;
    href = null;
    constructor(title, href) {
        this.title = title,
        this.href = href
        if (this.title == null || this.href == null) {
            console.error('both title and href of page route are necessary but null.')
        }
    }
}

/**
 * PageNavigationView component class.
 * @constructor
 * @classdesc `<section id={id} class=pageNavigationView></section>` is necessary in HTML.
 * usage:
 * `<code>`
 *  let pageNavigationView = new PageNavigationView('pageNavigationView')  // insert to table automatically
 *  pageNavigationView.state = PageNavigationViewState.attop;
 *  pageNavigationView.pageRoutes = [
 *      new PageRoute('Home', '/'),
 *      new PageRoute('Top', '/top')
 *  ]
 *  // go to the page
 *  pageNavigationView.state = PageNavigationViewState.atpage;
 *  pageNavigationView.pageRoutes.add(new PageRoute('NextPage', '/next'));
 *  pageNavigationView.pageBackTitle = 'Back to the previous page';
 * `</code>`
 * @param {string} id - The DOM id where this view is inserted.
 */
class PageNavigationView {
    __template__ = `
        <ul class="breadcrumbs cf" style=display:none;>
        </ul>
        <div class=backbutton style=display:none;>
            <img class=backarrow src=/img/icons/backarrow.png srcset="/img/icons/backarrow@2x.png 2x"/>
            <span class=pagebacktitle></span>
        </div>
    `

    __id__ = null;

    _pageRoutes = [];
    _state = null;
    _pageBackTitle = '';

    constructor(id) {
        this.__id__ = id;
        document.getElementById(id).innerHTML = this.__template__;
        this._setElements();
        this._setEventHandlers();
    }

    /* setters */

    /**
     * pageRoutes setter.
     */
    set pageRoutes(pageRoutes) {
        console.log(`update pageNavigationView.pageRoutes with ${pageRoutes.length} routes.`);
        this._pageRoutes = pageRoutes;
        this._resetBreadcrumbs();
    }

    /**
     * pageBackTitle setter.
     */
    set pageBackTitle(title) {
        console.log(`update pageNavigationView.pageBackTitle with ${title}`);
        this._pageBackTitle = title;
        this.$pageBackTitle.innerHTML = this._pageBackTitle;
    }

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case PageNavigationViewState.athome:
                console.log(`PageNavigationView state changed -> athome`);
                this.$pageNavigationView.style.display = 'none';
                break
            case PageNavigationViewState.attop:
                console.log(`PageNavigationView state changed -> attop`);
                this.$pageNavigationView.style.display = 'flex';
                this.$breadcrumbs.style.display = 'flex';
                this.$backbutton.style.display = 'none';
                break
             case PageNavigationViewState.atpage:
                console.log(`PageNavigationView state changed -> atpage`);
                this.$pageNavigationView.style.display = 'flex';
                this.$breadcrumbs.style.display = 'flex';
                this.$backbutton.style.display = 'flex';
                this.$backbutton.classList.add('pageNavigationViewInsertBuckButton');
                break
             case PageNavigationViewState.onpagebackstart:
                console.log(`PageNavigationView state changed -> onpagebackstart`);
                switch (previousState) {
                    case PageNavigationViewState.atpage:
                        // dispatch statechange event to other object
                        const event = new CustomEvent(
                            'onpagebackstart', {
                                detail: {
                                    previous: previousState,
                                    new: state,
                                }});
                        if (previousState != state) {
                            this.$pageNavigationView.dispatchEvent(event);
                        }
                        break;
                }
 
                break
             case PageNavigationViewState.onpagebackdone:
                console.log(`PageNavigationView state changed -> onpagebackdone`);
                break
        }
    }
 
    /* private methods */

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$pageNavigationView = document.getElementById(this.__id__);
        if (this.$pageNavigationView == null) {
            console.warn(
                `<section id=${this.__id__} class=pageNavigationView></section> is necessary in HTML.`);
        }
        this.$breadcrumbs = this.$pageNavigationView.querySelector('.breadcrumbs');
        if (this.$breadcrumbs == null) {
            console.warn(
                `<ul class="breadcrumbs cf"></ul> is necessary in HTML.`);
        }
        this.$backbutton = this.$pageNavigationView.querySelector('.backbutton');
        if (this.$backbutton == null) {
            console.warn(
                `<div class=backbutton> is necessary in HTML.`);
        }
        this.$pageBackTitle = this.$backbutton.querySelector('.pagebacktitle');
        if (this.$pageBackTitle == null) {
            console.warn(
                `<span class=pagebacktitle> is necessary in HTML.`);
        }
    }

    /**
     * Initialize the layout for display.
     */
    _initLayout() {
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
        this.$backbutton.addEventListener('click', e => {
            console.log(`backbutton ${_this.$backbutton} clicked`)
                _this.state = PageNavigationViewState.onpagebackstart;
        });
    }

    /**
     * Reset bread crumbs from this._pageRoutes.
     */
    _resetBreadcrumbs() {
        // make html template from pageRoutes
        const innerTemplate = this._pageRoutes.map((pageRoute, i) =>{
            console.log(pageRoute);
            console.log(`
                add navigation link in breadcrumbs ->
                    depth:${i} title:${pageRoute.title} href:${pageRoute.href}
                `);
            const template_arrow = `<li>></li>`; 
            const template_route = `<a href=${pageRoute.href}><li>${pageRoute.title}</li></a>`;
            return (i == this._pageRoutes.length-1) ? template_route : template_route + template_arrow;
        }).join('');
        console.log(`insert ${innerTemplate}`);
        this.$breadcrumbs.innerHTML = innerTemplate;
    }

}
