# search_box.coffee
#
# $("#elem_id").searchBox({
#  TYPE: SEARCHBOX_TYPE.GLOBAL
# });

SEARCHBOX_TYPE =
  GLOBAL: 1
  LOCATION: 2
  MOVIE: 3
  PERSON: 4

window.SEARCHBOX_TYPE = SEARCHBOX_TYPE

class SearchBox
 
  ### STATIC VARIABLES ###
  
  SEARCHBOX_TYPE: null 
  LINK_ENABLE: true
  MAX_SEARCH_TEXT_LENGTH : 24
  MIN_SEARCH_TEXT_LENGTH : 2
  ICONBOX_FOCUS_CLASS_NAME : 'isInputFieldFocused'
  MOBILE_BORDER_WIDTH : 1000
  IS_MOBILE: false

  SEARCH_API_URL_GLOBAL : '/search/all'
  SEARCH_API_URL_MOVIE : '/search/movie'
  SEARCH_API_URL_PERSON : '/search/person'
  SEARCH_API_URL_LOCATION : '/search/location'

  GENERAL_PERSON_ICON_URL: '/img/main/noimage.png'

  SEARCHBOX_TEMPLATE :\
    '''
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
    </div>
    '''

  LIST_ITEM_TEMPLATE_1 :\
    '''
    <li class="listItem" data-type="$dataType" data-id="$id" data-movie_id="$movie_id" data-name="$name" data-title="$title" data-release_year="$year" data-country="$country" data-directed_by_name="$directed_by_name" data-action="$action">
      <img class="listItemIcon" src="$imgsrc">
      <div class="listItemTextBox">
        <p class="listItemName">$name</p>
        <p class="listItemAdditionalInfo">$additionalInfo</p>
      </div>
    </li>
    '''

  LIST_ITEM_TEMPLATE_2 :\
    '''
    <li class="listItem" data-type="$dataType" data-id="$id" data-name="$name" data-action="$action">
      <div class="listItemTextBox">
        <p class="listItemName">$name</p>
      </div>
    </li>
    '''

  ### CONSTRUCTOR ###
  
  constructor: (element_id, searchBoxType) ->
    @SEARCHBOX_TYPE = searchBoxType
    @IS_MOBILE = if @MOBILE_BORDER_WIDTH > $(window).width() then true else false
    $(element_id).html(@SEARCHBOX_TEMPLATE)
    @initParts(element_id)
    @setEventHandlers()
    @initInstanceValuables()


  ### INITIALIZE INSTANCE VALIABLES ###
  initInstanceValuables: () ->
    @IsResultsViewHovered = false
    return false


  ### INITIALIZE COMPONENT PARTS ###
  
  initParts: (element_id) ->
    @$searchBox = $(element_id)
    @$searchInput = $('[data-parts=searchBoxInput]', @$searchBox)
    @$searchInputHidden = $('[data-parts=searchBoxInputHidden]', @$searchBox)
    @$searchIconBox = $('[data-parts=searchBoxIconBox]', @$searchBox)
    @$loadingIndicatorView = $('[data-parts=searchBoxLoadingIndicatorView]', @$searchBox) 
    @$resultsView = $('[data-parts=searchBoxResultsView]', @$searchBox)
    @$listContainer = $('[data-parts=searchBoxResultsViewListContainer]', @$searchBox)
    @$additionalRow = $('[data-parts=searchBoxResultsViewAdditionalRow]', @$searchBox)
    return false


  ### SET INPUT ATTRIBUTES ###
  #
  setDefaultValue: (text) ->
    @$searchInput.val(text)
    return false
 
  setPlaceholder: (placeHolderText) ->
    @$searchInput.attr('placeholder', placeHolderText)
    return false

  setFormName: (formName) -> 
    @$searchInput.attr('name', formName)
    switch @SEARCHBOX_TYPE
      when SEARCHBOX_TYPE.LOCATION
        @$searchInputHidden.attr('name', 'location_id')
        break
    return false

  setInputClass: (className) ->
    @$searchInput.addClass(className)
    return false

  setAutoComplete: (shouldSetAutoComplete) ->
    if not shouldSetAutoComplete
      @$searchInput.attr('autocomplete', 'off')
    return false

  setLinkEnable: (enable) ->
    @link_enable = enable
    return false

  setIconBoxVisible: (visible) ->
    if not visible
      @$searchIconBox.css({'display': 'none'})
    return false

  setAction: (action) ->
    @action = action
    return false

  ### SET LAYOUT ###
  
  setLayout: (form_W, form_H, hasIconBox, loadingTextLeft, loadingImgLeft) =>
    if hasIconBox
      $(@).css({'width': form_W + form_H, 'height': form_H + 4})
    else
      $(@).css({'width': form_W, 'height': form_H})
      @$searchIconBox.hide()
    @$searchIconBox.css({'left': form_W, 'width': form_H, 'height': form_H})
    @$searchIconBox.find('.searchIcon').css({'width': form_H, 'height': form_H})
    @$searchInput.css({'width': form_W, 'hight': form_H})
    @$resultsView.css({'width': form_W, 'top': form_H+6})
    @$loadingIndicatorView.css({'width': form_W, 'height': form_H, 'top': form_H+6})
    @$loadingIndicatorView.find('span').css({'left': loadingTextLeft})
    @$loadingIndicatorView.find('img').css({'left': loadingImgLeft})

  setResultsViewLayout: (width, top, left) =>
    @$resultsView.css({'width': width, 'top': top, 'left': left})
    return false



  ### EVENT HANDLERS ###

  setEventHandlers: () ->

    @$searchInput.on 'focus', (e) =>
      # change icon box color when focused
      if @$searchInput.val().length > 0
        @showResultsView(true)
      return @changeSearchBoxIconBoxBGColor(isFocused=true)

    @$searchInput.on 'blur', (e) =>
      console.log(@IsResultsViewHovered)
      if @IsResultsViewHovered == true
        return false
      #@showResultsView(false)
      return @changeSearchBoxIconBoxBGColor(isFocused=false)

    @$resultsView.hover(
      =>
        @IsResultsViewHovered = true
      =>
        @IsResultsViewHovered = false
    )

    @$searchInput.on 'input', (e) =>
      # get search results when typed
      typedText = @$searchInput.val()
      console.log(typedText)
      if typedText.length >= @MIN_SEARCH_TEXT_LENGTH and typedText.length <= @MAX_SEARCH_TEXT_LENGTH
        console.log('search')
        @searchWithText(typedText)
      if typedText.length == 0
        @showResultsView(false)
      return false

    @$listContainer.on 'click', '.listItem', (e) =>
      # clicked list item
      e.preventDefault()

      @showResultsView(false)
      @$searchBox.trigger(
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
      )
      return false


    @$listContainer.on 'click', '[data-action=moviepage]', (e)=>
      console.log('moviepage')
      $target = $(e.currentTarget)
      movie_id = $target.data('movie_id')
      movie_title = $target.data('title')
      console.log(movie_id, movie_title)
      window.pageControl.goTo('film/'+movie_id+'/'+movie_title)
      if @IS_MOBILE
        $('#contentView').removeClass('sp_menu_open')
        $('#sp_menu').removeClass('open')
      return false


    @$listContainer.on 'click', '[data-action=personpage]', (e)=>
      $target = $(e.currentTarget)
      person_id = $target.data('id')
      person_name = $target.data('name')
      window.pageControl.goTo('related/'+person_name)
      return false

    @$listContainer.on 'click', '[data-action=selectlocation]', (e)=>
      _id = $(e.currentTarget).data('id')
      name = $(e.currentTarget).data('name')
      @$searchInput.val(name)
      @$searchInputHidden.val(_id)
      return false

    @$listContainer.on 'click', '[data-action=selectperson]', (e)=>
      _id = $(e.currentTarget).data('id')
      name = $(e.currentTarget).data('name')
      @$searchInput.val(name)
      @$searchInputHidden.val(_id)
      return false

    @$searchBox.on 'click', '[data-action=moreresults]', (e)=>
      $target = $(e.currentTarget)
      search_text = $target.data('search_text')
      window.pageControl.goTo('moreresults/'+search_text)
      @showResultsView(false)
      return false

    return false

  ### FUNCTIONS ###

  changeSearchBoxIconBoxBGColor: (isFocused) =>
    if isFocused
      @$searchIconBox.addClass(@ICONBOX_FOCUS_CLASS_NAME)
    else
      @$searchIconBox.removeClass(@ICONBOX_FOCUS_CLASS_NAME)
    return false
  
  searchWithText: (search_text) =>
    switch @SEARCHBOX_TYPE
      when SEARCHBOX_TYPE.GLOBAL
        search_url = @SEARCH_API_URL_GLOBAL
        break
      when SEARCHBOX_TYPE.MOVIE
        search_url = @SEARCH_API_URL_MOVIE
        break
      when SEARCHBOX_TYPE.PERSON
        search_url = @SEARCH_API_URL_PERSON
        break
      when SEARCHBOX_TYPE.LOCATION
        search_url = @SEARCH_API_URL_LOCATION
        break
    $this = @
    $.ajax(
      url: search_url
      type: 'GET'
      data: {'searchText': search_text}
      dataType: 'JSON'
      beforeSend: () ->
        console.log($this)
        $this.showIndicatorView(true)
        console.log('before send')
      success: (results) ->
        console.log(@)
        $this.showIndicatorView(false)
        console.log(results)
        $this.createListRowsWithResults(results, search_text)
        $this.showResultsView(true)
      error: (data) ->
        $this.showIndicatorView(false)
        console.log('[WARNING] AJAX ERROR')
        console.log(data)
        $this.showResultsView(false)
    )
  
  showIndicatorView: (isShown=true) ->
    switch isShown
      when true
        @$loadingIndicatorView.addClass('show')
        break
      when false
        @$loadingIndicatorView.removeClass('show')
        break
    return false
  
  showResultsView: (isShown=true) ->
    switch isShown
      when true
        @$resultsView.addClass('show')
      when false
        @$resultsView.removeClass('show')
    return false
  
  createListRowsWithResults: (results, search_text) =>
    list_rows_html = ''
    for data in results
      row_data = {}
      row_html = ''
      row_data['$dataType'] = data['type']
      switch data['type']
        when 'Film'
          row_data['$id'] = data['_id']
          row_data['$movie_id'] = data['movie_id']
          row_data['$title'] = data['title']
          row_data['$name'] = data['title']
          row_data['$year'] = data['release_year']
          row_data['$country'] = data['country']
          row_data['$directed_by_name'] = data['directed_by']['name']
          row_data['$link'] = '/film/'+data['movie_id']+'/'+data['title']
          row_data['$imgsrc'] = '/resources/movies/cover/en/'+data['movie_id']+'.jpg?width=25&height=34&type=resize' 
          if data['release_year']
            row_data['$additionalInfo'] = 'Film, '+data['release_year']+' '+data['country']+', Directed by '+data['directed_by']['name']
          else
            row_data['$additionalInfo'] = ', Directed by '+data['directed_by']['name']
          row_html = @LIST_ITEM_TEMPLATE_1
          if @link_enable and not @action
            row_data['$action'] = 'moviepage'
          else if @action
            row_data['$action'] = @action
          break
        when 'Person'
          row_data['$id'] = data['_id']
          row_data['$name'] = data['name']
          row_data['$link'] = '/person/'+data['_id']+'/'+data['$name']
          row_data['$imgsrc'] = @GENERAL_PERSON_ICON_URL
          row_data['$additionalInfo'] = data['job']
          row_html = @LIST_ITEM_TEMPLATE_1
          if @link_enable and not @action
            row_data['$action'] = 'personpage'
          else if @action
            row_data['$action'] = @action
          break
        when 'Location'
          row_data['$id'] = data['_id']
          row_data['$name'] = data['name']
          row_html = @LIST_ITEM_TEMPLATE_2
          if @link_enable and not @action
            row_data['$action'] = 'selectlocation'
          else if @action
            row_data['$action'] = @action
          break
      for key, value of row_data
        row_html = row_html.split(key).join(value)
      list_rows_html += row_html
    @$listContainer.html(list_rows_html)
    # additional row
    if results.length == 0
      @setAdditionalRow('No Result', null, null)
    else
      @setAdditionalRow('See More Results of "$"'.replace('$', search_text), 'moreresults', search_text)

  
  setAdditionalRow: (text, action, search_text) ->
    @$additionalRow.find('p').html(text)
    if action
      @$additionalRow.attr('data-action', action)
      @$additionalRow.attr('data-search_text', search_text)
    else
      @$additionalRow.attr('data-action', '')
      @$additionalRow.attr('data-search_text', '')
  
  initializeListContainer: () ->
     @$listContainer.html('')



window.SearchBox = SearchBox
