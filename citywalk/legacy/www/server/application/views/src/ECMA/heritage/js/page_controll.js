/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// page_control.coffee

class PageControl { 

  constructor() {
    this.popHistory = this.popHistory.bind(this);
    this.openModal = this.openModal.bind(this);
    this.openSignupSelectView = this.openSignupSelectView.bind(this);
    this.closeSignupSelectView = this.closeSignupSelectView.bind(this);
    this.openEmailSignupView = this.openEmailSignupView.bind(this);
    this.closeEmailSignupView = this.closeEmailSignupView.bind(this);
    this.openSigninView = this.openSigninView.bind(this);
    this.closeSigninView = this.closeSigninView.bind(this);
    this.openEmailSigninView = this.openEmailSigninView.bind(this);
    this.closeEmailSigninView = this.closeEmailSigninView.bind(this);
    this.openForgotPasswordView = this.openForgotPasswordView.bind(this);
    this.closeForgotPasswordView = this.closeForgotPasswordView.bind(this);
    this.openResetPasswordView = this.openResetPasswordView.bind(this);
    this.closeResetPasswordView = this.closeResetPasswordView.bind(this);
    this.setInstanceVal();
    this.setEventHandlers();
  }

  setInstanceVal(){
    this.states = [''];
    this.HOST = 'http://ilrsa.localhost:8000';
    return false;
  }

  setEventHandlers(){
    return $(window).on('popstate', e=> {
      console.log('popstate');
      console.log(location.pathname);
      const {
        state
      } = e.originalEvent;
      if (!state) {
        return false;
      }
      return this.goTo(state, true);
    });
  }


  goTo(page_name, pop) {
    const $this = this;
    $.ajax({
      type: 'GET',
      url: '/' + page_name,
      dataType: 'html',
      contentType: 'text/html;charset=UTF-8',
      beforeSend(){
        return $this.wait(true);
      },

      success(data, status, xhr){
        console.log(data);
        console.log(xhr.getResponseHeader("content-type").substring(0, 9));
        if ((xhr.getResponseHeader("content-type").substring(0, 9) === 'text/json') && JSON.parse(data)['open']) {
          $this.openModal(JSON.parse(data)['open']);
        }
        if (xhr.getResponseHeader("content-type").substring(0, 9) === 'text/html') {
          $('#contentView').html(data);
          if (!pop) {
            $this.pushHistory(page_name);
          }
        }
        return $this.wait(false);
      },

      error(data, status){
        console.log(data, status);
        return $this.wait(false);
      }
    });
    return false;
  }

  open(page_name, html){
    this.wait(true);
    $('#contentView').html(html);
    this.pushHistory(page_name);
    this.wait(false);
    return false;
  }

  wait(waiting) {
    if (waiting) {
      return $('html').addClass('wait');
    } else {
      return $('html').removeClass('wait');
    }
  }

  pushHistory(page_name) {
    this.states.push(page_name);
    if (window.history && window.history.pushState) {
      console.log(this.states);
      window.history.pushState(page_name, page_name, '/' + page_name);
    }
    return false;
  }

  popHistory() {
    console.log(this.states);
    console.log('pop');
    if (this.states.length > 1) {
      this.states.pop();
    }
    const prev_state = this.states[this.states.length-1];
    if (window.history && window.history.pushState) {
      console.log(this.states);
      console.log(prev_state);
    }
      //window.history.pushState(prev_state, prev_state, '/' + prev_state)
    return false;
  }

  // open with window_name
  openModal(view_name){
    switch (view_name) {
      case 'signin':
        this.openSigninView();
        break;
      case 'signup_select':
        this.openSignupSelectView();
        break;
      case 'email_signup':
        this.openEmailSignupView();
        break;
      case 'signin_select':
        this.openEmailSigninView();
        break;
      case 'forget_password':
        this.openForgotPasswordView();
        break;
      case 'reset_password':
        this.openResetPasswordView();
        break;
      default:
        this.openSigninView();
    }
    return false;
  }

  // signup select 
  openSignupSelectView(){
    $('#signupSelectView').css({'display': 'block'});
    this.pushHistory('signup_select');
    return false;
  }

  closeSignupSelectView(){
    $('#signupSelectView').css({'display': 'none'});
    this.popHistory();
    return false;
  }

  // email signup
  openEmailSignupView(){
    $('#emailSignupView').css({'display': 'block'});
    this.pushHistory('email_signup');
    return false;
  }

  closeEmailSignupView(){
    $('#emailSignupView').css({'display': 'none'});
    this.popHistory();
    return false;
  }

  // signin 
  openSigninView(){
    $('#signinView').css({'display': 'block'});
    this.pushHistory('signin');
    return false;
  }

  closeSigninView(){
    $('#signinView').css({'display': 'none'});
    this.popHistory();
    return false;
  }

  // email signin
  openEmailSigninView(){
    $('#emailSigninView').css({'display': 'block'});
    this.pushHistory('signin_select');
    return false;
  }

  closeEmailSigninView(){
    $('#emailSigninView').css({'display': 'none'});
    this.popHistory();
    return false;
  }

  // forgot password
  openForgotPasswordView(){
    $('#forgotPasswordView').css({'display': 'block'});
    this.pushHistory('forgot_password');
    return false;
  }

  closeForgotPasswordView(){
    $('#forgotPasswordView').css({'display': 'none'});
    this.popHistory();
    return false;
  }

  // reset password
  openResetPasswordView(){
    $('#resetPasswordView').css({'display': 'block'});
    this.pushHistory('reset_password');
    return false;
  }

  closeResetPasswordView(){
    $('#resetPasswordView').css({'display': 'none'});
    this.popHistory();
    return false;
  }
}


window.PageControl = PageControl; 
