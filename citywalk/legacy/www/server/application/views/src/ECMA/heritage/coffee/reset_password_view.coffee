# reset_password.coffee

$ ->
  ROOT_SELECTOR = '#resetPasswordView'

  $resetPasswordView = $(ROOT_SELECTOR)
  $close = $('[data-parts=close]', $resetPasswordView)
  $passwordForm = $('input[name=password]', $resetPasswordView)
  $passwordConfirmForm = $('input[name=password_confirm]', $resetPasswordView)
  $emailForm = $('input[name=email]', $resetPasswordView)
  $submitButton = $('[data-parts=submitButton]', $resetPasswordView)
  $cancelButton = $('[data-parts=submitButton]', $resetPasswordView)

  $alertMessageView = $('[data-parts=alertMessage]', $resetPasswordView)
  $alertMessageText = $('[data-parts=alertMessageText]', $resetPasswordView)

  $successMessage = $('[data-parts=successMessage]', $resetPasswordView)

  f = {
    validate: () ->
      f.resetFormAlertStyle()
      if $passwordForm.val().length == 0
        $passwordForm.addClass('alert')
        return false
      if $passwordConfirmForm.val().length == 0
        $passwordConfirmForm.addClass('alert')
        return false
      return true

    showAlertMessageView: (message) ->
      $alertMessageView.show()
      $alertMessageView.find('span').html(message)
      return false
  
    resetAlertMessageView: () ->
      $alertMessageView.hide()
      $alertMessageView.find('span').html('')
      return false

    resetFormAlertStyle: () ->
      $passwordForm.removeClass('alert')
      $passwordConfirmForm.removeClass('alert')
      return false

    resetView: () ->
      $emailForm.val('')
      $alertMessageView.css({'display': 'none'})
      $successMessage.css({'display': 'none'})
      return false

    showSuccessMessage: (message)->
      $successMessage.css({'display': 'block', 'opacity': 1})
      c = 0
      l = message.length
      t = setInterval ->
        console.log(message.substring(0, c))
        $successMessage.html(message.substring(0, c))
        c++
        if c == l
          clearInterval(t)
      , 5
  }

  $resetPasswordView.ready (e)->
    $passwordForm.focus()

  $submitButton.on 'click', (e)->
    console.log('SUBMIT')
    e.preventDefault()
    if not f.validate()
      return false
    f.resetAlertMessageView()
    $.ajax({
      url: '/reset_password',
      dataType: 'json',
      type: 'POST',
      data: JSON.stringify({'password': $passwordForm.val(), 'password_confirm': $passwordConfirmForm.val(), 'email': $emailForm.val()})
      contentType: 'application/json;charset=UTF-8'
      success: (result)->
        console.log(result)
        if result['success']
          console.log('success')
          $passwordForm.val('')
          $passwordConfirmForm.val('')
          #window.pageControl.closeForgotPasswordView()
          f.showSuccessMessage(result['success']['message'])
          #
        if result['alert']
          console.log(result['alert']['message'])
          f.showAlertMessageView(result['alert']['message'])
          if result['alert']['is_password_alerted']
            $passwordForm.addClass('alert')
          if result['alert']['is_password_confirm_alerted']
            $passwordConfirmForm.addClass('alert')

      error: (XMLHttpRequest, status, error)->
        f.showAlertMessageView(error)
    })
    return false

  $close.on 'click', (e) ->
    window.pageControl.closeResetPasswordView()
    return false
