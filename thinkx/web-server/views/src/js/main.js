document.addEventListener('DOMContentLoaded', function() {
    const f = {
        initializeLayout: function() {
            const windowHeight = window.innerHeight;
            f.showSite();
        },

        showSite: function() {
            document.body.classList.add('show');
        }
    };

    window.addEventListener('load', function(e) {
        f.initializeLayout();
    });
});
