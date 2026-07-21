# page_control.coffee

class PageControl 

  constructor: () ->
    @setInstanceVal()
    @setEventHandlers()

  setInstanceVal: ()->
    @states = ['']
    @HOST = 'http://ilrsa.localhost:8000'
    return false

  setEventHandlers: ()->
    $(window).on 'popstate', (e)=>
      console.log('popstate')
      console.log(location.pathname)
      state = e.originalEvent.state
      if not state
        return false
      @goTo(state, true)


  goTo: (page_name, pop) ->
    $this = @
    $.ajax
      type: 'GET'
      url: '/' + page_name
      dataType: 'html'
      contentType: 'text/html;charset=UTF-8'
      beforeSend: ()->
        $this.wait(true)

      success: (data, status, xhr)->
        console.log(data)
        console.log(xhr.getResponseHeader("content-type").substring(0, 9))
        if xhr.getResponseHeader("content-type").substring(0, 9) == 'text/json' and JSON.parse(data)['open']
          $this.openModal(JSON.parse(data)['open'])
        if xhr.getResponseHeader("content-type").substring(0, 9) == 'text/html'
          $('#contentView').html(data)
          if not pop
            $this.pushHistory(page_name)
        $this.wait(false)

      error: (data, status)->
        console.log(data, status)
        $this.wait(false)
    return false

  open: (page_name, html)->
    @.wait(true)
    $('#contentView').html(html)
    @.pushHistory(page_name)
    @.wait(false)
    return false

  wait: (waiting) ->
    if waiting
      $('html').addClass('wait')
    else
      $('html').removeClass('wait')

  pushHistory: (page_name) ->
    @states.push(page_name)
    if window.history and window.history.pushState
      console.log(@states)
      window.history.pushState(page_name, page_name, '/' + page_name)
    return false

  popHistory: () =>
    console.log(@states)
    console.log('pop')
    if @states.length > 1
      @states.pop()
    prev_state = @states[@states.length-1]
    if window.history and window.history.pushState
      console.log(@states)
      console.log(prev_state)
      #window.history.pushState(prev_state, prev_state, '/' + prev_state)
    return false

  # open with window_name
  openModal: (view_name)=>
    switch view_name
      when 'signin'
        @openSigninView()
      when 'signup_select'
        @openSignupSelectView()
      when 'email_signup'
        @openEmailSignupView()
      when 'signin_select'
        @openEmailSigninView()
      when 'forget_password'
        @openForgotPasswordView()
      when 'reset_password'
        @openResetPasswordView()
      else
        @openSigninView()
    return false

  # signup select 
  openSignupSelectView: ()=>
    $('#signupSelectView').css({'display': 'block'})
    @pushHistory('signup_select')
    return false

  closeSignupSelectView: ()=>
    $('#signupSelectView').css({'display': 'none'})
    @popHistory()
    return false

  # email signup
  openEmailSignupView: ()=>
    $('#emailSignupView').css({'display': 'block'})
    @pushHistory('email_signup')
    return false

  closeEmailSignupView: ()=>
    $('#emailSignupView').css({'display': 'none'})
    @popHistory()
    return false

  # signin 
  openSigninView: ()=>
    $('#signinView').css({'display': 'block'})
    @pushHistory('signin')
    return false

  closeSigninView: ()=>
    $('#signinView').css({'display': 'none'})
    @popHistory()
    return false

  # email signin
  openEmailSigninView: ()=>
    $('#emailSigninView').css({'display': 'block'})
    @pushHistory('signin_select')
    return false

  closeEmailSigninView: ()=>
    $('#emailSigninView').css({'display': 'none'})
    @popHistory()
    return false

  # forgot password
  openForgotPasswordView: ()=>
    $('#forgotPasswordView').css({'display': 'block'})
    @pushHistory('forgot_password')
    return false

  closeForgotPasswordView: ()=>
    $('#forgotPasswordView').css({'display': 'none'})
    @popHistory()
    return false

  # reset password
  openResetPasswordView: ()=>
    $('#resetPasswordView').css({'display': 'block'})
    @pushHistory('reset_password')
    return false

  closeResetPasswordView: ()=>
    $('#resetPasswordView').css({'display': 'none'})
    @popHistory()
    return false


window.PageControl = PageControl 
