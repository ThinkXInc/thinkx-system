/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// modal_view.coffee
//
// $("#elem_id").loadingIndicatorView({
// });

class ModalView {
  static initClass() {
   
    /* STATIC VARIABLES */
    
    this.prototype.BASE_TEMPLATE  =
      `\
<div class="modalView" id="$modal_id">
  <div class="modalViewContainer" data-parts="modalViewContainer">
    <div class="modalViewContent" data-parts="modalViewContent">
  
    </div>
    <div class="modalViewBottom cf">
      <div class="alert" data-parts="modalViewAlert">
      </div>
      <div class="buttons">
        <button type="button" class="cancel" data-parts='cancel'>Cancel</button>
        <button type="button" class="done" data-parts='done'>Done</button>
      </div>
    </div>
  </div>
</div>\
`;
  }

  /* CONSTRUCTOR */
  
  constructor(modal_id, content) {
    // append indicator view to document
    this.setLayout = this.setLayout.bind(this);
    this.show = this.show.bind(this);
    this.hide = this.hide.bind(this);
    this.showAlert = this.showAlert.bind(this);
    this.hideAlert = this.hideAlert.bind(this);
    $('body').append(this.BASE_TEMPLATE.replace('$modal_id', modal_id));
    // init parts
    this._initParts('#'+modal_id);
    // set event handlers
    this._setEventHandlers();
    // init instance valuables
    this._initInstanceValuables();
  }


  /* INITIALIZE INSTANCE VALIABLES */
  _initInstanceValuables() {
    this.is_shown = false;
    return false;
  }


  /* INITIALIZE COMPONENT PARTS */
  
  _initParts(ROOT_SELECTOR) {
    this.$modalView = $(ROOT_SELECTOR);
    this.$modalViewContainer = $('[data-parts=modalViewContainer]', ROOT_SELECTOR);
    this.$modalViewContent = $('[data-parts=modalViewContent]', ROOT_SELECTOR);
    this.$cancelButton = $('[data-parts=cancel]', ROOT_SELECTOR);
    this.$doneButton = $('[data-parts=done]', ROOT_SELECTOR);
    this.$alert = $('[data-parts=modalViewAlert]', ROOT_SELECTOR);
    return false;
  }


  /* SET INPUT ATTRIBUTES */
  

  /* SET LAYOUT */
  
  setLayout() {
    console.log('set layout');
    const window_H = $(window).height();
    console.log(this.$modalViewContainer);
    const view_H = this.$modalViewContainer.height();
    console.log(view_H);
    const container_top = window_H>view_H ? Math.floor((window_H-view_H)/2) : 10;
    console.log(container_top);
    this.$modalViewContainer.css('margin-top', container_top);
    return false;
  }


  /* EVENT HANDLERS */

  _setEventHandlers() {
    this.$cancelButton.on('click', e => {
      return this.hide();
    });

    this.$doneButton.on('click', e => {
      return false;
    });

    return false;
  }

  /* FUNCTIONS */

  show() {
    console.log('show');
    this.$modalView.css('display', 'block');
    this.setLayout();
    console.log('display');
    this.$modalView.animate({
      opacity: 1
    }, 200, this.DEFAULT_EASE_TYPE, () => {
      this.is_shown = true;
      return this.$modalView.trigger('show');
    });
    $('#mainView').css({'user-select': 'user-select', 'none': 'none'});
    $('#mainView').css({'-webkit-user-select': '-webkit-user-select', 'none': 'none'});
    $('#mainView').css({'-moz-user-select': '-moz-user-select', 'none': 'none'});
    $('#mainView').css({'-ms-user-select': '-ms-user-select', 'none': 'none'});
    return false;
  }

  hide() {
    this.$modalView.animate({
      opacity: 0
    }, 200, this.DEFAULT_EASE_TYPE, () => {
      this.$modalView.css('display', 'none');
      this.is_shown = false;
      return this.$modalView.trigger('hide');
    });
    $('#mainView').css({'user-select': 'user-select', 'initial': 'initial'});
    $('#mainView').css({'-webkit-user-select': '-webkit-user-select', 'initial': 'initial'});
    $('#mainView').css({'-moz-user-select': '-moz-user-select', 'initial': 'initial'});
    $('#mainView').css({'-ms-user-select': '-ms-user-select', 'initial': 'initial'});
    return false;
  }

  showAlert(message) {
    this.$alert.html(message);
    this.$alert.css({'display':'block'});
    return false;
  }

  hideAlert() {
    this.$alert.html('');
    this.$alert.css({'display': 'none'});
    return false;
  }
}
ModalView.initClass();

window.ModalView = ModalView;
