/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// forgot_password.coffee

$(function() {
  const ROOT_SELECTOR = '#forgotPasswordView';

  const $forgotPasswordView = $(ROOT_SELECTOR);
  const $close = $('[data-parts=close]', $forgotPasswordView);
  const $emailForm = $('input[name=email]', $forgotPasswordView);
  const $submitButton = $('[data-parts=submitButton]', $forgotPasswordView);

  const $alertMessageView = $('[data-parts=alertMessage]', $forgotPasswordView);
  const $alertMessageText = $('[data-parts=alertMessageText]', $forgotPasswordView);

  const $successMessage = $('[data-parts=successMessage]', $forgotPasswordView);

  var f = {
    validate() {
      f.resetFormAlertStyle();
      if ($emailForm.val().length === 0) {
        $emailForm.addClass('alert');
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
          $emailForm.val('');
          return clearInterval(t);
          /*
          t = setTimeout ->
            f.resetView()
            window.pageControl.closeForgotPasswordView()
          , 1000
          */
        }
      }
      , 5);
    }
  };

  $forgotPasswordView.ready(e => $emailForm.focus());

  $submitButton.on('click', function(e){
    console.log('SUBMIT');
    e.preventDefault();
    if (!f.validate()) {
      return false;
    }
    console.log($emailForm.val());
    f.resetAlertMessageView();
    $.ajax({
      url: '/forgot_password',
      dataType: 'json',
      type: 'POST',
      data: JSON.stringify({'email': $emailForm.val()}),
      contentType: 'application/json;charset=UTF-8',
      success(result){
        console.log(result);
        if (result['success']) {
          console.log('success');
          //window.pageControl.closeForgotPasswordView()
          f.showSuccessMessage(result['success']['message']);
        }
          //
        if (result['alert']) {
          console.log(result['alert']['message']);
          f.showAlertMessageView(result['alert']['message']);
          if (result['alert']['is_email_alerted']) {
            console.log('alerted');
            return $emailForm.addClass('alert');
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
    window.pageControl.closeForgotPasswordView();
    return false;
  });
});
