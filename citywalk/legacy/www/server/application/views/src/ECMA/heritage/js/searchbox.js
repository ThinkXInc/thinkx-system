/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// search_box.coffee
//
// $("#elem_id").searchBox({
//  TYPE: SEARCHBOX_TYPE.GLOBAL
// });

const SEARCHBOX_TYPE = {
  GLOBAL: 1,
  LOCATION: 2,
  MOVIE: 3,
  PERSON: 4
};

window.SEARCHBOX_TYPE = SEARCHBOX_TYPE;

class SearchBox {
  static initClass() {
   
    /* STATIC VARIABLES */
    
    this.prototype.SEARCHBOX_TYPE = null; 
    this.prototype.LINK_ENABLE = true;
    this.prototype.MAX_SEARCH_TEXT_LENGTH  = 24;
    this.prototype.MIN_SEARCH_TEXT_LENGTH  = 2;
    this.prototype.ICONBOX_FOCUS_CLASS_NAME  = 'isInputFieldFocused';
    this.prototype.MOBILE_BORDER_WIDTH  = 1000;
    this.prototype.IS_MOBILE = false;
  
    this.prototype.SEARCH_API_URL_GLOBAL  = '/search/all';
    this.prototype.SEARCH_API_URL_MOVIE  = '/search/movie';
    this.prototype.SEARCH_API_URL_PERSON  = '/search/person';
    this.prototype.SEARCH_API_URL_LOCATION  = '/search/location';
  
    this.prototype.GENERAL_PERSON_ICON_URL = '/img/main/noimage.png';
  
    this.prototype.SEARCHBOX_TEMPLATE  =
      `\
<input class="searchBoxInput" type="text" name="" placeholder="" data-parts="searchBoxInput"/> 
<input type="text" name="_id" data-parts="searchBoxInputHidden" hidden/>
<span class="searchBoxIconBox" data-parts="searchBoxIconBox">
  <img class="searchIcon" src="/img/main/search_icon.png" srcset="/img/main/search_icon@2x.png 2x"/>
</span>
<div class="searchBoxIndicatorView" data-parts="searchBoxIndicatorView">
  <span>RETRIEVING SUGGESTIONS</span><img src="/img/main/load_of_the_ring_20.png" srcset="/img/main/load_of_the_ring_20@2x.png 2x"/>
</div>
<div class="searchBoxResultsView" data-parts="searchBoxResultsView">
  <ul class="searchBoxResultsViewListContainer" data-parts="searchBoxResultsViewListContainer">
  </ul>
  <div class="searchBoxResultsViewAdditionalRow" data-parts="searchBoxResultsViewAdditionalRow">
    <p>See more results of "<span></span>"</p>
  </div>
</div>\
`;
  
    this.prototype.LIST_ITEM_TEMPLATE_1  =
      `\
<li class="listItem" data-type="$dataType" data-id="$id" data-movie_id="$movie_id" data-name="$name" data-title="$title" data-release_year="$year" data-country="$country" data-directed_by_name="$directed_by_name" data-action="$action">
  <img class="listItemIcon" src="$imgsrc">
  <div class="listItemTextBox">
    <p class="listItemName">$name</p>
    <p class="listItemAdditionalInfo">$additionalInfo</p>
  </div>
</li>\
`;
  
    this.prototype.LIST_ITEM_TEMPLATE_2  =
      `\
<li class="listItem" data-type="$dataType" data-id="$id" data-name="$name" data-action="$action">
  <div class="listItemTextBox">
    <p class="listItemName">$name</p>
  </div>
</li>\
`;
  }

  /* CONSTRUCTOR */
  
  constructor(element_id, searchBoxType) {
    this.setLayout = this.setLayout.bind(this);
    this.setResultsViewLayout = this.setResultsViewLayout.bind(this);
    this.changeSearchBoxIconBoxBGColor = this.changeSearchBoxIconBoxBGColor.bind(this);
    this.searchWithText = this.searchWithText.bind(this);
    this.createListRowsWithResults = this.createListRowsWithResults.bind(this);
    this.SEARCHBOX_TYPE = searchBoxType;
    this.IS_MOBILE = this.MOBILE_BORDER_WIDTH > $(window).width() ? true : false;
    $(element_id).html(this.SEARCHBOX_TEMPLATE);
    this.initParts(element_id);
    this.setEventHandlers();
    this.initInstanceValuables();
  }


  /* INITIALIZE INSTANCE VALIABLES */
  initInstanceValuables() {
    this.IsResultsViewHovered = false;
    return false;
  }


  /* INITIALIZE COMPONENT PARTS */
  
  initParts(element_id) {
    this.$searchBox = $(element_id);
    this.$searchInput = $('[data-parts=searchBoxInput]', this.$searchBox);
    this.$searchInputHidden = $('[data-parts=searchBoxInputHidden]', this.$searchBox);
    this.$searchIconBox = $('[data-parts=searchBoxIconBox]', this.$searchBox);
    this.$loadingIndicatorView = $('[data-parts=searchBoxLoadingIndicatorView]', this.$searchBox); 
    this.$resultsView = $('[data-parts=searchBoxResultsView]', this.$searchBox);
    this.$listContainer = $('[data-parts=searchBoxResultsViewListContainer]', this.$searchBox);
    this.$additionalRow = $('[data-parts=searchBoxResultsViewAdditionalRow]', this.$searchBox);
    return false;
  }


  /* SET INPUT ATTRIBUTES */
  //
  setDefaultValue(text) {
    this.$searchInput.val(text);
    return false;
  }
 
  setPlaceholder(placeHolderText) {
    this.$searchInput.attr('placeholder', placeHolderText);
    return false;
  }

  setFormName(formName) { 
    this.$searchInput.attr('name', formName);
    switch (this.SEARCHBOX_TYPE) {
      case SEARCHBOX_TYPE.LOCATION:
        this.$searchInputHidden.attr('name', 'location_id');
        break;
    }
    return false;
  }

  setInputClass(className) {
    this.$searchInput.addClass(className);
    return false;
  }

  setAutoComplete(shouldSetAutoComplete) {
    if (!shouldSetAutoComplete) {
      this.$searchInput.attr('autocomplete', 'off');
    }
    return false;
  }

  setLinkEnable(enable) {
    this.link_enable = enable;
    return false;
  }

  setIconBoxVisible(visible) {
    if (!visible) {
      this.$searchIconBox.css({'display': 'none'});
    }
    return false;
  }

  setAction(action) {
    this.action = action;
    return false;
  }

  /* SET LAYOUT */
  
  setLayout(form_W, form_H, hasIconBox, loadingTextLeft, loadingImgLeft) {
    if (hasIconBox) {
      $(this).css({'width': form_W + form_H, 'height': form_H + 4});
    } else {
      $(this).css({'width': form_W, 'height': form_H});
      this.$searchIconBox.hide();
    }
    this.$searchIconBox.css({'left': form_W, 'width': form_H, 'height': form_H});
    this.$searchIconBox.find('.searchIcon').css({'width': form_H, 'height': form_H});
    this.$searchInput.css({'width': form_W, 'hight': form_H});
    this.$resultsView.css({'width': form_W, 'top': form_H+6});
    this.$loadingIndicatorView.css({'width': form_W, 'height': form_H, 'top': form_H+6});
    this.$loadingIndicatorView.find('span').css({'left': loadingTextLeft});
    return this.$loadingIndicatorView.find('img').css({'left': loadingImgLeft});
  }

  setResultsViewLayout(width, top, left) {
    this.$resultsView.css({'width': width, 'top': top, 'left': left});
    return false;
  }



  /* EVENT HANDLERS */

  setEventHandlers() {

    this.$searchInput.on('focus', e => {
      // change icon box color when focused
      let isFocused;
      if (this.$searchInput.val().length > 0) {
        this.showResultsView(true);
      }
      return this.changeSearchBoxIconBoxBGColor(isFocused=true);
    });

    this.$searchInput.on('blur', e => {
      let isFocused;
      console.log(this.IsResultsViewHovered);
      if (this.IsResultsViewHovered === true) {
        return false;
      }
      //@showResultsView(false)
      return this.changeSearchBoxIconBoxBGColor(isFocused=false);
    });

    this.$resultsView.hover(
      () => {
        return this.IsResultsViewHovered = true;
      },
      () => {
        return this.IsResultsViewHovered = false;
    });

    this.$searchInput.on('input', e => {
      // get search results when typed
      const typedText = this.$searchInput.val();
      console.log(typedText);
      if ((typedText.length >= this.MIN_SEARCH_TEXT_LENGTH) && (typedText.length <= this.MAX_SEARCH_TEXT_LENGTH)) {
        console.log('search');
        this.searchWithText(typedText);
      }
      if (typedText.length === 0) {
        this.showResultsView(false);
      }
      return false;
    });

    this.$listContainer.on('click', '.listItem', e => {
      // clicked list item
      e.preventDefault();

      this.showResultsView(false);
      this.$searchBox.trigger(
        'selected', 
        {
          'type': $(e.currentTarget).data('type'),
          '_id': $(e.currentTarget).data('id'),
          'movie_id': $(e.currentTarget).data('movie_id'),
          'title': $(e.currentTarget).data('title'),
          'name': $(e.currentTarget).data('name'),
          'directed_by_name': $(e.currentTarget).data('directed_by_name'),
          'release_year': $(e.currentTarget).data('release_year'),
          'country': $(e.currentTarget).data('country'),
          'img_src': $(e.currentTarget).find('img').attr('src')
        }
      );
      return false;
    });


    this.$listContainer.on('click', '[data-action=moviepage]', e=> {
      console.log('moviepage');
      const $target = $(e.currentTarget);
      const movie_id = $target.data('movie_id');
      const movie_title = $target.data('title');
      console.log(movie_id, movie_title);
      window.pageControl.goTo('film/'+movie_id+'/'+movie_title);
      if (this.IS_MOBILE) {
        $('#contentView').removeClass('sp_menu_open');
        $('#sp_menu').removeClass('open');
      }
      return false;
    });


    this.$listContainer.on('click', '[data-action=personpage]', e=> {
      const $target = $(e.currentTarget);
      const person_id = $target.data('id');
      const person_name = $target.data('name');
      window.pageControl.goTo('related/'+person_name);
      return false;
    });

    this.$listContainer.on('click', '[data-action=selectlocation]', e=> {
      const _id = $(e.currentTarget).data('id');
      const name = $(e.currentTarget).data('name');
      this.$searchInput.val(name);
      this.$searchInputHidden.val(_id);
      return false;
    });

    this.$listContainer.on('click', '[data-action=selectperson]', e=> {
      const _id = $(e.currentTarget).data('id');
      const name = $(e.currentTarget).data('name');
      this.$searchInput.val(name);
      this.$searchInputHidden.val(_id);
      return false;
    });

    this.$searchBox.on('click', '[data-action=moreresults]', e=> {
      const $target = $(e.currentTarget);
      const search_text = $target.data('search_text');
      window.pageControl.goTo('moreresults/'+search_text);
      this.showResultsView(false);
      return false;
    });

    return false;
  }

  /* FUNCTIONS */

  changeSearchBoxIconBoxBGColor(isFocused) {
    if (isFocused) {
      this.$searchIconBox.addClass(this.ICONBOX_FOCUS_CLASS_NAME);
    } else {
      this.$searchIconBox.removeClass(this.ICONBOX_FOCUS_CLASS_NAME);
    }
    return false;
  }
  
  searchWithText(search_text) {
    let search_url;
    switch (this.SEARCHBOX_TYPE) {
      case SEARCHBOX_TYPE.GLOBAL:
        search_url = this.SEARCH_API_URL_GLOBAL;
        break;
      case SEARCHBOX_TYPE.MOVIE:
        search_url = this.SEARCH_API_URL_MOVIE;
        break;
      case SEARCHBOX_TYPE.PERSON:
        search_url = this.SEARCH_API_URL_PERSON;
        break;
      case SEARCHBOX_TYPE.LOCATION:
        search_url = this.SEARCH_API_URL_LOCATION;
        break;
    }
    const $this = this;
    return $.ajax({
      url: search_url,
      type: 'GET',
      data: {'searchText': search_text},
      dataType: 'JSON',
      beforeSend() {
        console.log($this);
        $this.showIndicatorView(true);
        return console.log('before send');
      },
      success(results) {
        console.log(this);
        $this.showIndicatorView(false);
        console.log(results);
        $this.createListRowsWithResults(results, search_text);
        return $this.showResultsView(true);
      },
      error(data) {
        $this.showIndicatorView(false);
        console.log('[WARNING] AJAX ERROR');
        console.log(data);
        return $this.showResultsView(false);
      }
    });
  }
  
  showIndicatorView(isShown) {
    if (isShown == null) { isShown = true; }
    switch (isShown) {
      case true:
        this.$loadingIndicatorView.addClass('show');
        break;
      case false:
        this.$loadingIndicatorView.removeClass('show');
        break;
    }
    return false;
  }
  
  showResultsView(isShown) {
    if (isShown == null) { isShown = true; }
    switch (isShown) {
      case true:
        this.$resultsView.addClass('show');
        break;
      case false:
        this.$resultsView.removeClass('show');
        break;
    }
    return false;
  }
  
  createListRowsWithResults(results, search_text) {
    let list_rows_html = '';
    for (let data of Array.from(results)) {
      const row_data = {};
      let row_html = '';
      row_data['$dataType'] = data['type'];
      switch (data['type']) {
        case 'Film':
          row_data['$id'] = data['_id'];
          row_data['$movie_id'] = data['movie_id'];
          row_data['$title'] = data['title'];
          row_data['$name'] = data['title'];
          row_data['$year'] = data['release_year'];
          row_data['$country'] = data['country'];
          row_data['$directed_by_name'] = data['directed_by']['name'];
          row_data['$link'] = '/film/'+data['movie_id']+'/'+data['title'];
          row_data['$imgsrc'] = '/resources/movies/cover/en/'+data['movie_id']+'.jpg?width=25&height=34&type=resize'; 
          if (data['release_year']) {
            row_data['$additionalInfo'] = 'Film, '+data['release_year']+' '+data['country']+', Directed by '+data['directed_by']['name'];
          } else {
            row_data['$additionalInfo'] = ', Directed by '+data['directed_by']['name'];
          }
          row_html = this.LIST_ITEM_TEMPLATE_1;
          if (this.link_enable && !this.action) {
            row_data['$action'] = 'moviepage';
          } else if (this.action) {
            row_data['$action'] = this.action;
          }
          break;
        case 'Person':
          row_data['$id'] = data['_id'];
          row_data['$name'] = data['name'];
          row_data['$link'] = '/person/'+data['_id']+'/'+data['$name'];
          row_data['$imgsrc'] = this.GENERAL_PERSON_ICON_URL;
          row_data['$additionalInfo'] = data['job'];
          row_html = this.LIST_ITEM_TEMPLATE_1;
          if (this.link_enable && !this.action) {
            row_data['$action'] = 'personpage';
          } else if (this.action) {
            row_data['$action'] = this.action;
          }
          break;
        case 'Location':
          row_data['$id'] = data['_id'];
          row_data['$name'] = data['name'];
          row_html = this.LIST_ITEM_TEMPLATE_2;
          if (this.link_enable && !this.action) {
            row_data['$action'] = 'selectlocation';
          } else if (this.action) {
            row_data['$action'] = this.action;
          }
          break;
      }
      for (let key in row_data) {
        const value = row_data[key];
        row_html = row_html.split(key).join(value);
      }
      list_rows_html += row_html;
    }
    this.$listContainer.html(list_rows_html);
    // additional row
    if (results.length === 0) {
      return this.setAdditionalRow('No Result', null, null);
    } else {
      return this.setAdditionalRow('See More Results of "$"'.replace('$', search_text), 'moreresults', search_text);
    }
  }

  
  setAdditionalRow(text, action, search_text) {
    this.$additionalRow.find('p').html(text);
    if (action) {
      this.$additionalRow.attr('data-action', action);
      return this.$additionalRow.attr('data-search_text', search_text);
    } else {
      this.$additionalRow.attr('data-action', '');
      return this.$additionalRow.attr('data-search_text', '');
    }
  }
  
  initializeListContainer() {
     return this.$listContainer.html('');
   }
}
SearchBox.initClass();



window.SearchBox = SearchBox;
