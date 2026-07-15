document.addEventListener("DOMContentLoaded", function() {
    const productsSection = document.getElementById('products-section');
    const $products = document.querySelectorAll('.product');
    const viewportHeight = window.innerHeight;

    const $videoContainer = document.querySelector('.video-container');

    const $videoQuantz = document.getElementById('video-quantz');
    const $videoVoiceAIOS = document.getElementById('video-voice-AI-OS')
    const $videoILRSA = document.getElementById('video-ILRSA')
    const $videoCITYWALK = document.getElementById('video-CITYWALK')
    const $imgLSH = document.getElementById('image-LSH')

    const fadeImages = document.querySelectorAll(
        '.product.voiceOS .images-container img'
      );

    function activateVideoQuantz() {
        $videoQuantz.classList.add('active');
        $videoQuantz.play()
    }

    function deactivateVideoQuantz() {
        $videoQuantz.classList.remove('active');
        $videoQuantz.pause();
        $videoQuantz.currentTime = 0; // Optionally reset video time
    }
    
    function activateVideoVoiceAIOS() {
        $videoVoiceAIOS.classList.add('active');
        $videoVoiceAIOS.play();
    }
    
    function deactivateVideoVoiceAIOS() {
        $videoVoiceAIOS.classList.remove('active');
        $videoVoiceAIOS.pause();
        $videoVoiceAIOS.currentTime = 0; // Optionally reset video time
    }
    
    function activateVideoILRSA() {
        $videoILRSA.classList.add('active');
        $videoILRSA.play();
    }
    
    function deactivateVideoILRSA() {
        $videoILRSA.classList.remove('active');
        $videoILRSA.pause();
        $videoILRSA.currentTime = 0;
    }
    
    function activateVideoCITYWALK() {
        $videoCITYWALK.classList.add('active');
        $videoCITYWALK.play();
    }
    
    function deactivateVideoCITYWALK() {
        $videoCITYWALK.classList.remove('active');
        $videoCITYWALK.pause();
        $videoCITYWALK.currentTime = 0;
    }

    function activateImageLSH() {
        if ($imgLSH) {
            $imgLSH.classList.add("active");
        }
    }
    function deactivateImageLSH() {
        if ($imgLSH) {
            $imgLSH.classList.remove("active");
        }
    }

    function activateMedia(productKey) {
        switch (productKey) {
            case "quantz":
                console.log('Activating Quantz video');
                activateVideoQuantz();
                break;
            case "voice-AI-OS":
                console.log('Activating Voice AI OS video');
                activateVideoVoiceAIOS();
                break;
            case "ILRSA":
                console.log('Activating ILRSA video');
                activateVideoILRSA();
                break;
            case "CITYWALK":
                console.log('Activating CITYWALK video');
                activateVideoCITYWALK();
                break;
            case "LSH":
                console.log('Activating LSH image');
                activateImageLSH();
                break;
            default:
                console.log('Deactivating all videos');
                //deactivateAllVideo()
        }
    }

    function deactivateMedia(productKey) {
        console.log(`Deactivating video for: ${productKey}`);
        switch (productKey) {
            case "quantz":
                deactivateVideoQuantz();
                break;
            case "voice-AI-OS":
                deactivateVideoVoiceAIOS();
                break;
            case "ILRSA":
                deactivateVideoILRSA();
                break;
            case "CITYWALK":
                deactivateVideoCITYWALK();
                break;
            case "LSH":
                deactivateImageLSH();
                break;
            default:
                console.log('Deactivating all videos');
                //deactivateAllVideo();
        }
    }

    function toggleMediaActivation(product, activate = true) {
        const productKey = product.dataset.product;
        if (activate) {
            product.classList.add('active');
            activateMedia(productKey);
        } else {
            product.classList.remove('active');
            deactivateMedia(productKey);
        }
    }
    
    function toggleAllMediaActivation(activate = true) {
        $products.forEach(product => {
            toggleMediaActivation(product, activate)
        })
    }

    function checkVisibility() {
        const scrollY = window.screenY;
        const productsSectionRect = productsSection.getBoundingClientRect();
        const viewportCenter = viewportHeight / 2 + window.scrollY; // center of the viewport
        const viewportHeightCenter = viewportHeight / 2;
        const windowH = viewportHeight;

        const productsSectionTopY = productsSectionRect.top + scrollY;
        const productsSectionBottomY = productsSectionRect.bottom + scrollY;

        console.log(`productsSection top: ${productsSectionTopY}, bottom: ${productsSectionBottomY}, viewportCenter: ${viewportCenter}, viewport height center ${viewportHeightCenter}`);

        // Check if the viewport center is between the top and bottom of the products section
        //if (viewportHeightCenter > sectionTop && viewportHeightCenter < sectionBottom) {
        //    console.log('******************** triggered');
        //    $videoContainer.classList.add('active');
        //} else {
        //    console.log('**not triggered');
        //    $videoContainer.classList.remove('active');
        //    deactivateAllVideo()
        //}

        if (viewportHeightCenter < productsSectionTopY) {
            toggleAllMediaActivation(false)
        }

        $products.forEach(product => {
            const windowTop = window.scrollY;
            const productRect = product.getBoundingClientRect();
            const productCenter = productRect.top + window.scrollY + productRect.height / 2;
            const productTop = productRect.top + window.scrollY;
            const productBottom = productRect.bottom + window.scrollY;

            //console.log(`Checking product: ${product.querySelector('h2.name').textContent}`);
            //console.log(`Window Top: ${windowTop}, Viewport Center: ${viewportCenter}, Product Center: ${productCenter}, Product Top: ${productTop}`);

            if (productTop < viewportCenter - (windowH / 3) && productBottom > windowTop) {
                //console.log(`Activating product: ${product.querySelector('h2.name').textContent}`);
                toggleMediaActivation(product, true);
            } else {
                //console.log(`Deactivating product: ${product.querySelector('h2.name').textContent}`);
                //toggleVideoActivation(product, false);
            }
        });

        $products.forEach(product => {
            product.addEventListener('mouseenter', () => toggleMediaActivation(product, true));
        });

    }

    function checkImagesVisibility() {
        fadeImages.forEach(img => {
          const rect = img.getBoundingClientRect();
          // Simple in-viewport test:
          const adjust = 500;
          const inView =
            rect.top < window.innerHeight - adjust && 
            rect.bottom > 0;
    
          if (inView) {
            // Add .visible -> triggers fade/slide-in via CSS
            img.classList.add('visible');
          }
          // If you ever want to hide them again when out of view,
          // you could remove the .visible class:
          // else {
          //   img.classList.remove('visible');
          // }
        });
    }

    window.addEventListener('scroll', checkVisibility);
    window.addEventListener('resize', checkVisibility); // Adjust when window size changes
    window.addEventListener('scroll', checkImagesVisibility);
    window.addEventListener('resize', checkImagesVisibility);
    checkVisibility(); // Initial check on load
    checkImagesVisibility();
});