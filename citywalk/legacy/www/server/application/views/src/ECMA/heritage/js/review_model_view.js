/*
 * decaffeinate suggestions:
 * DS002: Fix invalid constructor
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// review_modal.coffee
//

class ReviewModal extends ModalView {
  static initClass() {
  
    /* STATIC VARIABLES */
  
    this.prototype.TEMPLATE  =
      `\
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
</div>\
`;
  
    this.prototype.MODAL_ID  = 'reviewModal';
    this.prototype.POST_REVIEW_URL  = '/post_review';
    this.prototype.MOVIE_VIEW_SELECTOR  = '#movieView';
  }


  /* CONSTRUCTOR */
  
  constructor() {
    // call ModalView constructor
    this.setDefaultVal = this.setDefaultVal.bind(this);
    this.updateDefaultVal = this.updateDefaultVal.bind(this);
    this.setFavorite = this.setFavorite.bind(this);
    this.setRate = this.setRate.bind(this);
    this.getRate = this.getRate.bind(this);
    super(this.MODAL_ID);
    // set content
    $('#'+this.MODAL_ID).find('[data-parts=modalViewContent]').html(this.TEMPLATE);
    // init parts
    this.initParts('#'+this.MODAL_ID);
    // set event handlers
    this.setEventHandlers();
    // set this instance to window object
    window.reviewView = this;
  }

  show() {
    console.log('show');
    // set initial value
    this.setDefaultVal();
    return super.show();
  }


  /* EVENT HANDLERS */
  
  setEventHandlers() {
    this.$rateTapArea1.on('click', e => {
      if (this.$favorite.attr('data-value') !== 'yes') {
        return this.setRate(1);
      }
    });

    this.$rateTapArea2.on('click', e => {
      if (this.$favorite.attr('data-value') !== 'yes') {
        return this.setRate(2);
      }
    });

    this.$rateTapArea3.on('click', e => {
      if (this.$favorite.attr('data-value') !== 'yes') {
        return this.setRate(3);
      }
    });

    this.$rateTapArea4.on('click', e => {
      if (this.$favorite.attr('data-value') !== 'yes') {
        return this.setRate(4);
      }
    });

    this.$rateTapArea5.on('click', e => {
      if (this.$favorite.attr('data-value') !== 'yes') {
        return this.setRate(5);
      }
    });

    this.$reviewTextArea.on('focus', e => {
      if (this.$favorite.attr('data-value') !== 'yes') {
        return console.log('f');
      }
    });

    this.$doneButton.on('click', e => {
      e.preventDefault();
      const movie_id = $('input[name=movie_id]').val();
      const movie_title = $('input[name=movie_title]').val();
      const user_fullname = $('input[name=user_fullname]').val();
      const rating = this.getRate();
      const review = this.$reviewTextArea.val() ? this.$reviewTextArea.val() : null;
      const favorite = this.$favorite.attr('data-value') === 'yes' ? true : false;
      const $this = this;
      const {
        $fbShare
      } = this;
      const {
        $twShare
      } = this;
      return $.ajax({
        url: this.POST_REVIEW_URL, 
        type: 'POST',
        dataType: 'JSON',
        data: JSON.stringify({'movie_id': movie_id, 'rating': rating, 'review': review, 'favorite': favorite}),
        contentType: 'application/json;charset=UTF-8',
        beforeSend() {
          window.loadingIndicatorView.show();
          return console.log('before send');
        },
        success(results) {
          console.log(results);
          window.loadingIndicatorView.hide();
          $this.updateDefaultVal(rating, review, $this.$favorite.attr('data-value'));
          if (results['error']) {
            $this.showAlert(results['message']);
          } else {
            $this.hide();
          }

          const is_fbshare_on = $fbShare.attr('data-toggle') === 'on';
          const is_twshare_on = $twShare.attr('data-toggle') === 'on';
          const share_text = user_fullname+' watched 『'+movie_title+'』\n\n'+review;
          const hash_tags = 'ILRSA,film';
          if (is_fbshare_on) {
            console.log('fb share');
            const message = share_text;
            FB.ui({
                method: 'share_open_graph',
                action_type: 'og.like',
                action_properties: JSON.stringify({
                  object: location.href,
                  message,
                  image: 'http://data.ilrsa.com/resources/movies/cover/en/'+movie_id+'.jpg?width=110&height=163&type=resize'
                })
              }, function(response){}
            );
          }
          if (is_twshare_on) {
            console.log('tw share');
            const text = 'Watched 『'+movie_title+'』and rated '+rating+'\n #ILRSA';
            return window.open('https://twitter.com/share?original_referer='+location.href+'&text='+share_text+'&hashtags='+hash_tags, null, 'width=500,height=400');
          }
        },



        error(data) {
          console.log('[WARNING] AJAX ERROR');
          console.log(data);
          return window.loadingIndicatorView.hide();
        }
      });
    });

    this.$favorite.on('click', e => {
      const val = this.$favorite.attr('data-value');
      if (val === 'no') {
        this.setFavorite(true);
      } else {
        this.setFavorite(false);
      }
      return false;
    });

    this.$fbShare.on('click', e=> {
      console.log('fb');
      if (this.$fbShare.attr('class') === 'fb_button share_btn') {
        this.$fbShare.attr('class', 'fb_button share_btn on');
        this.$fbShare.attr('data-toggle', 'on');
      } else {
        this.$fbShare.attr('class', 'fb_button share_btn');
        this.$fbShare.attr('data-toggle', 'off');
      }
      return false;
    });

    return this.$twShare.on('click', e=> {
      if (this.$twShare.attr('class') === 'tw_button share_btn') {
        this.$twShare.attr('class', 'tw_button share_btn on');
        this.$twShare.attr('data-toggle', 'on');
      } else {
        this.$twShare.attr('class', 'tw_button share_btn');
        this.$twShare.attr('data-toggle', 'off');
      }
      return false;
    });
  }


  /* FUNCTIONS */
  
  setDefaultVal() {
    const rating = $('input[name=rating]', $('#movieView')).val();
    const review = $('input[name=review]', $('#movieView')).val();
    const favorite = $('input[name=favorite]', $('#movieView')).val();
    if (rating) {
      if (favorite === 'yes') {
        this.setFavorite(true);
      } else {
        this.setFavorite(false);
      }
      this.setRate(rating);
      this.$reviewTextArea.val(review);
    }
    return false;
  }
    
  updateDefaultVal(rating, review, favorite){
    $('input[name=rating]', $('#movieView')).val(rating);
    $('input[name=review]', $('#movieView')).val(review);
    $('input[name=favorite]', $('#movieView')).val(favorite);
    return false;
  }

  setFavorite(favorited){
    if (favorited) {
      this.$favorite.attr('data-value', 'yes');
      this.$favorite.addClass('on');
      return this.setRate(5);
    } else {
      this.$favorite.attr('data-value', 'no');
      return this.$favorite.removeClass('on');
    }
  }

  setRate(rate) {
    const remove_nums = [0, 1, 2, 3, 4, 5].filter(item => item !== rate);
    for (let i of Array.from(remove_nums)) { 
      this.$rating.removeClass('rate'+i);
    }
    this.$rating.addClass('rate'+rate);
    this.$rating.attr('data-rate', rate);
    return false;
  }

  getRate() {
    return this.$rating.attr('data-rate');
  }

  /* INITIALIZE COMPONENT PARTS */

  initParts(ROOT_SELECTOR) {
    this.$reviewModal = $(ROOT_SELECTOR);
    this.$rating = $('[data-parts=rating]', ROOT_SELECTOR);
    this.$reviewTextArea = $('textarea[name=review]', ROOT_SELECTOR);
    this.$rateTapArea1 = $('[data-parts=rateTapArea1]', ROOT_SELECTOR);
    this.$rateTapArea2 = $('[data-parts=rateTapArea2]', ROOT_SELECTOR);
    this.$rateTapArea3 = $('[data-parts=rateTapArea3]', ROOT_SELECTOR);
    this.$rateTapArea4 = $('[data-parts=rateTapArea4]', ROOT_SELECTOR);
    this.$rateTapArea5 = $('[data-parts=rateTapArea5]', ROOT_SELECTOR);
    this.$favorite = $('[data-parts=favorite]', ROOT_SELECTOR);
    this.$fbShare = $('[data-parts=fb_share]', ROOT_SELECTOR);
    return this.$twShare = $('[data-parts=tw_share]', ROOT_SELECTOR);
  }
}
ReviewModal.initClass();


window.ReviewModal = ReviewModal;
