$(function() {

    $("body").on('click', '.likehuy', function () {
        console.log('huy');
        var article_id = $(this).attr("data-article-id");
        var action = $(this).attr("data-action");

        console.log(article_id);
        console.log(action);

        if (action == 'del') {
            $.ajax({
                url: '/articles/like',
                type: 'delete',
                data: {
                    'article_id': article_id,
                    'csrfmiddlewaretoken': '{{ csrf_token }}'
                },
                dataType: 'json',
                success: function (data) {
                    console.log(data);
                }
            });
        } else {
            $.ajax({
                url: '/articles/like',
                type: 'get',
                data: {
                    'article_id': article_id,
                    'csrfmiddlewaretoken': '{{ csrf_token }}'
                },
                dataType: 'json',
                success: function (data) {
                    console.log(data);
                }
            });
        }
        console.log('huy2');
    });

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

});