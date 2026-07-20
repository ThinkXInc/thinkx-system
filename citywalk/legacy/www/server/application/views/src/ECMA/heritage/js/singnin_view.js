/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// signin.coffee

$(function() {

  const ROOT_SELECTOR = '#signinView';

  const $signinView = $(ROOT_SELECTOR);
  const $close = $('[data-parts=close]', $signinView);
  const $facebookLogin = $('[data-parts=facebookLogin]', $signinView);
  const $emailForm = $('input[name=email]', $signinView);
  const $passwordForm = $('input[name=password]', $signinView);
  const $submitButton = $('[data-parts=submitButton]', $signinView);
  const $alertMessageView = $('[data-parts=alertMessage]', $signinView);
  const $alertMessageText = $('[data-parts=alertMessageText]', $signinView);

  const $forgotPasswordLink = $('[data-parts=forgotPasswordLink]', $signinView);


  var f = {
    validate() {
      f.resetFormAlertStyle();
      if ($emailForm.val().length === 0) {
        $emailForm.addClass('alert');
        return false;
      }
      if ($passwordForm.val().length === 0) {
        $passwordForm.addClass('alert');
        return false;
      }
      return true;
    },

    showAlertMessageView(message) {
      $alertMessageView.show();
      $alertMessageView.find('span').html(message);
      return false;
    },
  
    resetAlertMessageView() {
      $alertMessageView.hide();
      $alertMessageView.find('span').html('');
      return false;
    },

    resetFormAlertStyle() {
      $emailForm.removeClass('alert');
      $passwordForm.removeClass('alert');
      return false;
    }
  };

  $signinView.ready(e => $emailForm.focus());


  $('input').keypress(function(e){
    if (e.which === 13) {
      $submitButton.click();
      return false;
    }
  });

  $submitButton.on('click', function(e){
    console.log('SUBMIT');
    e.preventDefault();
    if (!f.validate()) {
      return false;
    }
    console.log($emailForm.val(), $passwordForm.val());
    f.resetAlertMessageView();
    $.ajax({
      url: '/signin',
      dataType: 'json',
      type: 'POST',
      data: JSON.stringify({'email': $emailForm.val(), 'password': $passwordForm.val()}),
      contentType: 'application/json;charset=UTF-8',
      success(result){
        console.log(result);
        if (result['success']) {
          console.log('success');
          window.pageControl.closeSigninView();
          location.href = '/';
        }
        if (result['alert']) {
          console.log(result['alert']['message']);
          f.showAlertMessageView(result['alert']['message']);
          if (result['alert']['is_email_alerted']) {
            console.log('alerted');
            $emailForm.addClass('alert');
          }
          if (result['alert']['is_password_alerted']) {
            console.log('alerted');
            return $passwordForm.addClass('alert');
          }
        }
      },

      error(XMLHttpRequest, status, error){
        return f.showAlertMessageView(error);
      }
    });
    return false;
  });

  $close.on('click', function(e) {
    window.pageControl.closeSigninView();
    return false;
  });

  $forgotPasswordLink.on('click', function(e) {
    window.pageControl.closeSigninView();
    window.pageControl.openForgotPasswordView();
    return false;
  });

  return $signinView.on('click', '[data-action=signup]', function(e) {
    console.log('signUp');
    window.pageControl.closeSigninView();
    window.pageControl.openSignupSelectView();
    return false;
  });
});


