/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// flashtext.coffee
//
// <div id="element_id">
//   <p data-parts="display"><span data-parts="cursor"></p>
//   <ul data-parts="textList">
//     <li>Flash text number 1</li>
//     <li>Flash text number 2</li>
//     ...
//   </ul>
// </div>

class FlashText {

  constructor(element_id) {
    this.setEventHandlers = this.setEventHandlers.bind(this);
    this.start = this.start.bind(this);
    this.flashIn = this.flashIn.bind(this);
    this.flashOut = this.flashOut.bind(this);
    this.blinkCursor = this.blinkCursor.bind(this);
    this.init(element_id);
  }

  init(element_id) {
    this.$flashText = $(element_id);
    this.$display = $('[data-parts=display]', this.$flashText);
    this.$textList = $('[data-parts=textList]', this.$flashText);
    this.$cursor = $('[data-parts=cursor]', this.$flashText);
    console.log(this.$flashText);
    console.log(this.$textList);
    this.texts = this.$textList.find('li').html();
    console.log(this.$textList.find('li').html());
    this.texts.append(this.$textList.find('li').html());
    this.end = false;
    return false;
  }

  setEventHandlers(){
    this.$flashText.on('completeFlashIn', (e, data)=> {
      const index = data['index'];
      this.flashOut(index);
      return false;
    });

    this.$flashText.on('completeFlashOut', (e, data)=> {
      let index = data['index'];
      if (index = this.texts.length-1) {
        // finished
        this.end = true;
        this.$flashText.trigger('finished', {});
      } else {
        index = index+1;
        this.flashIn(index);
      }
      return false;
    });

    return false;
  }


  start(){
    this.flashIn(0);
    return false;
  }

  flashIn(index){
    const text = this.texts[index];
    let chars = '';
    const interval = 100;
    const remain = 1000;
    for (let c of Array.from(text)) {
      chars += c;
      setTimeout(function() {
        return this.$display.html(chars);
      }
      , interval);
    }
    setTimeout(function() {
      return this.flashText.trigger('completeFlashIn', {'index': index});
    }
    , (text.length*interval)+remain);
    return false;
  }

  flashOut(index){
    this.$display.addClass('flashOut');
    const duration = 1000;
    setTimeout(function() {
      this.$display.html('');
      this.$display.removeClass('flashOut');
      return this.flashText.trigger('completeFlashOut', {'index': index});
    }
    , 1000);
    return false;
  }

  blinkCursor(){
    let t;
    return t = setInterval(function(){
      if (this.$cursor.hasClass('blinkin')) {
        this.$cursor.removeClass('blinkin');
      } else {
        this.$cursor.addClass('blinkin');
      }
      if (this.end === true) {
        return clearInterval(t);
      }
    }
    , 200);
  }
}

window.FlashText = FlashText;
