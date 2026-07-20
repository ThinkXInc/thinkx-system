# signin.coffee

$ ->

  ROOT_SELECTOR = '#signinView'

  $signinView = $(ROOT_SELECTOR)
  $close = $('[data-parts=close]', $signinView)
  $facebookLogin = $('[data-parts=facebookLogin]', $signinView)
  $emailForm = $('input[name=email]', $signinView)
  $passwordForm = $('input[name=password]', $signinView)
  $submitButton = $('[data-parts=submitButton]', $signinView)
  $alertMessageView = $('[data-parts=alertMessage]', $signinView)
  $alertMessageText = $('[data-parts=alertMessageText]', $signinView)

  $forgotPasswordLink = $('[data-parts=forgotPasswordLink]', $signinView)


  f = {
    validate: () ->
      f.resetFormAlertStyle()
      if $emailForm.val().length == 0
        $emailForm.addClass('alert')
        return false
      if $passwordForm.val().length == 0
        $passwordForm.addClass('alert')
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
      $passwordForm.removeClass('alert')
      return false
  }

  $signinView.ready (e)->
    $emailForm.focus()


  $('input').keypress (e)->
    if e.which == 13
      $submitButton.click()
      return false

  $submitButton.on 'click', (e)->
    console.log('SUBMIT')
    e.preventDefault()
    if not f.validate()
      return false
    console.log($emailForm.val(), $passwordForm.val())
    f.resetAlertMessageView()
    $.ajax({
      url: '/signin',
      dataType: 'json',
      type: 'POST',
      data: JSON.stringify({'email': $emailForm.val(), 'password': $passwordForm.val()})
      contentType: 'application/json;charset=UTF-8'
      success: (result)->
        console.log(result)
        if result['success']
          console.log('success')
          window.pageControl.closeSigninView()
          location.href = '/'
        if result['alert']
          console.log(result['alert']['message'])
          f.showAlertMessageView(result['alert']['message'])
          if result['alert']['is_email_alerted']
            console.log('alerted')
            $emailForm.addClass('alert')
          if result['alert']['is_password_alerted']
            console.log('alerted')
            $passwordForm.addClass('alert')

      error: (XMLHttpRequest, status, error)->
        f.showAlertMessageView(error)
    })
    return false

  $close.on 'click', (e) ->
    window.pageControl.closeSigninView()
    return false

  $forgotPasswordLink.on 'click', (e) ->
    window.pageControl.closeSigninView()
    window.pageControl.openForgotPasswordView()
    return false

  $signinView.on 'click', '[data-action=signup]', (e) ->
    console.log('signUp')
    window.pageControl.closeSigninView()
    window.pageControl.openSignupSelectView()
    return false


