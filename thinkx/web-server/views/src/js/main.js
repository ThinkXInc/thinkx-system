// load だと GTM / 和文フォント等、描画に不要なものの完了まで body が伏せられる。
document.addEventListener('DOMContentLoaded', function() {
    // opacity:0 を1フレーム描画してから付与する。同一フレームだとフェードが飛ぶ。
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            document.body.classList.add('show');
        });
    });
});
