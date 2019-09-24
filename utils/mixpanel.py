import mixpanel
from mlprior.settings import IS_DEBUG

class MixPanel_actions:
    ###############
    #   GENERAL   #
    ###############

    load_login = 'LOAD login'
    load_signup = 'LOAD signup'

    login = 'LOGIN'                                             # done
    signup = 'SIGNUP'                                           # done
    logout = 'LOGOUT'                                           # done
    feedback = 'FEEDBACK'                                       # done
    search = 'SEARCH'                                           # done

    request_demo = "REQUEST DEMO"

    ###############
    #  DASHBOARD  #
    ###############

    load_dashboard = 'LOAD dashboard'                           # done

    ###############
    #   Articles  #
    ###############

    load_articles_recent = 'LOAD articles.recent'               # done
    load_articles_recommended = 'LOAD articles.recommended'     # done
    load_articles_popular = 'LOAD articles.popular'             # done
    load_articles_library = 'LOAD articles.library'             # done
    load_articles_liked = 'LOAD articles.liked'                 # done
    load_articles_author = 'LOAD articles.author'               # done

    ###############
    #   Details   #
    ###############

    load_article_details = 'LOAD article.details'               # done

    action_article_pdf = 'OUT article.pdf'                      # done
    action_article_summary = 'SHOW article.summary'             # done   in article details
    action_open_article_summary = 'OPEN article.summary'        # done   in short article view
    action_article_blogpts = 'SHOW article.blogposts'
    action_article_related = 'SHOW article.related'             # done

    ###############
    #   Premium   #
    ###############

    open_premium_description = 'PREMIUM open description'       # done
    start_premium_trial = 'PREMIUM start trial'                 # done


class MixPanel:
    actions = MixPanel_actions()
    MIXPANEL_TOKEN = '48b541d1a79e7cd214268d30a58f190d'

    def __init__(self, user):
        self.mp = mixpanel.Mixpanel(self.MIXPANEL_TOKEN)

        if user.is_authenticated:
            self.user_id = user.id
            self.user_email = user.email
        else:
            self.user_id = -1
            self.user_email = 'Anonym'

        if not IS_DEBUG:
            self.mp.people_set(self.user_id, {
                '$ID': self.user_id,
                '$Email': self.user_email
            })

    def track(self, action, properties=None):
        if not IS_DEBUG:
            self.mp.track(self.user_id, action, properties)
