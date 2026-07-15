
//stage setting
var FPS = 30;
var N = 700; //テキストオブジェクトの数
var floorInset = 0.05; //床剛体の最下部からの位置をスクリーン長比で指定 (0.0~1.0)
var fallFrequency = 400; //落下周期 (ms)

//phisical environment
var gravity = 20;
var density_floor = 2.0; //密度
var friction_floor = 1.5; //摩擦
var restitution_floor = 0; //弾性

var density_object = 1.0; //密度
var friction_object = 0.5; //摩擦
var restitution_object = 0.6; //弾性

//sentences
var message1 = "Since the scientific revolution of the 17th century, society has been facing the limits of complexity.";
var message2 = "As differentiation has progressed, people have become mechanized within the confines of systems,";
var message3 = " and meditation has become indispensable for protecting themselves from stimuli.";
var message4 = "We need to regain the era of integrated knowledge. This is the transcendence of modernity,"
var message5 = "which will bring us a new creative society,"
var message6 = " that is, a new Renaissance era."
//var message1 = "Science is the conflicting concept with ideology\nabout the objectivity.";
//var message2 = "But when the science takes in ideologies,\nit would be an art.";
//var message3 = "Though it's difficult to answer the question that what is art,\nnot difficult to say that this is an art for some work of art.";
//var message4 = "Because it always has some ability to make people doubt something\nwhich is in a deep inside of us."
//var message5 = "And now the possibility for more people to make them is getting increased\nby the democratize of technologies and the growth of capitalism."
//var message6 = "We believe that to embody this reality makes our world exciting more."

var company = 'CONTACT\nKazuki Otsuka\n81(80)4365-1460\notsuka.kazuki@googlemail.com';

//shuffle effect
const shuffle = true;//false;
const shuffleSpeed = 20;

// layout
const menuLeft = 20;
const menuTop = 60;

var copyright = 'Copyright© 2012-2015 ThinkX,Inc All rights reserved.';

/*
 *	rlayQueue.addPlayList('grid',2000,100,null);
	playQueue.addPlayList('circle',0,null,{'interval':3});
	playQueue.addPlayList('verticaltransfer',1000,null,{'positoin':-0.1,'interval':3});
	playQueue.play();
	
	*/

