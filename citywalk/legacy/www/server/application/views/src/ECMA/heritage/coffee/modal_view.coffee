# modal_view.coffee
#
# $("#elem_id").loadingIndicatorView({
# });

class ModalView
 
  ### STATIC VARIABLES ###
  
  BASE_TEMPLATE :\
    '''
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
    </div>
    '''

  ### CONSTRUCTOR ###
  
  constructor: (modal_id, content) ->
    # append indicator view to document
    $('body').append(@BASE_TEMPLATE.replace('$modal_id', modal_id))
    # init parts
    @_initParts('#'+modal_id)
    # set event handlers
    @_setEventHandlers()
    # init instance valuables
    @_initInstanceValuables()


  ### INITIALIZE INSTANCE VALIABLES ###
  _initInstanceValuables: () ->
    @is_shown = false
    return false


  ### INITIALIZE COMPONENT PARTS ###
  
  _initParts: (ROOT_SELECTOR) ->
    @$modalView = $(ROOT_SELECTOR)
    @$modalViewContainer = $('[data-parts=modalViewContainer]', ROOT_SELECTOR)
    @$modalViewContent = $('[data-parts=modalViewContent]', ROOT_SELECTOR)
    @$cancelButton = $('[data-parts=cancel]', ROOT_SELECTOR)
    @$doneButton = $('[data-parts=done]', ROOT_SELECTOR)
    @$alert = $('[data-parts=modalViewAlert]', ROOT_SELECTOR)
    return false


  ### SET INPUT ATTRIBUTES ###
  

  ### SET LAYOUT ###
  
  setLayout: () =>
    console.log('set layout')
    window_H = $(window).height()
    console.log(@$modalViewContainer)
    view_H = @$modalViewContainer.height()
    console.log(view_H)
    container_top = if window_H>view_H then Math.floor((window_H-view_H)/2) else 10
    console.log(container_top)
    @$modalViewContainer.css('margin-top', container_top)
    return false


  ### EVENT HANDLERS ###

  _setEventHandlers: () ->
    @$cancelButton.on 'click', (e) =>
      return @hide()

    @$doneButton.on 'click', (e) =>
      return false

    return false

  ### FUNCTIONS ###

  show: () =>
    console.log('show')
    @$modalView.css('display', 'block')
    @setLayout()
    console.log('display')
    @$modalView.animate {
      opacity: 1
    }, 200, @DEFAULT_EASE_TYPE, =>
      @is_shown = true
      @$modalView.trigger('show')
    $('#mainView').css({'user-select', 'none'})
    $('#mainView').css({'-webkit-user-select', 'none'})
    $('#mainView').css({'-moz-user-select', 'none'})
    $('#mainView').css({'-ms-user-select', 'none'})
    return false

  hide: () =>
    @$modalView.animate {
      opacity: 0
    }, 200, @DEFAULT_EASE_TYPE, =>
      @$modalView.css('display', 'none')
      @is_shown = false
      @$modalView.trigger('hide')
    $('#mainView').css({'user-select', 'initial'})
    $('#mainView').css({'-webkit-user-select', 'initial'})
    $('#mainView').css({'-moz-user-select', 'initial'})
    $('#mainView').css({'-ms-user-select', 'initial'})
    return false

  showAlert: (message) =>
    @$alert.html(message)
    @$alert.css({'display':'block'})
    return false

  hideAlert: () =>
    @$alert.html('')
    @$alert.css({'display': 'none'})
    return false

window.ModalView = ModalView
