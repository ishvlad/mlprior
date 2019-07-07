from mlprior.settings import IS_DEBUG
import os

class MixPanel:
    ###############
    #   GENERAL   #
    ###############

    MIXPANEL_TOKEN = '48b541d1a79e7cd214268d30a58f190d'
    PREFIX = ('[DEV MODE | ' + os.environ['HOME'].split('/')[-1] + '] ') * int(IS_DEBUG)

    login = PREFIX + 'LOGIN'
    signup = PREFIX + 'SIGNUP'

    ###############
    #  DASHBOARD  #
    ###############

    load_dashboard = PREFIX + 'LOAD dashboard'
    update_categories = PREFIX + 'UPDATE categories'

    ###############
    #   Articles  #
    ###############

    load_articles_recent = PREFIX + 'LOAD articles recent'
    load_articles_recommended = PREFIX + 'LOAD articles recommended'
    load_articles_popular = PREFIX + 'LOAD articles popular'

    ###############
    #   Details   #
    ###############

    load_article_details = PREFIX + 'LOAD article details'

    ###############
    #   Library   #
    ###############

    load_articles_saved = PREFIX + 'LOAD articles saved'
    load_articles_liked = PREFIX + 'LOAD articles liked'
    load_articles_disliked = PREFIX + 'LOAD articles disliked'

    ###############
    #    Author   #
    ###############

    load_author_articles = PREFIX + 'LOAD author articles'

    @staticmethod
    def user_set(mp, user):
        if user.is_authenticated:
            mp.people_set(user.id, {
                '$ID': user.id,
                '$Email': user.email
            })
            return user.id
        else:
            mp.people_set(-1, {
                '$ID': -1,
                '$Email': 'Anonym'
            })
            return -1
