'use strict'
/**
 * @fileoverview business/view_controllers/introduction_view_controller.js
 * IntroductionView controller class.
 * 
 * @author kaz@thinkxinc.com (Kazuki Otsuka)
 **/


/**
 * IntroductionViewController class.
 * 
 * TODO: write view_components/modal_view_controller.js and inherit it
 * 
 * @constructor
 */
class IntroductionViewController {
    __introduction_view_id__ = 'introductionView'
    __introduction_video_src__ = '/video/intro.mp4'
    __introduction_video_poster__ = '/img/intro_video_poster.png'

    constructor() {
        this._initObservers()
    }

    /**
     * Initialize observers.
     */
    _initObservers() {
        const _this = this;
    }

    /**
     * Create IntroductionView.
     * 
     */
    createView(parentViewId) {
        let $parentView = document.getElementById(parentViewId);
        // introductionView
        let $introductionView = document.createElement('section');
        $introductionView.id = this.__introduction_view_id__;
        $introductionView.classList.add(this.__introduction_view_id__);
        $parentView.appendChild($introductionView);
        // container
        let $container = document.createElement('div');
        $container.classList.add('container');
        $introductionView.appendChild($container);
        // video
        let $video = document.createElement('video');
        $video.src = this.__introduction_video_src__;
        $video.poster = this.__introduction_video_poster__;
        $video.autoplay = true;
        $video.controls = false;
        $video.muted = true;  // necessary to enable autoplay
        $video.playsInline = true;
        $video.loop = false;
        $container.appendChild($video);
        // skip button
        let $skipButton = document.createElement('button');
        $skipButton.innerText = 'skip';
        let _this = this;
        $skipButton.addEventListener('click', (e) => {
            _this.closeView();
        })
        $introductionView.appendChild($skipButton);
        // TODO: modulize
        // progress bar
        let $progressBG = document.createElement('div');
        $progressBG.classList.add('progressBG');
        $progressBG.style.width = '100%';
        $progressBG.style.height = '6px';
        $progressBG.style.backgroundColor = '#f0f0f0';
        let $progress = document.createElement('div');
        $progress.id = `${this.__introduction_view_id__}_progress`;
        $progress.classList.add('progress');
        $progress.style.width = '10%';
        $progress.style.height = '6px';
        $progress.style.backgroundColor = '#616161';
        $container.appendChild($progressBG);
        $progressBG.appendChild($progress);

        // set timer
        const durationSec = 6;
        this._setTimerToCloseIntroductionView(durationSec);
        this._setProgressTimer(durationSec);
    }

    /**
     * Close $introductionView
     * 
     */
    closeView() {
        console.log('close introductionView');
        // hide introductionView
        let $introductionView = document.getElementById(this.__introduction_view_id__);
        $introductionView.classList.add('hidden');
    }

    /**
     * Set progress time inteval.
     * 
     * @param {Int or Float} durationSec 
     */
    _setProgressTimer(durationSec) {
        function isFloat(n) {
            return n === +n && n !== (n|0);
        }
        function isInteger(n) {
            return n === +n && n === (n|0);
        }
        if (!(isFloat(durationSec) || isInteger(durationSec))) {
            console.error(`durationSec must be type of Int/Float, but${typeof(durationSec)}.`)
        }
        let _that = this;
        let count = 0;
        window.setInterval(() => {
            count = count + 0.1;
            const percentage = (count/durationSec)*100;
            // console.log(`[progress] ===> ${percentage} %`);  // [DEBUG]
            _that._updateProgress(_that.__introduction_view_id__, percentage);
        }, 100)
    }

    /**
     * Update progress indicator.
     * TODO: modulize
     * 
     * @param {String} viewId 
     * @param {Int} percentage 
     */
    _updateProgress(viewId, percentage) {
        let $progress = document.getElementById(
            `${viewId}_progress`);
        $progress.style.width = `${percentage}%`;
    }

    /**
     * Set timer to close $introductioView.
     * 
     * @param {Int} sec 
     */
    _setTimerToCloseIntroductionView(sec) {
        let _that = this;
        window.setTimeout(() => {
            _that.closeView();
        }, sec*1000);
    }

 
}
 