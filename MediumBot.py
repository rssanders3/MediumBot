#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Matt Flood

import time
from selenium import webdriver
from bs4 import BeautifulSoup

# Configure constants here
EMAIL = ''
PASSWORD = ''
LOGIN_SERVICE = 'Google'
DRIVER = 'Firefox'
LIKE_POSTS = True
NUM_LIKES_ON_POST = 20
ARTICLE_BLACK_LIST = []
FOLLOW_USERS = False
UNFOLLOW_USERS = False
VERBOSE = True
SEARCH_TOPICS = []


users_followed_file = open("users_followed.txt", "r")
USERS_ALREADY_FOLLOWED = users_followed_file.read().split("\n")
print "USERS_ALREADY_FOLLOWED: " + str(USERS_ALREADY_FOLLOWED)

def Launch():
    """
    Launch the Medium bot and ask the user what browser they want to use.
    """

    if 'chrome' not in DRIVER.lower() and 'firefox' not in DRIVER.lower() and 'phantomjs' not in DRIVER.lower():

        # Browser choice
        print 'Choose your browser:'
        print '[1] Chrome'
        print '[2] Firefox/Iceweasel'
        print '[3] PhantomJS'

        while True:
            try:
                browserChoice = int(raw_input('Choice? '))
            except ValueError:
                print 'Invalid choice.',
            else:
                if browserChoice not in [1,2,3]:
                    print 'Invalid choice.',
                else:
                    break

        StartBrowser(browserChoice)

    elif 'chrome' in DRIVER.lower():
        StartBrowser(1)

    elif 'firefox' in DRIVER.lower():
        StartBrowser(2)

    elif 'phantomjs' in DRIVER.lower():
        StartBrowser(3)

def WriteUserToFollowed(user):
    USERS_ALREADY_FOLLOWED.append(user)
    users_followed_file = open("users_followed.txt", "a")
    users_followed_file.write("\n" + user)
    users_followed_file.flush()
    users_followed_file.close()

def StartBrowser(browserChoice):
    """
    Based on the option selected by the user start the selenium browser.
    browserChoice: browser option selected by the user.
    """

    if browserChoice == 1:
        print '\nLaunching Chrome'
        browser = webdriver.Chrome()
    elif browserChoice == 2:
        print '\nLaunching Firefox/Iceweasel'
        browser = webdriver.Firefox()
    elif browserChoice == 3:
        print '\nLaunching PhantomJS'
        browser = webdriver.PhantomJS()

    if SignInToService(browser):
        print 'Success!\n'
        MediumBot(browser)

    else:
        soup = BeautifulSoup(browser.page_source, "lxml")
        if soup.find('div', {'class':'alert error'}):
            print 'Error! Please verify your username and password.'
        elif browser.title == '403: Forbidden':
            print 'Medium is momentarily unavailable. Please wait a moment, then try again.'
        else:
            print 'Please make sure your config is set up correctly.'

    browser.quit()


def SignInToService(browser):
    """
    Using the selenium browser passed and the config file login to Medium to
    begin the botting.
    browser: the selenium browser used to login to Medium.
    """

    serviceToSignWith = LOGIN_SERVICE.lower()
    signInCompleted = False
    print 'Signing in...'

    # Sign in
    browser.get('https://medium.com/m/signin?redirect=https%3A%2F%2Fmedium.com%2F')

    if serviceToSignWith == "google":
        signInCompleted = SignInToGoogle(browser)

    return signInCompleted


def SignInToGoogle(browser):
    """
    Sign into Medium using a Google account.
    browser: selenium driver used to interact with the page.
    return: true if successfully logged in : false if login failed.
    """

    signInCompleted = False

    try:
        browser.find_element_by_xpath('//span[contains(text(),"Sign up with Google")]').click()
        time.sleep(3)
        browser.find_element_by_id('identifierId').send_keys(EMAIL)
        browser.find_element_by_id('identifierNext').click()
        time.sleep(3)
        browser.find_element_by_name('password').send_keys(PASSWORD)
        browser.find_element_by_id('passwordNext').click()
        time.sleep(2)
        signInCompleted = True
    except Exception, e:
        print "Exception while setting username and password: " + str(e)

    return signInCompleted


def MediumBot(browser):
    """
    Start botting Medium
    browser: selenium browser used to interact with the page
    """

    articleURLsVisited = []

    # Infinite loop
    while True:

        articleURLsQueued = ScrapeArticlesOffMainPage(browser)
        for topic in SEARCH_TOPICS:
            articleURLsQueued.extend(ScrapeUrlsOffSearchPage(browser, topic))

        print("articleURLsQueued: " + str(articleURLsQueued))

        for articleURL in articleURLsQueued:
            if articleURL not in articleURLsVisited:
                LikeAndFollowOnPost(browser, articleURL)
            else:
                print "Already Visited this URL"

        print '\nPause for 1 hour to wait for new articles to be posted\n'
        time.sleep(3600+(random.randrange(0, 10))*60)


def ScrapeArticlesOffMainPage(browser):
    browser.get("https://medium.com/")
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, "lxml")
    urls = []
    print 'Gathering urls'

    try:
        for a in soup.find_all('a', class_='ds-link ds-link--stylePointer u-overflowHidden u-flex0 u-width100pct'):
            if a["href"] not in urls:
                urls.append(a["href"])
                if VERBOSE:
                    print a["href"]
    except Exception, e:
        print 'Exception thrown in ScrapeArticlesOffMainPage(): ' + str(e)

    return urls


def ScrapeUrlsOffSearchPage(browser, topic):
    print "topic: " + str(topic)
    browser.get("https://medium.com/search?q=" + str(topic))
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, "lxml")
    urls = []
    print 'Gathering urls'

    try:
        for a in soup.find_all('a', {"data-action": "open-post"}):
            if a["href"] not in urls:
                urls.append(a["href"])
                if VERBOSE:
                    print a["href"]
    except Exception, e:
        print 'Exception thrown in ScrapeUrlsOffSearch()' + str(e)

    return urls


def LikeAndFollowOnPost(browser, articleURL):
    """
    Like, comment, and/or follow the author of the post that has been navigated to.
    browser: selenium browser used to find the like button and click it.
    articleURL: the url of the article to navigate to and like and/or comment
    """

    browser.get(articleURL)

    if browser.title not in ARTICLE_BLACK_LIST:
        if FOLLOW_USERS:
            FollowUser(browser)
        if UNFOLLOW_USERS:
            UnFollowUser(browser)
        ScrollToBottomAndWaitForLoad(browser)
        ScrollHalfWayAndWaitForLoad(browser)
        if LIKE_POSTS:
            LikeArticle(browser)


def LikeArticle(browser):
    """
    Like the article that has already been navigated to.
    browser: selenium driver used to interact with the page.
    """
    alreadyLikedButton = None
    try:
        alreadyLikedButton = browser.find_element_by_xpath('//button[contains(@class, "multi-vote-undo-revealed")]')
    except Exception, e:
        pass

    try:
        if not alreadyLikedButton:
            likeButton = browser.find_element_by_xpath('//div[@data-test-id="post-sidebar"]/div/div/div/div/div/button')
            for i in range(0, NUM_LIKES_ON_POST):
                likeButton.click()
        else:
            print "Article was already liked"
    except Exception, e:
        print 'Exception thrown in LikeArticle(): ' + str(e)


def FollowUser(browser):
    """
    Follow the user whose article you have already currently navigated to.
    browser: selenium webdriver used to interact with the browser.
    """
    try:
        user_name = browser.find_element_by_xpath('//div/span/a').text
        if user_name not in USERS_ALREADY_FOLLOWED:
            browser.find_element_by_xpath('//button[text()="Follow"]').click()
            WriteUserToFollowed(user_name)
        else:
            print "Skipping following user '" + str(user_name) + "' since they were already followed"
    except Exception, e:
        if VERBOSE:
            print 'Exception thrown when trying to follow the user: ' + str(e)


def UnFollowUser(browser):
    """
    UnFollow a just from your followed user list.
    browser: selenium webdriver used to interact with the browser.
    Note: view the black list of users you do not want to unfollow.
    """
    try:
        soup = BeautifulSoup(browser.page_source, "lxml")
        if len(soup.find_all('button', text="Following")) != 0:
            browser.find_element_by_xpath('//button[text()="Following"]').click()
        else:
            print "Can't unfollow user as you are not following"
    except Exception, e:
        if VERBOSE:
            print 'Exception thrown when trying to follow the user: ' + str(e)


def ScrollToBottomAndWaitForLoad(browser):
    """
    Scroll to the bottom of the page and wait for the page to perform it's lazy loading.
    browser: selenium webdriver used to interact with the browser.
    """

    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)


def ScrollHalfWayAndWaitForLoad(browser):
    """
    Scroll to the bottom of the page and wait for the page to perform it's lazy loading.
    browser: selenium webdriver used to interact with the browser.
    """

    browser.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(3)


if __name__ == '__main__':
    Launch()
