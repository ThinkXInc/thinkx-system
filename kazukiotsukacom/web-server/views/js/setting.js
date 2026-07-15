/**
 * This program is for setting canvas
 */
const $top = document.getElementById('top');
const $canvas = document.getElementById('canvas');
const $bio = document.getElementById("bio");
const $menu = document.getElementById("ms");
const MOBILE_WIDTH = 480; 
var SW = $(window).width();
var SH = $(window).height();
let isMobile = SW < MOBILE_WIDTH;
let isProductsShown = false;

let timer = false;

/** View events & lifecycle */

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
	resetIsMobile();
});


$(document).ready(function() {
	console.log('start settings')

    document.body.classList.add('show');
	// ***
    //$('.logo').delay(700).animate({
    //     'opacity' : '1',        
    //     'top' : '+=50px'
    //}, { duration: 700, easing: 'swing' });

    //$('#title').delay(1000).animate({
    //     'opacity' : '1',
    //     'top' : '+=30px'
    //}, { duration: 700, easing: 'easeOutSine' });
	// ***
   
	setPosition();
	showMenu();
	showCopyRight();

	let url = new URL(window.location.href);
  	let page = url.searchParams.get('page');
  	if (page === 'bio') {
  	  showBio();
	  if (isMobile) {toggleMenu(false)};
	  //toggleMenu(false);
  	} else if (page === 'contact') {
  	  showContact();
  	} else {
  	  // Default: show home
  	  showHome();
  	}

	resetIsMobile();
});

// ***
document.addEventListener('introFinished', (e)=> {
    console.log('received: introFinished')
})
// ***


/** Setup elements */

function showMenu(){
	console.log('show menu');
	var $ms = $("#ms");
	log($ms);
	$ms.show();
	$ms.animate({
		opacity:1
	},1000,'linear',null);
	if (shuffle) {
		shuffleAllMenu(40, 50);
	}
}

function showCopyRight() {
	var $copyright = $("#copyright");
	$copyright.show();
	$copyright.animate({
		opacity:1
	},1000,'linear',function(){
		//isMenuShown = true; // **
	});
}


/** Views **/

function closeAllViews() {
	// hide pages
	$bio.style.display = 'none';

	// show canvas
	let $c = $("#canvas");
	$c.animate({
		opacity:1
	},1000,'linear',function(){
		//isMenuShown = true; // **
	});
}

function toggleMenu(expand) {
	console.log('toggle menu ', expand)
	if (expand) {
		$menu.classList.add('expand')
		$menu.classList.remove('hide')
	} else {
		$menu.classList.remove('expand')
		$menu.classList.add('hide')
	}
}

function showHome() {
	console.log('show home');
	closeAllViews();
	if(isMobile){toggleMenu(true);}
	updateUrl(null);
}

function showBio() {
	console.log('show bio');
	closeAllViews();
	if(isMobile){toggleMenu(false);}
    $bio.style.display = 'flex';

	var $elem = $("#canvas");
	$elem.animate({
		opacity:0
	},1000,'linear',function(){
		//$canvas.style.opacity = '0';
		//isMenuShown = true; // **
	});
	updateUrl('bio');
}

function showBlog() {
	console.log('show blog');
	closeAllViews();
    window.open("https://kazukiotsuka.org", "_blank");
	updateUrl('blog');
}

function showContact() {
	console.log('show contact');
	closeAllViews();
	updateUrl('contact');
}

function justPlay() {
	console.log('just play selected');
	closeAllViews();
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

/** Set position */

function setPosition(){
	console.log('setPosition');
	console.log('SCREEN W='+SW);
	console.log('SCREEN H='+SH);

	setHeight(SH);

	if(SW > 600 && shuffle){
		shuffleAllMenu(30);
	}

	// <div class=toptexts>
	setLeftCenter($("#toptexts"));
	setTopCenter($("#toptexts"), -0);


	setMenuPosition();
	setCopyrightPosition();
	$('#products').css({top:60,left:140,width:SW-200,height:SH-40});
}

function setHeight(height) {
	console.log('set height ', height)
	$top.style.height = height + 'px';
	$canvas.style.height = height + 'px';
}

function setLeftCenter($elem) {
	console.log(SW/2 - $elem.width()/2)
	$elem.css({left: SW/2 - $elem.width()/2})
}

function setTopCenter($elem, plus=0) {
	console.log(SH/2 - $elem.height()/2 + plus)
	$elem.css({top: SH/2 - $elem.height()/2 + plus})
}

function setMenuPosition() {
	$('#ms').css({top:menuTop,left:menuLeft});
}

function setCopyrightPosition(){
	//if(isProductsShown){
	//	$('#copyright').css({top:document.body.scrollHeight + 20,left:20});
	//}
	//else{
	//	$('#copyright').css({bottom:copyrightBottom,left:copyrightLeft});
	//}
}

/** Shuffle menu */

function shuffleAllMenu(delay, interval=20){
	console.log('suffle all menu')
	var ml = $("#ms *").length;
	var i = 1;
	var n;
	var seq = setInterval(function(){
		$('#m'+i).shuffleEffect(interval,'#mt'+i);
		i++;
		if(i==ml+1){
			clearInterval(seq);
			isMenuShown = true; // **
			return;
		}
	},delay);
}

if (shuffle) {
(function (){
	var ml = $("#ms *").length;
	for(var i=1;i<ml+1;i++){
		var n = (ml+1-i);
		//console.log('set n='+n);
		const id = "#m"+n;
		$(id).bind("mouseover",
			function(){
				//console.log("#"+$(this).attr("id").replace("m","mt_"));
				$(this).shuffleEffect(shuffleSpeed,"#"+$(this).attr("id").replace("m","mt_"));
				//console.log('over n='+n);
			}
		);
		$(id).bind("mouseout",
			function(){
				//console.log("#"+$(this).attr("id").replace("m","mt"));
				$(this).shuffleEffect(shuffleSpeed,"#"+$(this).attr("id").replace("m","mt"));
			}
		);
	}
})();
}

/** Helpers **/
function updateUrl(pageName) {
  // Parse current URL's query string
  let url = new URL(window.location.href);
  let params = url.searchParams;

  if (pageName) {
    // Set 'page' to the given pageName
    params.set('page', pageName);
  } else {
    // Remove 'page' parameter completely
    params.delete('page');
  }

  // Update the URL without reloading the page
  url.search = params.toString();
  history.replaceState({}, '', url.toString());
}

function resetIsMobile() {
	if (SW < MOBILE_WIDTH) {
		isMobile = true;
	} else {
		isMobile = false;
	}
}