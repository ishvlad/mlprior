var app = angular.module('drf-angular', [
    'djng.urls',
    'ui.router',
    // 'djangoRESTResources',
    'ngResource',

]);


// app.constant('BASE_URL', 'http://localhost:8000/articles/api/');
app.constant('BASE_URL', 'http://mlprior.com/articles/api/');

app.config(function($stateProvider, $urlRouterProvider, $interpolateProvider, $httpProvider){
    // $stateProvider
    //     .state('article_detail', {
    //         url: '/articles/details/:id',
    //         templateUrl: '/templates/articles/article_details.html',
    //         controller: 'MainCtrl'
    //     });
    //     .state('add-blogpost', {
    //         url: "/add",
    //         templateUrl: 'templates/add_todo.html',
    //         controller: 'MainCtrl'
    //     });

    $urlRouterProvider.otherwise('/');

    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');

    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

});


// app.factory('blogs', function ($resource) {
//     return $resource(
//             'http://localhost:8000/articles/api/articles/:id/',
//             {},
//             {
//                 'query': {
//                     method: 'GET',
//                     isArray: true,
//                     headers: {
//                         'Content-Type':'application/json'
//                     }
//                 }
//             },
//             {
//                 stripTrailingSlashes: false
//             }
//     );
// });

// app.service('articles', function($http, BASE_URL) {
//
// });


app.service('BlogPosts', function($location, $http, BASE_URL){
    var BlogPosts = {};

    var getArticleId = function () {
        return $location.absUrl().split('/')[5].replace(/\D/g,'');
    };

    // var url = $location.;
    // console.log('URL');
    // console.log(url);

    BlogPosts.all = function(callbackFunc){
        id = getArticleId();
        return $http.get(BASE_URL + 'articles/' + id).then(function (res) {
            blogposts = res.data['blog_post'];


            $http.get(BASE_URL + 'blogpostuser/').then(function (res) {
                console.log(res.data);
                blogposts.forEach(function (x) {
                    if (res.data.includes(x.id)){
                        x.is_like = true;
                    }
                });

                callbackFunc(blogposts);
            });


        });

    };

    BlogPosts.update = function(updatedTodo){
        return $http.put(BASE_URL + 'blogposts/' + updatedTodo.id + '/', updatedTodo);
    };

    BlogPosts.delete = function(id){
        return $http.delete(BASE_URL + id + '/');
    };

    BlogPosts.addOne = function(newBlogPost){
        newBlogPost.article_id = getArticleId();
        return $http.post(BASE_URL + 'blogposts/', newBlogPost)
    };

    return BlogPosts;
});


app.service('Articles', function ($location, $http, BASE_URL) {
    var Article = {};

    var getArticleId = function () {
        return $location.absUrl().split('/')[5].replace(/\D/g,'');
    };


    Article.get = function (callbackFunc) {
        id = getArticleId();

        $http.get(BASE_URL + 'articles/' + id).then(function (res) {
            article = res.data;

            callbackFunc(article);
        });

    };

    return Article
});



app.controller('MainCtrl', function($location, $scope, BlogPosts, Articles, $state){
    $scope.newBlogPost = {};
    $scope.blogposts = [];
    $scope.created = true;

    function updateBlogPosts() {
        BlogPosts.all(function(dataResponse) {
            console.log(dataResponse);
            $scope.blogposts = dataResponse;
        });
    }

    updateBlogPosts();

    Articles.get(function (dataResponse) {
        $scope.article = dataResponse;
        console.log($scope.article);
    });

    $scope.addBlogPost = function() {
        BlogPosts.addOne($scope.newBlogPost)
            .then(function(res){
                $scope.created = res.data.created;
                updateBlogPosts();
            });
    };

    $scope.changeLike = function(blogpost) {
        BlogPosts.update(blogpost).then(function () {
            updateBlogPosts();
        });
    };

    $scope.deleteTodo = function(id){
        Todos.delete(id);
        // update the list in ui
        $scope.todos = $scope.todos.filter(function(todo){
            return todo.id !== id;
        })
    };
});

$(document).ready(function(){
    $('[data-toggle="popover"]').popover();
});

