/* JavaScript Document */

jQuery.fn.extend({

	shuffleEffect: function(duration,target,callback) {

		if(duration == null) duration = 50;
		var arrLetter = [/*"A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",*/ "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "=", "=", "=", "=", "__", "__", "____", "_____", "___", "___", "__", "__", "____", "_____", "___", "___", "{", "}", ";", ":", "!", "$", "%", "(", "&", ")", "+", "'"];
		var $this = jQuery(this);
		var targetStr = $(target).text();//$this.text();
		var targetN = targetStr.length - 1;
		var i = 0;
		var displayedTStr = "";
		var tid = setInterval(function() {
			if(i < targetN+1){
				var strShuffle = "";
				for(var j=0; j<targetN-i; j++){
					strShuffle += arrLetter[Math.floor(Math.random() * arrLetter.length)];
				}
				displayedTStr += targetStr.charAt(i);
				$this.css({display:"block"}).text(displayedTStr + strShuffle);
				i++;
			} else {
				clearInterval(tid);
				if(callback){
					callback();
				}
			}
		}, duration);

	}

});
