document.addEventListener('DOMContentLoaded', function() {
  // Keep your constants & variables as in CoffeeScript
  const MIN_PAGE_H = 600;
  const SCROLL_RANGE_HEADER_1 = 88;
  const SCROLL_RANGE_HEADER_2 = 250;
  const LOGO_REDUCE_RATE = 0.4;
  const SYMBOL_REDUCE_RATE = 0.32;
  let LOGO_HEIGHT_ORIGIN = 0;
  let LOGO_WIDTH_ORIGIN = 0;
  let SYMBOL_HEIGHT_ORIGIN = 0;
  let SYMBOL_WIDTH_ORIGIN = 0;

  // The main object "f" from CoffeeScript
  const f = {
    layoutHeader: function() {
      // Mimic $window.scrollTop()
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const windowWidth = window.innerWidth;

      // Only move header if > 750px wide
      if (windowWidth > 750) {
        // "header" top
        const header = document.querySelector('header.overlay');
        if (header) {
          if (scrollTop <= SCROLL_RANGE_HEADER_1) {
            header.style.top = (-70 / SCROLL_RANGE_HEADER_1 * scrollTop) + 'px';
          } else {
            header.style.top = '-70px';
          }
        }

        // menu margin-top
        const headerMenu = document.querySelector('header.overlay .menu');
        if (headerMenu) {
          if (scrollTop <= SCROLL_RANGE_HEADER_1) {
            headerMenu.style.marginTop = (45 / SCROLL_RANGE_HEADER_1 * scrollTop) + 'px';
          } else {
            headerMenu.style.marginTop = '45px';
          }
        }

        // logo height/width/margin-top
        const logo = document.querySelector('header.overlay .logo');
        if (logo) {
          if (scrollTop <= SCROLL_RANGE_HEADER_1) {
            const ratio = 1 - ((1 - LOGO_REDUCE_RATE) / SCROLL_RANGE_HEADER_1 * scrollTop);
            logo.style.height = (LOGO_HEIGHT_ORIGIN * ratio) + 'px';
            logo.style.width = (LOGO_WIDTH_ORIGIN * ratio) + 'px';
            logo.style.marginTop = (63 / SCROLL_RANGE_HEADER_1 * scrollTop) + 'px';
          } else {
            logo.style.height = (LOGO_HEIGHT_ORIGIN * LOGO_REDUCE_RATE) + 'px';
            logo.style.width = (LOGO_WIDTH_ORIGIN * LOGO_REDUCE_RATE) + 'px';
            logo.style.marginTop = '63px';
          }
        }

        // symbol height/width/margin-top
        const symbol = document.querySelector('header.overlay .symbol');
        if (symbol) {
          if (scrollTop <= SCROLL_RANGE_HEADER_1) {
            const ratioS = 1 - ((1 - SYMBOL_REDUCE_RATE) / SCROLL_RANGE_HEADER_1 * scrollTop);
            symbol.style.height = (SYMBOL_HEIGHT_ORIGIN * ratioS) + 'px';
            symbol.style.width = (SYMBOL_WIDTH_ORIGIN * ratioS) + 'px';
            symbol.style.marginTop = (60 / SCROLL_RANGE_HEADER_1 * scrollTop) + 'px';
          } else {
            symbol.style.height = (SYMBOL_HEIGHT_ORIGIN * SYMBOL_REDUCE_RATE) + 'px';
            symbol.style.width = (SYMBOL_WIDTH_ORIGIN * SYMBOL_REDUCE_RATE) + 'px';
            symbol.style.marginTop = '60px';
          }
        }
      }

      // header.underlay opacity
      const underlay = document.querySelector('header.underlay');
      if (underlay) {
        if (scrollTop <= SCROLL_RANGE_HEADER_2) {
          const newOpacity = Math.ceil((0.8 / SCROLL_RANGE_HEADER_2 * scrollTop) * 1000) / 1000;
          underlay.style.opacity = newOpacity;
        } else {
          underlay.style.opacity = '0.8';
        }
      }

      // Menu highlight logic (switch true => if/else chain)
      // for example:
      const solutionsPage = document.querySelector('[data-page=solutions]');
      const servicesPage = document.querySelector('[data-page=services]');
      const missionPage = document.querySelector('[data-page=mission]');
      const companyPage = document.querySelector('[data-page=company]');
      const contactPage = document.querySelector('[data-page=contact]');

      // If these pages do not exist in your current HTML, comment them out
      const offsetTop = function(elem) {
        if (!elem) return Infinity; // fallback if element is missing
        const rect = elem.getBoundingClientRect();
        return rect.top + window.pageYOffset;
      };

      const solTop = offsetTop(solutionsPage);
      const srvTop = offsetTop(servicesPage);
      const misTop = offsetTop(missionPage);
      const comTop = offsetTop(companyPage);
      const cntTop = offsetTop(contactPage);

      // remove "active" from all
      const menuSelectors = [
        '[data-menu=home]',
        '[data-menu=solutions]',
        '[data-menu=services]',
        '[data-menu=mission]',
        '[data-menu=company]',
        '[data-menu=contact]'
      ];
      menuSelectors.forEach(sel => {
        const el = document.querySelector(sel);
        if (el) el.classList.remove('active');
      });

      // This block replicates your "switch true" logic
      if (scrollTop < solTop) {
        const menuHome = document.querySelector('[data-menu=home]');
        if (menuHome) menuHome.classList.add('active');
      } else if (scrollTop < srvTop) {
        const menuSolutions = document.querySelector('[data-menu=solutions]');
        if (menuSolutions) menuSolutions.classList.add('active');
      } else if (scrollTop < misTop) {
        const menuServices = document.querySelector('[data-menu=services]');
        if (menuServices) menuServices.classList.add('active');
      } else if (scrollTop < comTop) {
        const menuMission = document.querySelector('[data-menu=mission]');
        if (menuMission) menuMission.classList.add('active');
      } else if (scrollTop < cntTop) {
        const menuCompany = document.querySelector('[data-menu=company]');
        if (menuCompany) menuCompany.classList.add('active');
      } else {
        const menuContact = document.querySelector('[data-menu=contact]');
        if (menuContact) menuContact.classList.add('active');
      }
    },

    initializeLayout: function() {
      const windowHeight = window.innerHeight;
      // set each page layout
      const fitPages = document.querySelectorAll('[data-fit-window="true"]');
      fitPages.forEach(page => {
        const style = window.getComputedStyle(page);
        const pad = parseInt(style.padding) || 0; // if uniform padding
        let pageHeight;
        if (windowHeight < MIN_PAGE_H && window.innerWidth > 750) {
          pageHeight = MIN_PAGE_H;
        } else {
          // If top/bottom are different, parse them individually
          const padTop = parseInt(style.paddingTop) || 0;
          const padBot = parseInt(style.paddingBottom) || 0;
          pageHeight = windowHeight - (padTop + padBot);
        }
        page.style.height = pageHeight + 'px';

        // set [container] margin top
        const container = page.querySelector('.container');
        if (container) {
          const containerH = container.offsetHeight;
          container.style.marginTop = (pageHeight - containerH) / 2 + 'px';
        }
      });
      f.showSite();
    },

    initializeModal: function() {
      // Your remodal or custom modal init if needed
    },

    mediaScreen: function(pc_value, tablet_value, sp_value) {
      const w = window.innerWidth;
      if (w > 1000) return pc_value;
      if (w <= 1000 && w > 640) return tablet_value;
      return sp_value;
    },

    scrollTo: function(page_id) {
      const target = document.querySelector('[data-page=' + page_id + ']');
      if (!target) return;
      const topPos = target.getBoundingClientRect().top + window.pageYOffset;
      window.scrollTo({
        top: topPos,
        behavior: 'smooth'
      });
    },

    scrollToElement: function(elem) {
      if (!elem) return;
      const topPos = elem.getBoundingClientRect().top + window.pageYOffset;
      window.scrollTo({
        top: topPos,
        behavior: 'smooth'
      });
    },

    scrollToPosition: function(pos) {
      window.scrollTo({
        top: pos,
        behavior: 'smooth'
      });
    },

    resetDefault: function() {
      LOGO_HEIGHT_ORIGIN = f.mediaScreen(93, 79, 60);
      LOGO_WIDTH_ORIGIN = f.mediaScreen(243, 199, 150);
      SYMBOL_HEIGHT_ORIGIN = f.mediaScreen(172, 146, 100);
      SYMBOL_WIDTH_ORIGIN = f.mediaScreen(172, 146, 100);
    },

    showSite: function() {
      document.body.classList.add('show');
    }
  };

  // Set initial dimension-based values
  f.resetDefault();

  // Hook window events like $(window).on('load scroll resize') in jQuery
  window.addEventListener('load', function() {
    f.layoutHeader();
    f.initializeLayout();
    f.initializeModal();
  });
  window.addEventListener('scroll', f.layoutHeader);
  window.addEventListener('resize', function() {
    f.layoutHeader();
    f.resetDefault();
  });

  // If you had code like: $("[data-action=scroll]").on("click", ...)
  // => Use querySelectorAll and loop:
  const scrollEls = document.querySelectorAll('[data-action="scroll"]');
  scrollEls.forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      const dist = el.getAttribute('data-distination'); // or el.dataset.distination
      if (dist) {
        f.scrollTo(dist);
      }
      // If header.overlay hasClass('open'), remove it
      const hdr = document.querySelector('header.overlay');
      if (hdr && hdr.classList.contains('open')) {
        hdr.classList.remove('open');
      }
    });
  });

  // Toggle menu
  const toggleEls = document.querySelectorAll('[data-action="toggle-menu"]');
  toggleEls.forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      const hdr = document.querySelector('header.overlay');
      if (hdr) {
        if (hdr.classList.contains('open')) {
          hdr.classList.remove('open');
        } else {
          hdr.classList.add('open');
        }
      }
    });
  });

  // If you have an "open-inquiry-modal" button
  const openInquiryEls = document.querySelectorAll('[data-action="open-inquiry-modal"]');
  openInquiryEls.forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.preventDefault();

      const inquiryModal = document.getElementById('inquiry-modal');
      const inputKeys = ['name', 'organization', 'email', 'message'];
      let is_valid = true;
      let scroll_element_top = null;

      for (let i = 0; i < inputKeys.length; i++) {
        const key = inputKeys[i];
        let inputElem;
        if (key === 'message') {
          inputElem = document.querySelector('textarea[name=message]');
        } else {
          inputElem = document.querySelector('input[name=' + key + ']');
        }
        if (!inputElem) continue;

        if (inputElem.value.trim().length === 0) {
          inputElem.parentNode.classList.add('alert');
          is_valid = false;
          if (!scroll_element_top) {
            // top offset
            const rect = inputElem.getBoundingClientRect();
            scroll_element_top = rect.top + window.pageYOffset;
          }
        } else {
          inputElem.parentNode.classList.remove('alert');
        }

        // Insert input texts to modal preview
        // e.g. inquiryModal.querySelector('[data-review-input='+key+']').textContent = inputElem.value;
        if (inquiryModal) {
          const reviewTarget = inquiryModal.querySelector('[data-review-input=' + key + ']');
          if (reviewTarget) {
            reviewTarget.textContent = inputElem.value;
          }
        }
      }

      if (is_valid) {
        // If using Remodal, do inquiryModal.remodal().open();
        // Or use your custom modal
      } else {
        // scroll to the first invalid field
        if (scroll_element_top !== null) {
          f.scrollToPosition(scroll_element_top - 100);
        }
      }
    });
  });

  // Remove .alert on focus
  const inputsToWatch = document.querySelectorAll('input[name=name], input[name=organization], input[name=email], textarea[name=message]');
  inputsToWatch.forEach(function(el) {
    el.addEventListener('focus', function(e) {
      if (el.parentNode && el.parentNode.classList.contains('alert')) {
        el.parentNode.classList.remove('alert');
      }
    });
  });

  // If you had $(document).on 'confirmation', '#inquiry-modal'
  // You'd do something like:
  const inquiryModalEl = document.getElementById('inquiry-modal');
  if (inquiryModalEl) {
    inquiryModalEl.addEventListener('confirmation', function(e) {
      e.preventDefault();
      // same logic as the original
      const inputName = document.querySelector('input[name=name]');
      const inputOrg = document.querySelector('input[name=organization]');
      const inputEmail = document.querySelector('input[name=email]');
      const inputMsg = document.querySelector('textarea[name=message]');

      const name = inputName ? inputName.value : '';
      const organization = inputOrg ? inputOrg.value : '';
      const email = inputEmail ? inputEmail.value : '';
      const message = inputMsg ? inputMsg.value : '';

      const messageModal = document.getElementById('message-modal');

      // send inquiry => use fetch() instead of $.ajax
      fetch('/inquiry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json;charset=UTF-8' },
        body: JSON.stringify({
          name: name,
          organization: organization,
          email: email,
          message: message
        })
      })
        .then(response => response.json())
        .then(function(result) {
          console.log(result);
          if (result.success) {
            console.log('success');
            if (messageModal) {
              const msgTarget = messageModal.querySelector('[data-insert=message]');
              if (msgTarget) msgTarget.textContent = 'お問い合わせの送信が完了しました。';
              // messageModal.remodal().open() or your custom show
            }
            // clear inputs
            if (inputName) inputName.value = '';
            if (inputOrg) inputOrg.value = '';
            if (inputEmail) inputEmail.value = '';
            if (inputMsg) inputMsg.value = '';
          } else {
            console.log(result.alert);
            if (messageModal) {
              const msgTarget = messageModal.querySelector('[data-insert=message]');
              if (msgTarget) msgTarget.textContent = result.alert;
              // messageModal.remodal().open()
            }
          }
        })
        .catch(function(error) {
          console.log(error);
          if (messageModal) {
            const msgTarget = messageModal.querySelector('[data-insert=message]');
            if (msgTarget) msgTarget.textContent = error;
            // messageModal.remodal().open()
          }
        });
    });
  }
});
