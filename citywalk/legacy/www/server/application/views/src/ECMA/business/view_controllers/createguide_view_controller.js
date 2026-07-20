'use strict'
/**
 * @fileoverview business/view_controllers/createguide.js
 * CreateGuideView controller class.
 * 
 * <code>
 * 
* 
 * </code>
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 */


/**
 * Global Google map object.
 */
let map;


/**
 * CreateGuideViewController State Enum.
 */
const CreateGuideViewControllerState = Object.freeze({
    none: 1,
    editingnew: 2,
    reediting: 3,
});


 /**
 * CreateGuideViewController class.
 * @param {float} lat - initial map center latitude
 * @param {float} lng - initial map center longtitude
 * @param {in} zoom - initial map zoom
 * @constructor
 */
class CreateGuideViewController {
    // settings
    center = new Coordinate();
    zoom = null;

    // view components
    pageNavigationView = new PageNavigationView('pageNavigationView');
    contentTableView = new ContentTableView('contentTableView');
    editContentView = new EditContentView('editContentView');

    mapPointer; // initialized after map is loaded.
    mapBalloons = []; // initialized after map is loaded.

    editingMapBalloon = null;
    __editingMapBalloonUniqueIdentifier__ = 'newEditingMapBalloon';

    // data
    _contents = [];
    _state = CreateGuideViewControllerState.none;

    constructor(lat, lng, zoom) {
        // settings
        this.center = new Coordinate(lat, lng);
        this.zoom = zoom;
        // initialize observer 
        this._initObservers()
        this.editContentView.state = EditContentViewState.onhide;
    }

    /**
     * state setter.
     */
    set state(state) {
        const previousState = this._state;
        this._state = state;
        switch (state) {
            case CreateGuideViewControllerState.none:
                console.log(`CreateGuideViewController state changed -> none`);
                break
            case CreateGuideViewControllerState.editingnew:
                console.log(`CreateGuideViewController state changed -> oneditingnew`);
                break
        }
    }

    /**
     * state getter.
     */
    get state() {return this._state;}
 
    /**
     * contents setter.
     * contentTableView is automatically reconstructed.
     */
    set contents(contents) {
        console.log('update contents of CreateGuideViewController');
        this._contents = contents;
        this.contentTableView.contents = contents;
        this.pageNavigationView.state = PageNavigationViewState.attop;
        this.pageNavigationView.pageRoutes = [
            new PageRoute('Home', '/business/home'),
            new PageRoute('Create Guide', '/business/createguide')
        ]
        this.mapBalloons = this._contents.map((content, i) =>{
    //if (i == 0) {
            let balloon = new MapBalloon(content._id, new Coordinate(
                content.lat, content.lng).latlng, content.title, content.text);
            balloon.setMap(map);
            return balloon
    //}//
        })
    }

    _startEditContent(pageBackTitle, content) {
        // set pageNavigationView state
        this.pageNavigationView.state = PageNavigationViewState.atpage;
        this.pageNavigationView.pageBackTitle = pageBackTitle;
        applyCursorRippleEffect(this.pageNavigationView.$backbutton)
        // set content
        if (content) {
            this.editContentView.content = content;
            this.editContentView.editingContent = content;
        }
        // set editContentView state
        this.editContentView.state = EditContentViewState.onshow;
        // FIXME: overflow: hidden not work
        //applyCursorRippleEffect(this.editContentView.$saveButton);
    }

    /**
     * Initialize observers.
     */
    _initObservers() {
        const _this = this;
        // observe contentTableView.state
        this.contentTableView.$contentTableView.addEventListener(
            'onclosecomplete', (event) => {
                const selected = event.detail.selected;
                console.log(`received contentTableView ${event.type} by selected ${selected}`);
                ////_this._startEditContent('Guide Contents', this._contents[selected]);
                // set pageNavigationView state
                this.pageNavigationView.state = PageNavigationViewState.atpage;
                this.pageNavigationView.pageBackTitle = 'Contents';

                applyCursorRippleEffect(this.pageNavigationView.$backbutton)
                // set editContentView state
                if (selected !== null) {
                    // table cell selected
                    const content = this._contents[selected];
                    console.table(content);
                    this.state = CreateGuideViewControllerState.reediting;
                    this.editContentView.content = content;
                    if (this.mapPointer) {
                        this.mapPointer.state = MapPointerState.onclosestart;
                    }
                    // update page routes
                    //this.pageNavigationView.pageRoutes = [
                    //    new PageRoute('Home', '/business'),
                    //    new PageRoute('Create Guide', '/business/createguide'),
                    //    new PageRoute(`${content.label} の編集`, `/business/createguide?edit=${content.id}`)
                    //]
                } else {
                    // create new
                    this.state = CreateGuideViewControllerState.editingnew;
                    this.editContentView.content = null;
                    this.mapPointer = null;
                }
                this.editContentView.state = EditContentViewState.onshow;
                // FIXME: overflow: hidden not work
                //applyCursorRippleEffect(this.editContentView.$saveButton);
       })
       this.contentTableView.$contentTableView.addEventListener(
           'onmouseover', (event) => {
               const cellId = event.detail.cellId;
               const index = event.detail.index;
               console.log(`[event] cell hover cellId: ${cellId} index: ${index}`);
               this.mapBalloons.forEach((mapBalloon, i) => {
                   mapBalloon.state = (i == index) ? MapBalloonState.onfocus : MapBalloonState.onshow;
               })
               this.mapBalloons[index].state = MapBalloonState.onfocus;
           }
       )
       this.contentTableView.$contentTableView.addEventListener(
           'onmouseout', (event) => {
               const cellId = event.detail.cellId;
               const index = event.detail.index;
               console.log(`[event] cell out cellId: ${cellId} index: ${index}`);
           }
       )
       // observe pageNavigationView state
       this.pageNavigationView.$pageNavigationView.addEventListener(
           'onpagebackstart', (event) => {
                console.log(`received pageNavigationView ${event.type}`);
                // editContentView onclosestart
                this.editContentView.state = EditContentViewState.onclosestart;
                if (this.editingMapBalloon) {
                    this.editingMapBalloon.state = MapBalloonState.onclosestart;
                }
           }
       )
       // observe editContentView state
       this.editContentView.$editContentView.addEventListener(
           'onclosecomplete', (event) => {
                console.log(`received editContentView ${event.type}`);
                // contentTableView onshow
                this.contentTableView.contents = this._contents;
                this.contentTableView.state = 
                    ContentTableViewState.onshow;
                // pageNavigationView attop
                this.pageNavigationView.state = PageNavigationViewState.attop;
                // controller state none
                this.state = CreateGuideViewControllerState.none;
                //// update page routes
                //this.pageNavigationView.pageRoutes = [
                //    new PageRoute('Home', '/business'),
                //    new PageRoute('Create Guide', '/business/createguide'),
                //]
                // clean newEditingMapBalloon
                if (this.editingMapBalloon) {
                    this.editingMapBalloon = null;
                }
           }
       )
       // observe mapPointer state
       document.addEventListener(
           'mapPointerSelected', (event) => {
                const action = event.detail.action;
                const value = event.detail.value; 
                console.log(`received mapPointer ${event.type} action: ${action} value: ${value}`);
                if (value == 'createnew') {
                    ///_this._startEditContent('Guide Contents', null);
                    this.contentTableView.state = ContentTableViewState.onclosestart;
                    this.mapPointer.state = MapPointerState.onhide;
                    // create map balloon
                    this.editContentView.editingMapBalloon = this._addEditingMapBalloon(
                        this.__editingMapBalloonUniqueIdentifier__,
                        this.mapPointer.latLng, 'タイトル', '本文');
                    this.editContentView.content = new Content();
                    this.editContentView.editingContent = EditingContent.fromContent(
                        this.editContentView.content)
                } else if (value == 'cancel') {
                    // TODO:
                } else {
                    console.log(`unknown mapPointer selected value ${value}`);
                }
               
            }
       )

    }

    /**
    * Submit form data.
    * @param {callback function} onsuccess - called on seccess.
    * @param {callback function} onfailed - called on failed.
    */
    fetchContents(onsuccess, onfailed) {
        // url by type
        const url = `${app.config.host}/demo/1/contents/guide/list`;
        console.log(`fetch from ${url}`);

        // submit
        fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.info('fetch success:', data);
            onsuccess(data);
        })
        .catch((error) => {
            console.error('fetch error:', error);
            onfailed(error);
        })
    }

    /**
     * Add new MapPointer for create new guide.
     */
    addCreateNewGuideMapPointer(latLng) {
        const mapPointerId = 'newGuidePointer';
        this.mapPointer = new MapPointer(mapPointerId, 
            new Coordinate(latLng.lat, latLng.lng),
            [new MapPointerOption(
                'ここにガイドを作成', 'createnew', MapPointerAction.selectAndClose)]
        )
        this.mapPointer.setMap(map);
    }

    /**
     * Add new MapBalloon for editing.
     * @returns {MapBalloon} editingMapBalloon - 
     */
    _addEditingMapBalloon(id, latLng, title, text) {
        this.editingMapBalloon = new MapBalloon(id, latLng, title, text);
        this.editingMapBalloon.setMap(map);
        return this.editingMapBalloon;
    }
}


/**
 * Initialize view from Google Map API Callback function.
 * 
 * This function is called firstly after googlemap canvas was setup.
 */
function initMap() {
    console.log('initialize google map');

    // TODO: use organization's default center
    // center: {lat: 35.6603976, lng: 139.7292361},
    // const lat = 48.6358 // roppongi
    // const lon = -1.511  // roppongi
    const lat = 46.943986; // bern
    const lon = 7.426123; // bern
    const zoom = 14;

    // initialize ViewController
    var vc = new CreateGuideViewController(
        lat, lon, zoom);
    app.createGuideViewController = vc;

    // initialize google map by center and zoom
    map = new google.maps.Map(document.getElementById('map'), {
        center: vc.center.latlng,
        zoom: zoom
    });

    // set map custom layers
    // Custom layer classes need to be defined after google.map is loaded.
    // Since import('/path') is unavailable, dynamically create the <script>.
    let script_1 = document.createElement('script');
    script_1.src = '/js/business/view_components/map_pointer.js';
    document.getElementById('content').appendChild(script_1);
    script_1.onload = ()=> {
        // map components
        // MEMO: remove this line
        //vc.addCreateNewGuideMapPointer(new Coordinate(lat, lng).latlng);
        // observe map events
        map.addListener('click', (event) => {
            const latLng = event.latLng;
            console.log(`map clicked at ${latLng}`)
            if (vc.mapPointer 
                && (vc.mapPointer.state == MapPointerState.onhide)) {
                // soon after selected. do nothing .
            } else if (vc.mapPointer
                && (vc.mapPointer.state == MapPointerState.onshow)) {
                // close old one -> create new
                vc.mapPointer.state = MapPointerState.onclosestart;
                if (vc.state == CreateGuideViewControllerState.editingnew
                    || vc.state == CreateGuideViewControllerState.reediting) {
                    console.log('now editing. unable to set new.')
                } else {
                    vc.addCreateNewGuideMapPointer(latLng);
                }
            } else if (vc.mapPointer
                && (vc.mapPointer.state == MapPointerState.onclosecomplete)) {
                // no pointer. create new.
                if (vc.state == CreateGuideViewControllerState.editingnew
                    || vc.state == CreateGuideViewControllerState.reediting) {
                    console.log('now editing new content. unable to set new.')
                } else {
                    vc.addCreateNewGuideMapPointer(latLng);
                }
            } else if (vc.mapPointer == null) {
                // no pointer. create new.
                if (vc.state == CreateGuideViewControllerState.editingnew
                    || vc.state == CreateGuideViewControllerState.reediting) {
                    console.log('now editing new content. unable to set new.')
                } else {
                    vc.addCreateNewGuideMapPointer(latLng);
                }
            } else {
                console.error('unkown state');
            }
        });
        map.addListener('dblclick', (event) => {
            // TODO: if needed
        });
    }

    let script_2 = document.createElement('script');
    script_2.src = '/js/business/view_components/map_balloon.js';
    document.getElementById('content').appendChild(script_2);
    script_2.onload = () => {
        // fetch data & initialize tableView
        vc.fetchContents(function(data){
            // store contents data
            const contents = data.contents.map(content =>
                new Content.initFromJson(content)
            )
            console.table(contents);
            // reset contentTable
            vc.contents = contents;
            vc.contentTableView.state = 
                ContentTableViewState.onshow;
        }, function(){})
    }
}
 