$(function() {

    function changeButton(article_id, oldClasses, newClasses, newText) {
        el = document.getElementById('button-'+article_id);
          oldClasses.forEach(function(element) {
            el.classList.remove(element);
          });
          newClasses.forEach(function(element) {
            el.classList.add(element);
          });

          el.querySelector('.text').textContent = newText;
    }

    $("body").on('click', '.savetolibrary', function () {
        var article_id = $(this).attr("data-article-id");
        var action = $(this).attr("data-action");

            $.ajax({
                url: '/articles/api/v1/library/add/' + article_id,
                type: 'post',
                data: {
                    'article_id': article_id
                },
                dataType: 'json',
                success: function (data) {
                    var oldClasses = ['btn-primary', 'savetolibrary'];
                    var newClasses = ['btn-secondary', 'donotsave'];

                    changeButton(article_id, oldClasses, newClasses, 'Saved');

                }
            });

    }).on('click', '.removefromlibrary', function () {
        var article_id = $(this).attr("data-article-id");

        $.ajax({
            url: '/articles/api/v1/library/remove/' + article_id,
            type: 'delete',
            data: {
                'article_id': article_id
            },
            dataType: 'json',
            success: function (data) {
                el = document.getElementById('article-'+article_id);
                el.parentNode.removeChild(el);
            }
        });
    }).on('click', '.donotsave', function () {
        var article_id = $(this).attr("data-article-id");

        $.ajax({
            url: '/articles/api/v1/library/remove/' + article_id,
            type: 'delete',
            data: {
                'article_id': article_id
            },
            dataType: 'json',
            success: function (data) {
                var oldClasses = ['btn-secondary', 'donotsave'];
                var newClasses = ['btn-primary', 'savetolibrary'];

                changeButton(article_id, oldClasses, newClasses, 'Save to Library');
            }
        });
    }).on('input propertychange change', '.note-form', function () {
        // FUNCTION FOR NOTES
        var article_id = $(this).attr("data-article-id");

        console.log('huy');
        console.log($(this).val() );

            $.ajax({
                url: '/articles/api/v1/note/update/' + article_id,
                type: 'post',
                data: {
                    'article_id': article_id,
                    'note': $(this).val()
                },
                dataType: 'json',
                success: function (data) {


                }
            });

    });

        // .on('click', '#search-button', function () {
        // var search_query = document.getElementById('search-button').parentNode.parentNode;
        // search_query = search_query.querySelector('#search-input').value;
        //
        // console.log(search_query);
        //
        // $.ajax({
        //     url: '/api/articles/search/' + search_query,
        //     type: 'get',
        //     data: {'search_query': search_query},
        //     dataType: 'json',
        //     success: function (data) {
        //         print(data)
        //         // var oldClasses = ['btn-secondary', 'donotsave'];
        //         // var newClasses = ['btn-primary', 'savetolibrary'];
        //         //
        //         // changeButton(article_id, oldClasses, newClasses, 'Save to Library');
        //     }
        // });
    // })



    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $(document);

});