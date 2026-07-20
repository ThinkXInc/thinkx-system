# review_modal.coffee
#

class ReviewModal extends ModalView

  ### STATIC VARIABLES ###

  TEMPLATE :\
    '''
    <div class="tapToRate">
      <i class="rating rate0" data-parts="rating" data-rate="0">
        <span class="rateTapArea" data-parts="rateTapArea1"></span>
        <span class="rateTapArea" data-parts="rateTapArea2"></span>
        <span class="rateTapArea" data-parts="rateTapArea3"></span>
        <span class="rateTapArea" data-parts="rateTapArea4"></span>
        <span class="rateTapArea" data-parts="rateTapArea5"></span>
      </i> 
      <p>Tap to Rate</p>
    </div>
    <textarea placeholder="Review (Optional)" name="review" data-parts="revewTextArea">
    </textarea>
    <div class="favorite" data-parts="favorite" data-value="no">Favorite</div>
    <div class="share">
      <svg data-parts="fb_share" data-toggle='off' class="fb_button share_btn" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
      	 viewBox="0 0 100 100" enable-background="new 0 0 100 100" xml:space="preserve">
      <path class="path" fill="#FFF" stroke="#FFFFFF" stroke-miterlimit="10" d="M95.7,1.5H5.1C2.9,1.5,0.5,2.8,0.5,5v90.6c0,2.2,2.4,3.9,4.6,3.9h48.4
      	v-39h-13v-15h13V34.7c0-12.7,8-19.7,19.3-19.7c5.4,0,10.7,0.4,11.7,0.6v13.3l-8.3,0c-6.2,0-7.7,2.9-7.7,7.2v9.4h15.2l-1.9,15H68.5
      	v39h27.2c2.2,0,2.8-1.7,2.8-3.9V5C98.5,2.8,97.9,1.5,95.7,1.5z"/>
      </svg>
      <svg data-parts="tw_share" data-toggle='off' class="tw_button share_btn" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
      	 viewBox="0 0 100 100" enable-background="new 0 0 100 100" xml:space="preserve">
      <path class="path" fill="" stroke="#FFFFFF" stroke-miterlimit="10" d="M69,99.5h26.3c2.2,0,3.2-2.5,3.2-4.6v-90c0-2.2-1-3.4-3.2-3.4h-90
      	c-2.2,0-4.8,1.2-4.8,3.4v90c0,2.2,2.6,4.6,4.8,4.6h48.4H69z"/>
      <path class="path" fill="#FFF" stroke="#FFFFFF" stroke-miterlimit="10" d="M51.2,43.3c-2-7.9,3.5-14,8.2-15.5c4.7-1.5,10.7-0.3,14.2,3.5
      	c0,0,5.2-1.3,8.4-3.2c0,0-1.8,5.1-6,7.1c0,0,3.3-0.1,7.7-2c0,0-2.6,3.8-6.7,6.9c0,34.5-34.6,48.3-57.1,33.2c0,0,10.7,1.4,19.2-5.4
      	c0,0-9.5,0-12.4-9.1c0,0,3.9,0.6,6.1-0.3c0,0-10-2.1-10.6-13c0,0,1.7,1.9,6.1,1.7c0,0-9.6-5.9-4.2-17.8
      	C24.2,29.4,34.8,44.2,51.2,43.3z"/>
      </svg>
    </div>
    '''

  MODAL_ID : 'reviewModal'
  POST_REVIEW_URL : '/post_review'
  MOVIE_VIEW_SELECTOR : '#movieView'


  ### CONSTRUCTOR ###
  
  constructor: () ->
    # call ModalView constructor
    super(@MODAL_ID)
    # set content
    $('#'+@MODAL_ID).find('[data-parts=modalViewContent]').html(@TEMPLATE)
    # init parts
    @initParts('#'+@MODAL_ID)
    # set event handlers
    @setEventHandlers()
    # set this instance to window object
    window.reviewView = @

  show: () ->
    console.log('show')
    # set initial value
    @setDefaultVal()
    super()


  ### EVENT HANDLERS ###
  
  setEventHandlers: () ->
    @$rateTapArea1.on 'click', (e) =>
      if @$favorite.attr('data-value') != 'yes'
        @setRate(1)

    @$rateTapArea2.on 'click', (e) =>
      if @$favorite.attr('data-value') != 'yes'
        @setRate(2)

    @$rateTapArea3.on 'click', (e) =>
      if @$favorite.attr('data-value') != 'yes'
        @setRate(3)

    @$rateTapArea4.on 'click', (e) =>
      if @$favorite.attr('data-value') != 'yes'
        @setRate(4)

    @$rateTapArea5.on 'click', (e) =>
      if @$favorite.attr('data-value') != 'yes'
        @setRate(5)

    @$reviewTextArea.on 'focus', (e) =>
      if @$favorite.attr('data-value') != 'yes'
        console.log('f')

    @$doneButton.on 'click', (e) =>
      e.preventDefault()
      movie_id = $('input[name=movie_id]').val()
      movie_title = $('input[name=movie_title]').val()
      user_fullname = $('input[name=user_fullname]').val()
      rating = @getRate()
      review = if @$reviewTextArea.val() then @$reviewTextArea.val() else null
      favorite = if @$favorite.attr('data-value') == 'yes' then true else false
      $this = @
      $fbShare = @$fbShare
      $twShare = @$twShare
      $.ajax
        url: @POST_REVIEW_URL 
        type: 'POST'
        dataType: 'JSON'
        data: JSON.stringify({'movie_id': movie_id, 'rating': rating, 'review': review, 'favorite': favorite})
        contentType: 'application/json;charset=UTF-8'
        beforeSend: () ->
          window.loadingIndicatorView.show()
          console.log('before send')
        success: (results) ->
          console.log(results)
          window.loadingIndicatorView.hide()
          $this.updateDefaultVal(rating, review, $this.$favorite.attr('data-value'))
          if results['error']
            $this.showAlert(results['message'])
          else
            $this.hide()

          is_fbshare_on = $fbShare.attr('data-toggle') == 'on'
          is_twshare_on = $twShare.attr('data-toggle') == 'on'
          share_text = user_fullname+' watched 『'+movie_title+'』\n\n'+review
          hash_tags = 'ILRSA,film'
          if is_fbshare_on
            console.log('fb share')
            message = share_text
            FB.ui({
                method: 'share_open_graph',
                action_type: 'og.like',
                action_properties: JSON.stringify({
                  object: location.href,
                  message: message,
                  image: 'http://data.ilrsa.com/resources/movies/cover/en/'+movie_id+'.jpg?width=110&height=163&type=resize'
                })
              }, (response)->
            )
          if is_twshare_on
            console.log('tw share')
            text = 'Watched 『'+movie_title+'』and rated '+rating+'\n #ILRSA'
            window.open('https://twitter.com/share?original_referer='+location.href+'&text='+share_text+'&hashtags='+hash_tags, null, 'width=500,height=400')



        error: (data) ->
          console.log('[WARNING] AJAX ERROR')
          console.log(data)
          window.loadingIndicatorView.hide()

    @$favorite.on 'click', (e) =>
      val = @$favorite.attr('data-value')
      if val == 'no'
        @setFavorite(true)
      else
        @setFavorite(false)
      return false

    @$fbShare.on 'click', (e)=>
      console.log('fb')
      if @$fbShare.attr('class') == 'fb_button share_btn'
        @$fbShare.attr('class', 'fb_button share_btn on')
        @$fbShare.attr('data-toggle', 'on')
      else
        @$fbShare.attr('class', 'fb_button share_btn')
        @$fbShare.attr('data-toggle', 'off')
      return false

    @$twShare.on 'click', (e)=>
      if @$twShare.attr('class') == 'tw_button share_btn'
        @$twShare.attr('class', 'tw_button share_btn on')
        @$twShare.attr('data-toggle', 'on')
      else
        @$twShare.attr('class', 'tw_button share_btn')
        @$twShare.attr('data-toggle', 'off')
      return false


  ### FUNCTIONS ###
  
  setDefaultVal: () =>
    rating = $('input[name=rating]', $('#movieView')).val()
    review = $('input[name=review]', $('#movieView')).val()
    favorite = $('input[name=favorite]', $('#movieView')).val()
    if rating
      if favorite == 'yes'
        @setFavorite(true)
      else
        @setFavorite(false)
      @setRate(rating)
      @$reviewTextArea.val(review)
    return false
    
  updateDefaultVal: (rating, review, favorite)=>
    $('input[name=rating]', $('#movieView')).val(rating)
    $('input[name=review]', $('#movieView')).val(review)
    $('input[name=favorite]', $('#movieView')).val(favorite)
    return false

  setFavorite: (favorited)=>
    if favorited
      @$favorite.attr('data-value', 'yes')
      @$favorite.addClass('on')
      @setRate(5)
    else
      @$favorite.attr('data-value', 'no')
      @$favorite.removeClass('on')

  setRate: (rate) =>
    remove_nums = [0, 1, 2, 3, 4, 5].filter (item) ->
      return item != rate
    for i in remove_nums 
      @$rating.removeClass('rate'+i)
    @$rating.addClass('rate'+rate)
    @$rating.attr('data-rate', rate)
    return false

  getRate: () =>
    return @$rating.attr('data-rate')

  ### INITIALIZE COMPONENT PARTS ###

  initParts: (ROOT_SELECTOR) ->
    @$reviewModal = $(ROOT_SELECTOR)
    @$rating = $('[data-parts=rating]', ROOT_SELECTOR)
    @$reviewTextArea = $('textarea[name=review]', ROOT_SELECTOR)
    @$rateTapArea1 = $('[data-parts=rateTapArea1]', ROOT_SELECTOR)
    @$rateTapArea2 = $('[data-parts=rateTapArea2]', ROOT_SELECTOR)
    @$rateTapArea3 = $('[data-parts=rateTapArea3]', ROOT_SELECTOR)
    @$rateTapArea4 = $('[data-parts=rateTapArea4]', ROOT_SELECTOR)
    @$rateTapArea5 = $('[data-parts=rateTapArea5]', ROOT_SELECTOR)
    @$favorite = $('[data-parts=favorite]', ROOT_SELECTOR)
    @$fbShare = $('[data-parts=fb_share]', ROOT_SELECTOR)
    @$twShare = $('[data-parts=tw_share]', ROOT_SELECTOR)


window.ReviewModal = ReviewModal
