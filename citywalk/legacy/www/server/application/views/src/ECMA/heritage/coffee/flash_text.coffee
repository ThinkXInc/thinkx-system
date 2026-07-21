# flashtext.coffee
#
# <div id="element_id">
#   <p data-parts="display"><span data-parts="cursor"></p>
#   <ul data-parts="textList">
#     <li>Flash text number 1</li>
#     <li>Flash text number 2</li>
#     ...
#   </ul>
# </div>

class FlashText

  constructor: (element_id) ->
    @init(element_id)

  init: (element_id) ->
    @$flashText = $(element_id)
    @$display = $('[data-parts=display]', @$flashText)
    @$textList = $('[data-parts=textList]', @$flashText)
    @$cursor = $('[data-parts=cursor]', @$flashText)
    console.log(@$flashText)
    console.log(@$textList)
    @texts = @$textList.find('li').html()
    console.log(@$textList.find('li').html())
    @texts.append(@$textList.find('li').html())
    @end = false
    return false

  setEventHandlers: ()=>
    @$flashText.on 'completeFlashIn', (e, data)=>
      index = data['index']
      @flashOut(index)
      return false

    @$flashText.on 'completeFlashOut', (e, data)=>
      index = data['index']
      if index = @texts.length-1
        # finished
        @end = true
        @$flashText.trigger('finished', {})
      else
        index = index+1
        @flashIn(index)
      return false

    return false


  start: ()=>
    @flashIn(0)
    return false

  flashIn: (index)=>
    text = @texts[index]
    chars = ''
    interval = 100
    remain = 1000
    for c in text
      chars += c
      setTimeout ->
        @$display.html(chars)
      , interval
    setTimeout ->
      @flashText.trigger('completeFlashIn', {'index': index})
    , (text.length*interval)+remain
    return false

  flashOut: (index)=>
    @$display.addClass('flashOut')
    duration = 1000
    setTimeout ->
      @$display.html('')
      @$display.removeClass('flashOut')
      @flashText.trigger('completeFlashOut', {'index': index})
    , 1000
    return false

  blinkCursor: ()=>
    t = setInterval ()->
      if @$cursor.hasClass('blinkin')
        @$cursor.removeClass('blinkin')
      else
        @$cursor.addClass('blinkin')
      if @end == true
        clearInterval(t)
    , 200

window.FlashText = FlashText
