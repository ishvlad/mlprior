var app = angular.module('drf-angular', [
    'djng.urls',
    'ui.router',
    // 'djangoRESTResources',
    'ngResource',

]);

app.constant('BASE_URL', '/articles/api/');

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

app.directive("randomBackground", function () {
    return function(scope, element, attrs) {
        angular.element(element).css('color','blue');
    if (scope.$last){
        var backgrounds = ['bg-success', 'bg-info', 'bg-primary', 'bg-danger', ''];
        var show = backgrounds[Math.floor(Math.random() * backgrounds.length)];
        element[0].classList.add(show);
    }
  };
});



app.service('BlogPosts', function($location, $http, BASE_URL){
    var BlogPosts = {};

    var getArticleId = function () {
        return $location.absUrl().split('/')[5].replace(/\D/g,'');
    };

    BlogPosts.all = function(callbackFunc){
        id = getArticleId();
        return $http.get(BASE_URL + 'articles/' + id).then(function (res) {
            blogposts = res.data['blog_posts'];

            $http.get(BASE_URL + 'blogpostuser/').then(function (res) {
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


app.service('GitHubs', function($location, $http, BASE_URL){
    var GitHubs = {};

    var getArticleId = function () {
        return $location.absUrl().split('/')[5].replace(/\D/g,'');
    };

    GitHubs.all = function(callbackFunc){
        id = getArticleId();
        return $http.get(BASE_URL + 'articles/' + id).then(function (res) {
            githubs = res.data['githubs'];

            $http.get(BASE_URL + 'githubuser/').then(function (res) {
                githubs.forEach(function (x) {
                    if (res.data.includes(x.id)){
                        x.is_like = true;
                    }
                });

                callbackFunc(githubs);
            });


        });

    };

    GitHubs.update = function(updatedTodo){
        return $http.put(BASE_URL + 'githubs/' + updatedTodo.id + '/', updatedTodo);
    };

    GitHubs.delete = function(id){
        return $http.delete(BASE_URL + id + '/');
    };

    GitHubs.addOne = function(newGitHub){
        newGitHub.article_id = getArticleId();
        return $http.post(BASE_URL + 'githubs/', newGitHub)
    };

    return GitHubs;
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



app.controller('MainCtrl', function($location, $scope, BlogPosts, GitHubs, Articles, $state){
    $scope.newBlogPost = {};
    $scope.newGitHub = {};

    $scope.blogposts = [];
    $scope.githubs = [];

    $scope.created = true;

    function updateBlogPosts() {
        BlogPosts.all(function(dataResponse) {
            $scope.blogposts = dataResponse;
        });
    }

    function updateGitHubs() {
        GitHubs.all(function(dataResponse) {
            $scope.githubs = dataResponse;
        });
    }

    function resetForm() {
        $scope.blogPostForm.$setPristine();
                $scope.newBlogPost = {};
                $scope.blogPostForm.$setUntouched()
    }

    updateBlogPosts();
    updateGitHubs();

    Articles.get(function (dataResponse) {
        $scope.article = dataResponse;
    });

    $scope.addBlogPost = function() {
        BlogPosts.addOne($scope.newBlogPost)
            .then(function(res){
                $scope.created = res.data.created;
                updateBlogPosts();
                resetForm()
            });
    };

    $scope.addGitHub = function() {
        GitHubs.addOne($scope.newGitHub)
            .then(function(res){
                $scope.created = res.data.created;
                updateGitHubs();
                // resetForm() TODO update github form
            });
    };

    $scope.changBlogPostLike = function(blogpost) {
        BlogPosts.update(blogpost).then(function () {
            updateBlogPosts();
        });
    };

    $scope.changeGitHubLike = function(github) {
        GitHubs.update(github).then(function () {
            updateGitHubs();
        });
    };


    // $scope.deleteTodo = function(id){
    //     Todos.delete(id);
    //     // update the list in ui
    //     $scope.todos = $scope.todos.filter(function(todo){
    //         return todo.id !== id;
    //     })
    // };
});

$(document).ready(function(){
    $('[data-toggle="popover"]').popover();
});
