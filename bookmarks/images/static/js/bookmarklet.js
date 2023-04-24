(function(){
  var jquery_version = '3.3.1';
//  var site_url = 'https://3f6ad53c.ngrok.io/';
  var static_url = site_url + 'static/';
  var min_width = 100;
  var min_height = 100;

  function bookmarklet(msg) {
    // загрузка CSS
    var css = jQuery('<link>');
    css.attr({
      rel: 'stylesheet',
      type: 'text/css',
      href: static_url + 'css/bookmarklet.css?r=' + Math.floor(Math.random()*99999999999999999999)
    });
    jQuery('head').append(css);

    // загрузка HTML
    box_html = '<div id="bookmarklet"><a href="#" id="close">&times;</a><h1>Select an image to bookmark:</h1><div class="images"></div></div>';
    jQuery('body').append(box_html);

    // close event
    jQuery('#bookmarklet #close').click(function(){
       jQuery('#bookmarklet').remove();
    });
    
    // находим картинки и отображаем их
    jQuery.each(jQuery('img[src$="jpg"]'), function(index, image) {
      if (jQuery(image).width() >= min_width && jQuery(image).height() >= min_height)
      {
        image_url = jQuery(image).attr('src');
        jQuery('#bookmarklet .images').append('<a href="#"><img src="'+ image_url +'" /></a>');
      }
    });
    
    // когда картинка выбрана открывается её URL
    jQuery('#bookmarklet .images a').click(function(e){
      selected_image = jQuery(this).children('img').attr('src');
      // скрыть
      jQuery('#bookmarklet').hide();
      // открыть новое окно чтобы нажать на картинку
      window.open(site_url +'images/create/?url='
                  + encodeURIComponent(selected_image)
                  + '&title='
                  + encodeURIComponent(jQuery('title').text()),
                  '_blank');
    });
  };

  // проверить что jQuery загружен
  if(typeof window.jQuery != 'undefined') {
    bookmarklet();
  } else {
    // проверить нет ли конфликтов
    var conflict = typeof window.$ != 'undefined';
    // создать скрипт и указать Google API
    var script = document.createElement('script');
    script.src = '//ajax.googleapis.com/ajax/libs/jquery/' + 
      jquery_version + '/jquery.min.js';
    // добавить скрипт в хэд выполнения
    document.head.appendChild(script);
    // Создать путь для ожидания пока скрипт загрузится
    var attempts = 15;
    (function(){
      // если JQuery не задан проверить еще раз
      if(typeof window.jQuery == 'undefined') {
        if(--attempts > 0) {
          // вызвать его через несколько милисекунд
          window.setTimeout(arguments.callee, 250)
        } else {
          // Превышение попыток загрузки, отправить ошибку
          alert('An error occurred while loading jQuery')
        }
      } else {
          bookmarklet();
      }
    })();
  }
})()