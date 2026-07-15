var SW = $(window).width();
var SH = $(window).height();
var isProductsShown = false;

var timer = false;
$(window).resize(function(){
	if(timer != false){
		clearTimeout(timer);
	}
	timer = setTimeout(function(){
		SW = $(window).width();
		SH = $(window).height();
		console.log('resized');
		setPosition();
	}, 200);
});


$(document).ready(function() {
    $('.logo').delay(700).animate({
         'opacity' : '1',        
         'top' : '+=50px'
    }, { duration: 700, easing: 'swing' });

    $('#title').delay(1000).animate({
         'opacity' : '1',
         'top' : '+=30px'
    }, { duration: 700, easing: 'easeOutSine' });
   
	setPosition();
});

function setPosition(){

	console.log('setPosition');
	console.log('SCREEN W='+SW);
	console.log('SCREEN H='+SH);

	if(SW > 600){
		shuffleAllMenu(30);
	}

	setCopyrightPosition();
	$('#products').css({top:60,left:140,width:SW-200,height:SH-40});
}

function setCopyrightPosition(){
	
	if(isProductsShown){
		$('#copyright').css({top:document.body.scrollHeight + 20,left:20});
	}
	else{
		$('#copyright').css({top:SH-40,left:20});
	}
}

function shuffleAllMenu(delay){
	var ml = $("#ms *").length;
	var i = 1;
	var n;
	var seq = setInterval(function(){
		$('#m'+i).shuffleEffect(20,'#mt'+i);
		i++;
		if(i==ml+1){
			clearInterval(seq);
			return;
		}
	},delay);
}

(function (){
	var ml = $("#ms *").length;
	for(var i=1;i<ml+1;i++){
		var n = (ml+1-i);
		//console.log('set n='+n);
		$("#m"+n).bind("mouseover",
			function(){
				//console.log("#"+$(this).attr("id").replace("m","mt_"));
				$(this).shuffleEffect(20,"#"+$(this).attr("id").replace("m","mt_"));
				//console.log('over n='+n);
			}
		);
		$("#m"+n).bind("mouseout",
			function(){
				//console.log("#"+$(this).attr("id").replace("m","mt"));
				$(this).shuffleEffect(20,"#"+$(this).attr("id").replace("m","mt"));
			}
		);
	}
})();

function showMenu(){
	console.log('show menu');
	var $ms = $("#ms");
	log($ms);
	$ms.show();
	$ms.animate({
		opacity:1
	},1000,'linear',null);
	shuffleAllMenu(100);
	var $copyright = $("#copyright");
	$copyright.show();
	$copyright.animate({
		opacity:1
	},1000,'linear',function(){
		isMenuShown = true;
	});
}

function showProducts(){
	console.log('show products');
	var $products = $('#products');
	var $copyright = $('#copyright');
	$products.show();
	$products.animate({
         'opacity' : '1'
    }, { duration: 1700, easing: 'easeOutSine' , complete: setCopyrightPosition});
	isProductsShown = true;
}

function hideProducts(){
	if(isProductsShown){
		console.log('hide products');
		var $products = $('#products');
		$products.animate({
        	 'opacity' : '0'
    	}, { duration: 1000, easing: 'easeOutSine', complete: function(){$products.hide(); isProductsShown = false; setCopyrightPosition();}});
	}
}
