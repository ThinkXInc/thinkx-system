//
// PlayQueue.js
//
// wtitten by Kazuki Otsuka

//class definition
function PlayQueue (numberOfElements,stage){
	this.playList = new Array();
	this.overEffectList = new Array();
	this.isPlaying = false;
	this.stage = stage;
	this.numberOfElements = numberOfElements;
	this.currentRowCount = 0;
	this.currentLineCount = 0;
	this.currentUsedCharNameIndexes = new Array();
	this.callback = false;
}

//play list functions
PlayQueue.prototype.addPlayList = function(motionNameString,delayInSec,numberForNext,userInfo){
	console.log([motionNameString,' added to playlist'].join(''));
	this.playList.push({motion:motionNameString,delay:delayInSec,numberForNext:numberForNext,userInfo:userInfo});
}
PlayQueue.prototype.popPlayList = function(){
	this.playList.shift();
	this.overEffectList.shift();
}
PlayQueue.prototype.playListCount = function(){
	return this.playList.length;
}
PlayQueue.prototype.currentMotionName = function(){
	return this.playList[0]['action'];
}
PlayQueue.prototype.currentMotionDelay = function(){
	return this.playList[0]['delay'];
}
PlayQueue.prototype.currentMotionsUserInfo = function(){
	return this.playList[0]['userInfo'];
}
PlayQueue.prototype.currentMotionsNumberForNext = function(){
	return this.playList[0]['numberForNext'];
}

//over effect functions
PlayQueue.prototype.addOverEffect = function(effectTypeStringsArray,insertNumbersArray,userInfo){
	for(var i=0;i<effectTypeStringsArray.length;i++){
		console.log([effectTypeStringsArray[i],' added to overEffectList'].join(''));
	}
	this.overEffectList[this.playListCount()-1] = {effectTypeList:effectTypeStringsArray,insertNumberList:insertNumbersArray,userInfo:userInfo};
}
PlayQueue.prototype.popCurrentOverEffectList = function(){
	var typeList = this.overEffectList[0]['effectTypeList'];
	this.overEffectList[0]['effectTypeList'].shift();
	this.overEffectList[0]['insertNumberList'].shift();
}
PlayQueue.prototype.currentOverEffectTypeList = function(){
	var l = this.overEffectList[0];
	return (l)? l['effectTypeList'] : null;
}
PlayQueue.prototype.currentOverEffectInsertNumberList = function(){
	var l = this.overEffectList[0];
	log(this.overEffectList);
	return (l)? l['insertNumberList'] : null;
}
PlayQueue.prototype.currentOverEffectUserInfo = function(){
	return this.overEffectList[0]['userInfo'];
}

//text matrix
PlayQueue.prototype.setCurrentRowCount = function(c){
	this.currentRowCount = c;
}
PlayQueue.prototype.setCurrentLineCount = function(c){
	this.currentLineCount = c;
}
PlayQueue.prototype.getCurrentRowCount = function(){
	return this.currentRowCount;
}
PlayQueue.prototype.getCurrentLineCount = function(){
	return this.currentLineCount;
}

//text grid
PlayQueue.prototype.getCurrentUsedCharNameIndexes = function(){
	return this.currentUsedCharNameIndexes;
}
PlayQueue.prototype.pushCurrentUsedCharNameIndex = function(index){
	this.currentUsedCharNameIndexes.push(index);
}
PlayQueue.prototype.resetCurrentUsedCharNameIndexes = function(){
	this.currentUsedCharNameIndexes = [];
}

//call back
PlayQueue.prototype.setCallback = function(callback){
	this.callback = callback;
}
PlayQueue.prototype.executeCallback = function(){
	if(this.callback){
		this.callback();
	}	
}

//reset
PlayQueue.prototype.reset = function(){
	console.log('RESET');
	var Tween = createjs.Tween;
	Tween.removeAllTweens();
	this.playList = [];
	this.overEffectList = [];
	this.currentRowCount = 0;
	this.currentLineCount = 0;
	this.currentUsedCharNameIndexes = [];
	this.callback = false;
}

//play queue
PlayQueue.prototype.play = function(){
	var nextPlayList = this.playList[0];
	log('play');
	log(this.playList);
	log(this.currentUsedCharNameIndexes);
	log(this.callback);
	
	if(nextPlayList){
		this.isPlaying = true;
		console.log(['nextPlayList',nextPlayList['motion']].join(' is ->'));
		switch(nextPlayList['motion']){
			case 'scatter':
				this.playScatterMotion();
				break;
			case 'lineup':
				this.playLineupMotion();
				break;
			case 'circle':
				this.playCircleMotion();
				break;
			case 'grid':
				this.playGridMotion();
				break;
			case 'matrixrandomalpha':
				this.playMatrixRandomAlphaMotion();
				break;
			case 'randomalpha':
				this.playRandomAlphaMotion();
				break;
			case 'textsequence':
				this.playTextSequenceMotion();
				break;
			case 'resettextsequence':
				this.resetTextSequence();
				break;
			case 'verticaltransfer':
				this.playVerticalTransferMotion();
				break;
			default:
				console.log('unknown motion');
				break;
		}
	}
	else{
		console.log('no more play list');
		this.breakMotion();
		this.executeCallback();
		this.callback = false;
	}
}
PlayQueue.prototype.playNextMotion = function(){
	console.log('play next');
	this.popPlayList();
	this.play();	
}
PlayQueue.prototype.executeOverEffect = function(){
	var overEffectType = this.currentOverEffectTypeList()[0];
	switch(overEffectType){
		case 'randomalpha':
			this.setRandomAlphaEffect();
			break;
		default:
			break;
	}
	this.popCurrentOverEffectList();
}

PlayQueue.prototype.playGodsDice = function(motionCount,norepeatmode,callback){
	var PIPS = {
		SCATTER : 0,
		GRID : 1,
		CIRCLE : 2,
		TRANSFER : 3,
		LINEUP : 4,
		MATRIX : 5,
		_SIZE : 6
	}
	var pipsList = [];
	for(i=0;i<motionCount;i++){
		var delay = Math.floor(Math.random()*1000);
		var numberForNext = Math.floor(Math.floor(this.numberOfElements/2)+Math.random()*((this.numberOfElements-1)-Math.floor(this.numberOfElements/2)));
		var interval = Math.floor(Math.random()*2);
		var duration = Math.floor(300+Math.random()*500);
		var position = Math.floor(0.1+Math.random()*1);
		var insertNumber = Math.floor(Math.random()*(this.numberOfElements-1));

		var r = Math.floor(Math.random()*PIPS._SIZE);
		if(norepeatmode && pipsList.indexOf(r) != -1){
			do{
				r = Math.floor(Math.random()*PIPS._SIZE);
			}while(pipsList.indexOf(r) != -1);
		}
		pipsList.push(r);
		switch(r){
			case PIPS.SCATTER:
				this.addPlayList('scatter',delay,numberForNext,{'interval':interval,'duration':duration});
				break;
			case PIPS.GRID:
				this.addPlayList('grid',delay,numberForNext,{'interval':interval});
				break;
			case PIPS.CIRCLE:
				this.addPlayList('circle',delay,numberForNext,{'interval':interval});
				break;
			case PIPS.TRANSFER:
				this.addPlayList('verticaltransfer',delay,numberForNext,{'position':position,'interval':interval});
				break;
			case PIPS.LINEUP:
				this.addPlayList('lineup',delay,numberForNext,null);
				break;
			case PIPS.MATRIX:
				this.addPlayList('matrixrandomalpha',delay,numberForNext,null);
				break;
			default:
				if(i!=0){
					this.addOverEffect(['randomalpha'],[insertNumber],null);
				}
				break;
		}
	}
	this.setCallback(callback);
	this.play();
}

//motions
PlayQueue.prototype.playScatterMotion = function(){ //scatter :文字を画面上にランダムに配置する
	console.log('Now playing scatter');

	var userInfo = this.currentMotionsUserInfo();
	var interval = (userInfo && userInfo['interval'])? userInfo['interval'] : 1;
	var duration = (userInfo && userInfo['duration'])? userInfo['duration'] : 1000;
	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;
	for(var i=0,n=numberOfElements;i<n;i++){
		var elem = this.stage.getChildAt(i);
		var a = 0.4+Math.random()*0.6;
		var x = SW*Math.random();
		var y = SH*Math.random();
		switch(i){
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0}, 80, createjs.Ease.circOut)
						.to({alpha:a, x:x, y:y}, duration, Ease.circOut)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0}, 80, createjs.Ease.circOut)
						.to({alpha:a, x:x, y:y}, duration, Ease.circOut);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				Tween.get(elem)
				.wait(i*interval)
				.to({alpha:0}, 80, createjs.Ease.circOut)
				.to({alpha:a, x:x, y:y}, duration, Ease.circOut);
				break;
		}
	}
}

PlayQueue.prototype.playLineupMotion = function(){ //lineup :文字を画面中央に線形に並べる
	console.log('Now playing lineup');

	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;
	for(var i=0,n=numberOfElements;i<n;i++){
		var elem = this.stage.getChildAt(i);
		switch(i){
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(i*1)
						.to({alpha:0}, 80, createjs.Ease.circOut)
						.to({alpha:1, x:0+SW*i/numberOfElements, y:SH/2}, 1000, Ease.circOut)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(i*1)
						.to({alpha:0}, 80, createjs.Ease.circOut)
						.to({alpha:1, x:0+SW*i/numberOfElements, y:SH/2}, 1000, Ease.circOut);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				Tween.get(elem)
				.wait(i*1)
				.to({alpha:0}, 80, createjs.Ease.circOut)
				.to({alpha:1, x:0+SW*i/numberOfElements, y:SH/2}, 1000, Ease.circOut);
				break;
		}
	}
}

PlayQueue.prototype.playCircleMotion = function (){
	console.log('Now playing circle');

	var userInfo = this.currentMotionsUserInfo();
	var interval = (userInfo && userInfo['interval'])? userInfo['interval'] : 5;
	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements-1;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;
	for(var i=0,n=numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		var x0 = SW/2;
		var y0 = SH/2;
		var R = SW*0.5;
		var x = x0 + (R-(i*0.8))* Math.sin(i*8 * Math.PI/180);
		var y = y0 + (R-(i*0.8))* Math.cos(i*8 * Math.PI/180);
		var threadArg = {x0:elem.x,y0:elem.y,xto:x,yto:y,index:i};
		switch(i){
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					log('last element');
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0}, 80, Ease.circOut)
						.to({alpha:1, x:x, y:y}, 1000, Ease.circOut)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0}, 80, Ease.circOut)
						.to({alpha:1, x:x, y:y}, 1000, Ease.circOut);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				Tween.get(elem)
					.wait(i*interval)
					//.call(thread,[threadArg])
					.to({alpha:0}, 80, Ease.circOut)
					.to({alpha:0.2+Math.random()*0.8, x:x, y:y}, 800, Ease.circOut);
				break;
		}
	}

	function thread(arg){
		var x0 = arg['x0'];
		var y0 = arg['y0'];
		var xto = arg['xto'];
		var yto = arg['xto'];
		var line = new createjs.Shape();
		line.name = line + arg['index'];
		line.graphics.beginStroke('#DDD');
		line.graphics.moveTo(x0,y0);
		line.graphics.lineTo(xto,yto);
		line.graphics.endStroke();
		createjs.Tween.get(line).wait(0).to({alpha:0},100).call(function(){stage.removeChild(line);});
		stage.addChild(line);
	}
}

PlayQueue.prototype.playGridMotion = function(){ //grid : 文字を画面全体にアルファベット順に並べる
	console.log('Now playing text grid');

	var userInfo = this.currentMotionsUserInfo();
	var interval = (userInfo && userInfo['interval'])? userInfo['interval'] : 0;
	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;

	var toppd = 10; //top padding
	var sidepd = 10; //side padding
	var w = 30; //grid width
	var rowc = this.rowCountWithSidePaddingAndGridWidth(sidepd,w); //number of objects in a row 
	var linec = this.lineCountWithRowCount(rowc); //number of objects in a line
	var h = this.gridHeightWithRowCount(rowc); //grid height
	this.setCurrentRowCount(rowc);
	this.setCurrentLineCount(linec);

	for(var i=0,n=numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		switch(i){
			case 0: //first
				Tween.get(elem)
				.wait(i*interval)
				.to({alpha:0.2, x:sidepd, y:toppd,rotation:1}, 300, Ease.linear);
				break;
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0.2, x:sidepd+w*i-(Math.floor(i/rowc)*rowc*w), y:toppd+Math.floor(i/rowc)*h,rotation:1}, 300, Ease.linear)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0.2, x:sidepd+w*i-(Math.floor(i/rowc)*rowc*w), y:toppd+Math.floor(i/rowc)*h,rotation:1}, 300, Ease.linear);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default: 
				Tween.get(elem)
					.wait(i*interval)
					.to({alpha:0.2, x:sidepd+w*i-(Math.floor(i/rowc)*rowc*w), y:toppd+Math.floor(i/rowc)*h,rotation:1}, 300, Ease.linear);
				break;
		}
	}
}

PlayQueue.prototype.playMatrixRandomAlphaMotion = function(){ //matrixrandomalpha : alphaを縦方向に1文字ずつランダムにセットする
	console.log('Now playing MatrixRandomAlpha');

	var rowc = this.getCurrentRowCount();
	var linec = this.getCurrentLineCount();
	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var cniused = this.getCurrentUsedCharNameIndexes();
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;

	if(rowc == 0){
		this.playNextMotion();
		return;
	}

	for(var i=0,n=numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		var r = i%rowc;
		var l = Math.floor(i/rowc);
		var ans = String(r * Math.PI/180);
		ans = ans.substring(ans.length-2,ans.length-1);
		ans = parseFloat("0."+ans);
		var delay = ans * 3000;
		var interval = 40 + ans * 60;
		switch(i){
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(interval*l)
						.to({alpha:0.1},10,Ease.linear)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(interval*l)
						.to({alpha:0.1},10,Ease.linear);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				if(r%2==0 && (cniused.indexOf(i) == -1)){
					Tween.get(elem)
						.wait(delay+(interval*l))
						.to({alpha:0.4+Math.random()*0.6}, 10, Ease.linear)
				}else{
					Tween.get(elem)
						.wait(interval*l)
						.to({alpha:0.1},10,Ease.linear);
			}
		}
	}
}

PlayQueue.prototype.playRandomAlphaMotion = function(){ //randomalpha : alphaを1文字ずつランダムに次々セットする
	console.log('Now playing RandomAlpha');

	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var userInfo = this.currentMotionsUserInfo();
	var minOpacity = (userInfo && userInfo['minOpacitiy'])? userInfo['minOpacity'] : 0.3; 
	var maxOpacity = (userInfo && userInfo['maxOpacity'])? userInfo['maxOpacity'] : 1.0;
	var interval = (userInfo && userInfo['interval'])? userInfo['interval'] : 10;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;

	for(var i=0,n=this.numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		switch(i){
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut)
						.wait(500)
						.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut)
						.wait(500)
						.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				Tween.get(elem)
					.wait(i*10)
					.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut)
					.wait(500)
					.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut);
		}
	}
}


PlayQueue.prototype.playVerticalTransferMotion = function(){
	console.log('Now playing VerticalTransfer');

	var userInfo = this.currentMotionsUserInfo();
	var horizontalPosition = (userInfo['position'])? userInfo['position'] : -0.1;
	var interval = (userInfo && userInfo['interval'])? userInfo['interval'] : 10;
	var delay = (userInfo && userInfo['delay'])? userInfo['delay'] : 4000;
	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;

	for(var i=0,n=this.numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		switch(i){
			case numberForNext:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(i*interval)
						.to({y:SH*horizontalPosition}, delay, Ease.circOut)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
						.wait(i*interval)
						.to({y:SH*horizontalPosition}, delay, Ease.circOut);
				}
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				Tween.get(elem)
					.wait(i*interval)
					.to({y:SH*horizontalPosition}, delay, Ease.circOut);
		}
	}
}

PlayQueue.prototype.playTextSequenceMotion = function(){
	console.log('Now playing text sequence');

	var userInfo = this.currentMotionsUserInfo();
	var displayText = userInfo['text'];
	var interval = (userInfo['interval'])? userInfo['interval'] : 10;

	log('interval'+interval);
	var delayForNextMotion = (this.currentMotionDelay() === null)? false : this.currentMotionDelay();
	var numberOfElements = this.numberOfElements;
	var numberForNext = (this.currentMotionsNumberForNext()) ? this.currentMotionsNumberForNext() : numberOfElements-1;
	var overEffectInsertNumberList = (this.currentOverEffectInsertNumberList()) ? this.currentOverEffectInsertNumberList() : [numberOfElements+1];
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;

	var sidepd = (userInfo['sidepd'])? userInfo['sidepd'] : 150;
	var toppd = (userInfo['toppd'])? userInfo['toppd'] : 70;
	var w = 17; //char object width
	var h = 30; //char object height
	var rowc = this.rowCountWithSidePaddingAndGridWidth(sidepd,w); // number of objects in a row
	var shift = 0;
	for(var i=0,n=this.numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		Tween.get(elem).to({alpha:0.1}, 500, Ease.circOut);
	}
	for(var i=0,len=displayText.length;i<len;i++){
		var cname = this.charToCname(displayText[i]);
		var index = this.cnameToArrIndex(cname);
		if(index == -1){ //return
			shift += rowc - ((i+shift)%rowc) -1;
		}
		if((i+shift)%rowc == 0 && cname == 'space'){ //space in first row
			shift -= 1;
		}
		var elem = stage.getChildAt(index);
		if(elem){
		switch(i){
			case len-1:
				if(delayForNextMotion !== false){
					var playQueuePlayNextMotion = this.playNextMotion.bind(this);
					Tween.get(elem)
						.wait(i*interval)
						.to({alpha:0}, 80, Ease.circOut)
						.to({alpha:1, x:sidepd+w*(i+shift)-(Math.floor((i+shift)/rowc)*rowc*w), y:toppd+Math.floor((i+shift)/rowc)*h, rotation:1}, 1000, Ease.circOut)
						.wait(delayForNextMotion)
						.call(playQueuePlayNextMotion);
				}
				else{
					console.log('no motion to wait and stop');
					Tween.get(elem)
					.wait(i*interval)
					.to({alpha:0}, 80, Ease.circOut)
					.to({alpha:1, x:sidepd+w*(i+shift)-(Math.floor((i+shift)/rowc)*rowc*w), y:toppd+Math.floor((i+shift)/rowc)*h, rotation:1}, 1000, Ease.circOut)
				}
				break;
			case N-1:
				Tween.get(elem)
					.wait(i*interval)
					.to({alpha:0}, 80, Ease.circOut)
					.to({alpha:1, x:sidepd+w*(i+shift)-(Math.floor((i+shift)/rowc)*rowc*w), y:toppd+Math.floor((i+shift)/rowc)*h, rotation:1}, 1000, Ease.circOut)
					.wait(delayForNextMotion)
					.call(playQueuePlayNextMotion);
				break;
			case overEffectInsertNumberList[0]:
				this.executeOverEffect();
				break;
			default:
				Tween.get(elem)
					.wait(i*interval)
					.to({alpha:0}, 80, Ease.circOut)
					.to({alpha:1, x:sidepd+w*(i+shift)-(Math.floor((i+shift)/rowc)*rowc*w), y:toppd+Math.floor((i+shift)/rowc)*h, rotation:1}, 1000, Ease.circOut)
					.wait(0);
				break;
		}
		}
	}
}

PlayQueue.prototype.resetTextSequence = function(){
	console.log('Now playing reset text sequence');
	this.resetCurrentUsedCharNameIndexes();
	this.playNextMotion();
}

PlayQueue.prototype.breakMotion = function(){ //break (catch gravity) : 動的な剛体の位置をbmpに合わせて重力作用をONに
	console.log('Break Motion');
	this.isPlaying = true;
	var b = world.GetBodyList();
	var Math = Box2D.Common.Math;
	while(b){
		var bmp = b.GetUserData();
		if(bmp){
			var v = new Math.b2Vec2(bmp.x*SCALE,bmp.y*SCALE);
			var r = new Math.b2Mat22.FromAngle(bmp.rotation*createjs.Matrix2D.DEG_TO_RAD);
			var t = new Math.b2Transform(v,r);
			b.SetTransform(t);
		}
		b = b.GetNext();
	}
	this.isPlaying = false;
}

//effects
PlayQueue.prototype.setRandomAlphaEffect = function(){ //randomalpha (over effect)
	console.log("setrandomAlpha start");
	var userInfo = this.currentOverEffectUserInfo();
	var minOpacity = (userInfo && userInfo['minOpacitiy'])? userInfo['minOpacity'] : 0.3; 
	var maxOpacity = (userInfo && userInfo['maxOpacity'])? userInfo['maxOpacity'] : 1.0;
	var interval = (userInfo && userInfo['interval'])? userInfo['interval'] : 10;
	var Tween = createjs.Tween;
	var Ease = createjs.Ease;
	for(var i=0,n=this.numberOfElements;i<n;i++){
		var elem = stage.getChildAt(i);
		Tween.get(elem)
			.wait(interval*10)
			.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut)
			.wait(500)
			.to({alpha:minOpacity+Math.random()*(maxOpacity-minOpacity)},500,Ease.circOut);
	}
}


/***
 * calculates matrix size *
 					    ***/

PlayQueue.prototype.rowCountWithSidePaddingAndGridWidth = function(sidepd,w){
	var rowsize = Math.floor((SW-(sidepd*2))/w); //1行あたりの文字数
	rowsize = (rowsize < 40)? 40 : rowsize;
	return rowsize;
}	

PlayQueue.prototype.lineCountWithRowCount = function(rowc){
	return Math.ceil(this.numberOfElements/rowc);
}

PlayQueue.prototype.gridHeightWithRowCount = function(rowc){
	return Math.floor(SH/(Math.ceil(this.numberOfElements/rowc)))
}

/***
 * Charactors & Indexes *
 					  ***/

PlayQueue.prototype.cnameToChar = function(c_){ //文字符号から文字へ
	var c; 
	if(c_.indexOf("_") != -1){
		//_が含まれる
		c = c_.replace(/_/,'');
		//console.log(c_+'→'+c);
	}else if(c_.indexOf("dot") != -1){
		c = '.';
		//console.log(c);
	}else if(c_.indexOf("comma") != -1){
		c = ',';
		//console.log(c);
	}else if(c_.indexOf("space") != -1){
		c = ' ';
		//console.log(c);
	}else if(c_.indexOf("quest") != -1){
		c = '?';
		//console.log(c);
	}else if(c_.indexOf("quot") != -1){
		c = '\'';
		//console.log(c);
	}else if(c_.indexOf("dquot") != -1){
		c = '"';
		//console.log(c);
	}else if(c_.indexOf("colon") != -1){
		c = ':';
		//console.log(c);
	}else if(c_.indexOf("at") != -1){
		c = '@';
		//console.log(c);
	}else if(c_.indexOf("percent") != -1){
		c = '%';
		//console.log(c);
	}else if(c_.indexOf("lbrace") != -1){
		c = '{';
		//console.log(c);
	}else if(c_.indexOf("rbrace") != -1){
		c = '}';
		//console.log(c);
	}else if(c_.indexOf("lparent") != -1){
		c = '(';
		//console.log(c);
	}else if(c_.indexOf("rparent") != -1){
		c = ')';
		//console.log(c);
	}else if(c_.indexOf("hyphen") != -1){
		c = '-';
		//console.log(c);
	}else if(c_.indexOf("and") != -1){
		c = 'and';
		//console.log(c);
	}else if(c_.indexOf("exclam") != -1){
		c = '!';
		//console.log(c);
	}else if(c_.indexOf("tild") != -1){
		c = '~';
		//console.log(c);
	}else if(c_.indexOf("return") != -1){
		c = '\n';
		//console.log(c);
	}else{
		c = c_;
		//console.log(c);
	}
	return c;
}

PlayQueue.prototype.charToCname = function(c){ //文字から文字符号へ
	var c_;
	if(c.match(/[a-z]/)){
		//console.log('lower case'+'_' + c);
		return '_' + c;
	}else if(c.match(/[A-Z]/)){
		//console.log('upper case '+c);
		return c;
	}else if(c.match(/[0-9]/)){
		return c;
	}else if(c == '@'){
		return 'at';
	}else if(c == '%'){
		return 'percent';
	}else if(c == '!'){
		return 'exclam';
	}else if(c == '-'){
		return 'hyphen';
	}else if(c == '~'){
		return 'tild';
	}else if(c == '&'){
		return 'and';
	}else if(c == ' '){
		return 'space';
	}else if(c == '.'){
		return 'dot';
	}else if(c == ','){
		return 'comma';
	}else if(c == ':'){
		return 'colon';
	}else if(c == '?'){
		return 'quest';
	}else if(c == '{'){
		return 'lbrace';
	}else if(c == '}'){
		return 'rbrace';
	}else if(c == ')'){
		return 'rparent';
	}else if(c == '('){
		return 'lparent';
	}else if(c == '\''){
		return 'quot';
	}else if(c == '\"'){
		return 'dquot';
	}else if(c == '\n'){
		return 'return';
	}
}

PlayQueue.prototype.cnameToArrIndex = function(c){ //文字符号から要素インデックスを取得 (spaceか適用可能なエレメントが無い場合、エレメント数+1を返す)
	var index = 0;
	var cniused = this.getCurrentUsedCharNameIndexes();
	//console.log('search index by '+c);
	if(c == 'return'){
		return -1;
	}
	for(var i=0,len=cnames.length;i<len;i++){
		if(cnames[i] == c){
			index = i;
			//console.log('indexused indexOf ' + (cniused.indexOf(index)));
			do{
				index = index + cnames.length;
				//console.log(index);
				if(index > this.numberOfElements)break;
			}while(cniused.indexOf(index) != -1);

			if(index > 0 && index < this.numberOfElements){
				//console.log('index found '+index);
				cniused.push(index);
				//console.log(cniused);
				return index;
			}
		}
	}
	//console.log('index not found '+index);
	this.pushCurrentUsedCharNameIndex(index);
	//console.log(cniused);
	return index;
}






//文字要素を全て画面中央に並べる
function tocenter(arg){
	console.log("tocenter");
	//if(arg['index'] == N-1){
		for(var i=0;i<N;i++){
			//var arg = {index:i};
			var elem = stage.getChildAt(i);
			createjs.Tween.get(elem)
					.wait(i*1)
					.to({alpha:0}, 80, createjs.Ease.circOut)
					.to({alpha:1, x:150+30*i-(Math.floor(i/40)*40*30), y:80+Math.floor(i/40)*40}, 1000, createjs.Ease.circOut);
					//.call(todown,[arg]);
		}
	//}
}

//文字要素を全て画面下に並べる
function todown(arg){
	console.log("todown");
	//if(arg['index'] == N-1){
		console.log("comp fin");
		for(var i=0;i<N;i++){
			//var arg = {index:i};
			var elem = stage.getChildAt(i);
			createjs.Tween.get(elem)
					.wait(i*1)
					.to({alpha:0}, 80, createjs.Ease.circOut)
					.to({alpha:1, x:0+SW*i/N, y:SH}, 1000, createjs.Ease.circOut);
					//.call(fin2,[arg]);
		}
	//}
}


