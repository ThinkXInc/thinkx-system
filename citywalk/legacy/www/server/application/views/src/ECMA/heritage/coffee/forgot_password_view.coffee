# forgot_password.coffee

$ ->
  ROOT_SELECTOR = '#forgotPasswordView'

  $forgotPasswordView = $(ROOT_SELECTOR)
  $close = $('[data-parts=close]', $forgotPasswordView)
  $emailForm = $('input[name=email]', $forgotPasswordView)
  $submitButton = $('[data-parts=submitButton]', $forgotPasswordView)

  $alertMessageView = $('[data-parts=alertMessage]', $forgotPasswordView)
  $alertMessageText = $('[data-parts=alertMessageText]', $forgotPasswordView)

  $successMessage = $('[data-parts=successMessage]', $forgotPasswordView)

  f = {
    validate: () ->
      f.resetFormAlertStyle()
      if $emailForm.val().length == 0
        $emailForm.addClass('alert')
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
      $emailForm.removeClass('alert')
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
          $emailForm.val('')
          clearInterval(t)
          ###
          t = setTimeout ->
            f.resetView()
            window.pageControl.closeForgotPasswordView()
          , 1000
          ###
      , 5
  }

  $forgotPasswordView.ready (e)->
    $emailForm.focus()

  $submitButton.on 'click', (e)->
    console.log('SUBMIT')
    e.preventDefault()
    if not f.validate()
      return false
    console.log($emailForm.val())
    f.resetAlertMessageView()
    $.ajax({
      url: '/forgot_password',
      dataType: 'json',
      type: 'POST',
      data: JSON.stringify({'email': $emailForm.val()})
      contentType: 'application/json;charset=UTF-8'
      success: (result)->
        console.log(result)
        if result['success']
          console.log('success')
          #window.pageControl.closeForgotPasswordView()
          f.showSuccessMessage(result['success']['message'])
          #
        if result['alert']
          console.log(result['alert']['message'])
          f.showAlertMessageView(result['alert']['message'])
          if result['alert']['is_email_alerted']
            console.log('alerted')
            $emailForm.addClass('alert')

      error: (XMLHttpRequest, status, error)->
        f.showAlertMessageView(error)
    })
    return false

  $close.on 'click', (e) ->
    window.pageControl.closeForgotPasswordView()
    return false
