/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// reset_password.coffee

$(function() {
  const ROOT_SELECTOR = '#resetPasswordView';

  const $resetPasswordView = $(ROOT_SELECTOR);
  const $close = $('[data-parts=close]', $resetPasswordView);
  const $passwordForm = $('input[name=password]', $resetPasswordView);
  const $passwordConfirmForm = $('input[name=password_confirm]', $resetPasswordView);
  const $emailForm = $('input[name=email]', $resetPasswordView);
  const $submitButton = $('[data-parts=submitButton]', $resetPasswordView);
  const $cancelButton = $('[data-parts=submitButton]', $resetPasswordView);

  const $alertMessageView = $('[data-parts=alertMessage]', $resetPasswordView);
  const $alertMessageText = $('[data-parts=alertMessageText]', $resetPasswordView);

  const $successMessage = $('[data-parts=successMessage]', $resetPasswordView);

  var f = {
    validate() {
      f.resetFormAlertStyle();
      if ($passwordForm.val().length === 0) {
        $passwordForm.addClass('alert');
        return false;
      }
      if ($passwordConfirmForm.val().length === 0) {
        $passwordConfirmForm.addClass('alert');
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
      $passwordForm.removeClass('alert');
      $passwordConfirmForm.removeClass('alert');
      return false;
    },

    resetView() {
      $emailForm.val('');
      $alertMessageView.css({'display': 'none'});
      $successMessage.css({'display': 'none'});
      return false;
    },

    showSuccessMessage(message){
      let t;
      $successMessage.css({'display': 'block', 'opacity': 1});
      let c = 0;
      const l = message.length;
      return t = setInterval(function() {
        console.log(message.substring(0, c));
        $successMessage.html(message.substring(0, c));
        c++;
        if (c === l) {
          return clearInterval(t);
        }
      }
      , 5);
    }
  };

  $resetPasswordView.ready(e => $passwordForm.focus());

  $submitButton.on('click', function(e){
    console.log('SUBMIT');
    e.preventDefault();
    if (!f.validate()) {
      return false;
    }
    f.resetAlertMessageView();
    $.ajax({
      url: '/reset_password',
      dataType: 'json',
      type: 'POST',
      data: JSON.stringify({'password': $passwordForm.val(), 'password_confirm': $passwordConfirmForm.val(), 'email': $emailForm.val()}),
      contentType: 'application/json;charset=UTF-8',
      success(result){
        console.log(result);
        if (result['success']) {
          console.log('success');
          $passwordForm.val('');
          $passwordConfirmForm.val('');
          //window.pageControl.closeForgotPasswordView()
          f.showSuccessMessage(result['success']['message']);
        }
          //
        if (result['alert']) {
          console.log(result['alert']['message']);
          f.showAlertMessageView(result['alert']['message']);
          if (result['alert']['is_password_alerted']) {
            $passwordForm.addClass('alert');
          }
          if (result['alert']['is_password_confirm_alerted']) {
            return $passwordConfirmForm.addClass('alert');
          }
        }
      },

      error(XMLHttpRequest, status, error){
        return f.showAlertMessageView(error);
      }
    });
    return false;
  });

  return $close.on('click', function(e) {
    window.pageControl.closeResetPasswordView();
    return false;
  });
});
