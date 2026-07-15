/*@cc_on _d=document;eval('var document=_d')@*/

var SW = $(window).width();
var SH = $(window).height();
var SCALE = 1/30; //1px=30m

var log = function(a){console.log(a)};

var canvas; //canvas element
var context; //2d context of the canvas
var stage; //createjs stage
var world; //box2d world

var cnames = [
				'A','B','C','D','E','F',
				'G','H','I','J','K','L',
				'M','N','O','P','Q','R',
				'S','T','T','T','U','V','W','X',
				'Y','Z','_a','_a','_a','_a','_b','_c','_c','_d','_d','_d',
				'_e','_e','_e','_e','_e','_e','_e','_f','_f','_g','_h','_h','_i','_i','_i','_i','_i','_j',
				'_k','_l','_l','_l','_m','_n','_n','_n','_n','_n','_n','_n','_o','_o','_o','_o','_p','_p','_p','_p',
				'_q','_r','_r','_s','_s','_s','_t','_t','_t','_t','_t','_u','_v',
				'_w','_w','_x','_y','_y','_y','_z','0','1',
				'2','3','4','5','6','7',
				'8','9','space','quest','dot','quot','dquot','comma','colon','colon','and',
				'at','exclam','percent','tild','hyphen','hyphen','hyphen','hyphen',
				'lparent','rparent','rbrace','lbrace'
			];

var indexfall = 0;
var playQueue;
var isMenuShown = false;

function tick(event){
	stage.update();
}

function initCanvas() {
	var $canvas = $('#canvas');
	$canvas.attr("width",SW);
	$canvas.attr("height",SH);
	canvas = document.getElementById('canvas');
	context = canvas.getContext("2d");
	stage = new createjs.Stage(canvas);
	createjs.Ticker.setFPS(FPS);
	createjs.MotionGuidePlugin.install(createjs.Tween);
	createjs.Ticker.addEventListener("tick",update);
	playQueue = new PlayQueue(N,stage);

	var   b2Vec2 = Box2D.Common.Math.b2Vec2
	,  b2AABB = Box2D.Collision.b2AABB
	,	b2BodyDef = Box2D.Dynamics.b2BodyDef
	,	b2Body = Box2D.Dynamics.b2Body
	,	b2FixtureDef = Box2D.Dynamics.b2FixtureDef
	,	b2Fixture = Box2D.Dynamics.b2Fixture
	,	b2World = Box2D.Dynamics.b2World
	,	b2MassData = Box2D.Collision.Shapes.b2MassData
	,	b2PolygonShape = Box2D.Collision.Shapes.b2PolygonShape
	,	b2CircleShape = Box2D.Collision.Shapes.b2CircleShape
	,	b2DebugDraw = Box2D.Dynamics.b2DebugDraw
	,  b2MouseJointDef =  Box2D.Dynamics.Joints.b2MouseJointDef
	;
   
	world = new b2World(
         new b2Vec2(0, gravity)  //gravity
      ,  true                 //allow sleep
	);
   
	var fixDef_floor = new b2FixtureDef; //物理的な性質を決めるフィクスチャの定義
	fixDef_floor.density = density_floor; //密度
	fixDef_floor.friction = friction_floor; //摩擦
	fixDef_floor.restitution = restitution_floor; //弾性
   
	var bodyDef = new b2BodyDef;
   
	//create ground 
	bodyDef.type = b2Body.b2_staticBody; //静的な剛体
	fixDef_floor.shape = new b2PolygonShape; 
	//横
	fixDef_floor.shape.SetAsBox(SW*SCALE, 2*SCALE);
	bodyDef.position.Set(0,  (SH-(SH*floorInset))*SCALE);
	world.CreateBody(bodyDef).CreateFixture(fixDef_floor);
//   //縦
//   fixDef.shape.SetAsBox(2, 14);
//   bodyDef.position.Set(-1.8, 13);
//   world.CreateBody(bodyDef).CreateFixture(fixDef);
//   bodyDef.position.Set(21.8, 13);
//   world.CreateBody(bodyDef).CreateFixture(fixDef);
   
	var fixDef_object = new b2FixtureDef; //物理的な性質を決めるフィクスチャの定義
	fixDef_object.density = density_object; //密度
	fixDef_object.friction = friction_object; //摩擦
	fixDef_object.restitution = restitution_object; //弾性

	//create some objects
	bodyDef.type = b2Body.b2_dynamicBody; //動的な剛体
	for(var i = 0; i < N; ++i) {
		fixDef_object.shape = new b2PolygonShape;
		fixDef_object.shape.SetAsBox(
               7.5*0.5*SCALE //half width
            ,  10*0.5*SCALE //half height
		);
//         fixDef.shape = new b2CircleShape(
//            Math.random() + 0.1 //radius
//         );
		bodyDef.position.x = Math.random() * SW*SCALE;
		bodyDef.position.y = Math.random() * SH*SCALE;
		
		var c = i - Math.floor(i/cnames.length)*cnames.length;
		var bmp = new createjs.Bitmap(['img/char/',cnames[c],'.png'].join(''));
		bmp.x = 0;
		bmp.y = 0;
		bmp.scaleX = 0.5;
		bmp.scaleY = 0.5;
		bmp.regX = 30*0.5*0.5;
		bmp.regY = 40*0.5*0.5;
		bmp.alpha = Math.random()*1.0;
		bmp.name = cnames[c]+i;
		bmp.index = i;
		stage.addChild(bmp);

//	  createjs.Tween.get(bmp)
//				.wait(0)
//				.to({alpha:1, x:_left+logx+40, y:_left+logy, scaleX:0.75}, 3000, createjs.Ease.circOut)
//				.to({alpha:0, scaleX:0.65}, 800, createjs.Ease.circOut)
//				.call(intro2);

		bodyDef.userData = bmp;
		world.CreateBody(bodyDef).CreateFixture(fixDef_object);
	}
   
	//setup debug draw
	var debugDraw = new b2DebugDraw();
	debugDraw.SetSprite(document.getElementById("canvas").getContext("2d"));
	debugDraw.SetDrawScale(30.0); //1mを30pxにする
	debugDraw.SetFillAlpha(0.5);
	debugDraw.SetLineThickness(1.0);
	debugDraw.SetFlags(b2DebugDraw.e_shapeBit | b2DebugDraw.e_jointBit);
	world.SetDebugDraw(debugDraw);
   
	//window.setInterval(update, 1000 / 60);
   
	//mouse
   
	var mouseX, mouseY, mousePVec, isMouseDown, selectedBody, mouseJoint;
	var canvasPosition = getElementPosition(document.getElementById("canvas"));
   
	document.addEventListener("mousedown", function(e) {
		isMouseDown = true;
		handleMouseMove(e);
		document.addEventListener("mousemove", handleMouseMove, true);
		if(playQueue.isPlaying && isMenuShown){
			playQueue.breakMotion();
			playQueue.reset();
		}
		if(isProductsShown){
			hideProducts();
		}
	}, true);
   
	document.addEventListener("mouseup", function() {
		document.removeEventListener("mousemove", handleMouseMove, true);
		isMouseDown = false;
		mouseX = undefined;
		mouseY = undefined;
	}, true);
   
	function handleMouseMove(e) {
		mouseX = (e.clientX - canvasPosition.x) / 30;
		mouseY = (e.clientY - canvasPosition.y) / 30;
	};
   
	function getBodyAtMouse() {
		mousePVec = new b2Vec2(mouseX, mouseY);
		var aabb = new b2AABB();
		aabb.lowerBound.Set(mouseX - 0.001, mouseY - 0.001);
		aabb.upperBound.Set(mouseX + 0.001, mouseY + 0.001);
      
      // Query the world for overlapping shapes.

		selectedBody = null;
		world.QueryAABB(getBodyCB, aabb);
		return selectedBody;
	}

	function getBodyCB(fixture) {
		if(fixture.GetBody().GetType() != b2Body.b2_staticBody) {
			if(fixture.GetShape().TestPoint(fixture.GetBody().GetTransform(), mousePVec)) {
			selectedBody = fixture.GetBody();
			return false;
		}
	}
	return true;
	}
   

	//update
	function update(){
   		if(isMouseDown && (!mouseJoint)) {
			var body = getBodyAtMouse();
			if(body) {
				var md = new b2MouseJointDef();
				md.bodyA = world.GetGroundBody();
				md.bodyB = body;
				md.target.Set(mouseX, mouseY);
				md.collideConnected = true;
				md.maxForce = 300.0 * body.GetMass();
				mouseJoint = world.CreateJoint(md);
				body.SetAwake(true);
			}
		}
      
		if(mouseJoint) {
			if(isMouseDown) {
				mouseJoint.SetTarget(new b2Vec2(mouseX, mouseY));
			}else {
				world.DestroyJoint(mouseJoint);
				mouseJoint = null;
			}
		}
   
		var w = world;
		w.Step(1 / 60, 10, 10);
		w.DrawDebugData();
		w.ClearForces();

		if(!playQueue.isPlaying){
			var b = w.GetBodyList();
			while(b){
				var bmp = b.GetUserData();
				if(bmp){
					bmp.x = b.GetPosition().x / SCALE; 
					bmp.y = b.GetPosition().y / SCALE;
					bmp.rotation = b.GetAngle()/createjs.Matrix2D.DEG_TO_RAD;
				}
				b = b.GetNext();
			}
		}
		stage.update();
	};
   
	//helpers
   
	//http://js-tut.aardon.de/js-tut/tutorial/position.html
	function getElementPosition(element) {
		var elem=element, tagname="", x=0, y=0;
     
		while((typeof(elem) == "object") && (typeof(elem.tagName) != "undefined")) {
			y += elem.offsetTop;
			x += elem.offsetLeft;
			tagname = elem.tagName.toUpperCase();
			if(tagname == "BODY"){
				elem=0;
			}
			if(typeof(elem) == "object") {
			if(typeof(elem.offsetParent) == "object")
				elem = elem.offsetParent;
			}
		}
		return {x: x, y: y};
	}

	//一定間隔毎に剛体を画面上から落下させる
	var falldown = setInterval(function (){
		if(!playQueue.isPlaying){
			var B2Math = Box2D.Common.Math;
			var b = world.GetBodyList();
			for(var i=0,n=indexfall;i<=n;i++){
				b = b.GetNext();
			}
			var v = new B2Math.b2Vec2(Math.random()*SW*SCALE,0);
			var r = new B2Math.b2Mat22.FromAngle(0*createjs.Matrix2D.DEG_TO_RAD);
			var t = new B2Math.b2Transform(v,r);
			b.SetTransform(t);
			indexfall++;
			if(indexfall == N)indexfall = 0;
		}
	},fallFrequency);

	//オープンシークエンス開始　
	intro();	

};

/*---------------------------------------
 * シークエンス0 Intro
 * --------------------------------------*/
	
//lineup→grid→matrixrandomalpha→[break]
function intro(){
	playQueue.setCallback(function(){
		showMenu();
	});
	var catalog = ['ribbon','magnet','shuffle'];
	var r = Math.floor(Math.random()* (catalog.length+1));
	log('r='+r);
	log('catalog '+catalog[r]);

	var delayedPlay = setInterval(function(){
		switch (catalog[r]){
			case 'ribbon':
				playQueue.addPlayList('grid',2000,100,{'interval':3});
				playQueue.addPlayList('circle',0,600,{'interval':3});
				playQueue.addPlayList('verticaltransfer',1000,null,{'positoin':-0.1,'interval':6});
				playQueue.play();
				break;
			case 'shuffle':
				playQueue.addPlayList('grid',100,400,{'interval':2});
				playQueue.addPlayList('scatter',2000,400,{'interval':2,'duration':500});
				playQueue.play();
				break;
			case 'magnet':
				playQueue.addPlayList('verticaltransfer',0,200,{'position':0.9,'interval':2});
				playQueue.addOverEffect(['randomalpha'],[350],null);
				playQueue.addPlayList('verticaltransfer',0,100,{'position':0.5,'interval':1});
				playQueue.addPlayList('lineup',0,null,null);
				playQueue.addOverEffect(['randomalpha'],[350],null);
				playQueue.play();
				break;
			default:
				showMenu();
				break;
		}
		clearInterval(delayedPlay);
	},500);
}

/*---------------------------------------
 * シークエンス1 Message 
 * --------------------------------------*/

//circle→grid→textgrid
function messeq(){
	if(!playQueue.isPlaying){
		console.log("now pushed");
		playQueue.isPlaying = true;
		var arg = {context:'mes'};
		grid(arg);
	}
	if(playQueue.isPlaying){
	}
}
	

/*---------------------------------------
 * シークエンス2 Services 
 * --------------------------------------*/
	
function servseq(){
	if(!playQueue.isPlaying){
		console.log("now pushed");
		playQueue.isPlaying = true;
		var arg = {context:'serv'};
		circle(arg);
	}
	if(playQueue.isPlaying){
	}
}

function clickm1(){ //MESSAGE
	console.log('menu1 clicked');
	if(!playQueue.isPlaying){
		playQueue.playGodsDice(2,true,function (){
			playQueue.reset();
			playQueue.addPlayList('textsequence',3000,null,{'text':message1,'sidepd':150,'toppd':70,'interval':10});
			playQueue.addPlayList('resettextsequence',null,null,null);
			playQueue.addPlayList('textsequence',3000,null,{'text':message2,'sidepd':150,'toppd':70,'interval':10});
			playQueue.addPlayList('resettextsequence',null,null,null);
			playQueue.addPlayList('textsequence',3000,null,{'text':message3,'sidepd':150,'toppd':70,'interval':10});
			playQueue.addPlayList('resettextsequence',null,null,null);
			playQueue.addPlayList('textsequence',3000,null,{'text':message4,'sidepd':150,'toppd':70,'interval':10});
			playQueue.addPlayList('resettextsequence',null,null,null);
			playQueue.addPlayList('textsequence',3000,null,{'text':message5,'sidepd':150,'toppd':70,'interval':10});
			playQueue.addPlayList('resettextsequence',null,null,null);
			playQueue.addPlayList('textsequence',3000,null,{'text':message6,'sidepd':150,'toppd':70,'interval':10});
			playQueue.addPlayList('scatter',2000,400,{'interval':2,'duration':500});
			playQueue.play();
		});
	}
}

function clickm2(){ //PRODUCTS
	console.log('menu2 clicked');
	if(!isProductsShown){
		showProducts();
		playQueue.addPlayList('randomalpha',0,300,{'minOpacity':0.1,'maxOpacity':0.1,'interval':0});
		playQueue.addPlayList('grid',10000,null,{'interval':20});
		playQueue.addOverEffect(['randomalpha'],[0],{'minOpacity':0.1,'maxOpacity':0.1,'interval':0});
		playQueue.addPlayList('matrixrandomalpha',100,null,null);
		playQueue.addPlayList('randomalpha',null,null,{'minOpacity':0.1,'maxOpacity':0.1,'interval':0});
		playQueue.play();
	}
}

function clickm3(){ //COMPANY
	console.log('menu3 clicked');
	if(!playQueue.isPlaying){
		playQueue.reset();
		playQueue.playGodsDice(2,true,function (){
			playQueue.addPlayList('textsequence',null,null,{'text':company,'sidepd':150,'toppd':70,'interval':10});
			playQueue.play();
		});
	}
}

function clickm4(){ //CONTACT
	console.log('menu4 clicked');
	if(!playQueue.isPlaying){
		playQueue.reset();
		playQueue.playGodsDice(100,false,null);
	}
}


