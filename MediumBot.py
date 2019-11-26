#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Matt Flood

import time, random
from selenium import webdriver
from bs4 import BeautifulSoup

LOAD_TIME_SEC = 3

# Configure constants here
EMAIL = ''
PASSWORD = ''
LOGIN_SERVICE = 'Google'
DRIVER = 'Firefox'
GET_ARTICLES_FROM_MAIN_PAGE = True
NUMBER_OF_MAIN_PAGE_PAGES = 4
LIKE_POSTS = True
NUM_LIKES_ON_POST = 20
ARTICLE_BLACK_LIST = []
FOLLOW_USERS = False
UNFOLLOW_USERS = False
VERBOSE = True

GET_ARTICLES_FROM_SEARCH_TOPICS = False
SEARCH_TOPICS = ["fitness", "exercise", "health"]
NUMBER_OF_TOPIC_PAGES = 2

GET_ARTICLES_FROM_PUBLICATIONS = False
PUBLICATION_URLS = ["https://towardsdatascience.com/"]
NUMBER_OF_PUBLICATION_PAGES = 2

NUMBER_OF_TIMES_TO_ITERATE = 1  # -1 = infinite


users_followed_file = open("users_followed.txt", "r")
USERS_ALREADY_FOLLOWED = users_followed_file.read().split("\n")
print "USERS_ALREADY_FOLLOWED: " + str(USERS_ALREADY_FOLLOWED)


LIKE_COUNT = 0
SKIP_COUNT = 0
FAILED_COUNT = 0


def Launch():
    """
    Launch the Medium bot and ask the user what browser they want to use.
    """

    LIKE_COUNT = 0
    SKIP_COUNT = 0
    FAILED_COUNT = 0

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
        time.sleep(LOAD_TIME_SEC)
        browser.find_element_by_id('identifierId').send_keys(EMAIL)
        browser.find_element_by_id('identifierNext').click()
        time.sleep(LOAD_TIME_SEC)
        browser.find_element_by_name('password').send_keys(PASSWORD)
        browser.find_element_by_id('passwordNext').click()
        time.sleep(LOAD_TIME_SEC)
        signInCompleted = True
    except Exception, e:
        print "Exception while setting username and password: " + str(e)

    return signInCompleted


def MediumBot(browser):
    """
    Start botting Medium
    browser: selenium browser used to interact with the page
    """

    articleURLsQueued = []
    articleURLsVisited = []

    iteration = 0
    # Infinite loop
    while True:

        if GET_ARTICLES_FROM_MAIN_PAGE:
            articleURLsQueued.extend(ScrapeArticlesOffMainPage(browser))
        if GET_ARTICLES_FROM_SEARCH_TOPICS:
            for topic in SEARCH_TOPICS:
                articleURLsQueued.extend(ScrapeUrlsOffSearchPage(browser, topic))
        if GET_ARTICLES_FROM_PUBLICATIONS:
            for publication_url in PUBLICATION_URLS:
                articleURLsQueued.extend(ScrapeUrlsOffPublicationPage(browser, publication_url))

        print("\n")
        print("articleURLsQueued Length: " + str(len(articleURLsQueued)))

        totalCount = len(articleURLsQueued)
        currentPos = 0
        for articleURL in articleURLsQueued:
            if articleURL not in articleURLsVisited:
                LikeAndFollowOnPost(browser, articleURL)
                articleURLsVisited.append(articleURLsQueued)
            else:
                print "Already Visited this URL"
            currentPos += 1
            if (currentPos % 10) == 0 or currentPos == totalCount:
                print "Completed " + str(currentPos) + " of " + str(totalCount)

        iteration += 1
        print "iteration: " + str(iteration) + ", NUMBER_OF_TIMES_TO_ITERATE: " + str(NUMBER_OF_TIMES_TO_ITERATE)
        if NUMBER_OF_TIMES_TO_ITERATE != -1:
            if iteration == NUMBER_OF_TIMES_TO_ITERATE:
                print "\nBreaking loop and finishing..."
                break

        print '\nPause for 1 hour to wait for new articles to be posted\n'
        time.sleep(3600+(random.randrange(0, 10))*60)

    print "\nSummary:"
    print "Number of Posts Liked: " + str(LIKE_COUNT)
    print "Number of Posts Skipped: " + str(SKIP_COUNT)
    print "Number of Posts Failed to Like: " + str(FAILED_COUNT)


def ScrapeArticlesOffMainPage(browser):
    browser.get("https://medium.com/")
    time.sleep(LOAD_TIME_SEC)
    for i in range(0, NUMBER_OF_MAIN_PAGE_PAGES):
        ScrollToBottomAndWaitForLoad(browser)
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
    time.sleep(LOAD_TIME_SEC)
    for i in range(0, NUMBER_OF_TOPIC_PAGES):
        ScrollToBottomAndWaitForLoad(browser)
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


def ScrapeUrlsOffPublicationPage(browser, publication_url):
    print "publication_url: " + str(publication_url)
    browser.get(publication_url)
    time.sleep(LOAD_TIME_SEC)
    for i in range(0, NUMBER_OF_PUBLICATION_PAGES):
        ScrollToBottomAndWaitForLoad(browser)
    soup = BeautifulSoup(browser.page_source, "lxml")
    urls = []
    print 'Gathering urls'

    try:
        for a in soup.find_all('a', {"data-action": "open-post"}):
        # for a in soup.find_all('a', {"class": "u-block.*"}):
            if a["href"] not in urls:
                urls.append(a["href"])
                if VERBOSE:
                    print a["href"]
    except Exception, e:
        print 'Exception thrown in ScrapeUrlsOffPublicationPage()' + str(e)

    return urls


def LikeAndFollowOnPost(browser, articleURL):
    """
    Like, comment, and/or follow the author of the post that has been navigated to.
    browser: selenium browser used to find the like button and click it.
    articleURL: the url of the article to navigate to and like and/or comment
    """

    try:
        print "Navigating to: " + str(articleURL)
        browser.get(articleURL)

        if browser.title not in ARTICLE_BLACK_LIST:
            if FOLLOW_USERS:
                FollowUser(browser)
            if UNFOLLOW_USERS:
                UnFollowUser(browser)
            # ScrollToBottomAndWaitForLoad(browser)
            ScrollHalfWayAndWaitForLoad(browser)
            if LIKE_POSTS:
                LikeArticle(browser)
    except Exception, e:
        print 'Exception thrown in LikeAndFollowOnPost(): ' + str(e)
        browser.quit()
        exit(1)


def LikeArticle(browser):
    """
    Like the article that has already been navigated to.
    browser: selenium driver used to interact with the page.
    """

    # XQuery In Java Script for Testing:
    #   document.querySelector('/html/body/div/div');
    #   document.evaluate('/html/body//h2', document.body, null, XPathResult.ANY_TYPE, null).iterateNext()
    global LIKE_COUNT
    global SKIP_COUNT
    global FAILED_COUNT

    alreadyLikedButton = None
    try:
        alreadyLikedButton = browser.find_element_by_xpath('//button[contains(@class, "multi-vote-undo-revealed")]')
    except Exception, e:
        pass

    # document.evaluate('/html/body/div/div/div[5]/div/div[1]/div/div[4]/div[1]/div[1]/div/div/button', document.body, null, XPathResult.ANY_TYPE, null).iterateNext()

    try:
        if not alreadyLikedButton:
            # likeButton = browser.find_element_by_xpath('//div[@data-test-id="post-sidebar"]/div/div/div/div/div/button')
            likeButton = browser.find_element_by_xpath('/html/body/div/div/div[5]/div/div[1]/div/div[4]/div[1]/div[1]/div/div/button')
            for i in range(0, NUM_LIKES_ON_POST):
                likeButton.click()
            print "Successfully Liked the Article"
            LIKE_COUNT += 1
        else:
            print "Article was already liked"
            SKIP_COUNT += 1
    except Exception, e:
        FAILED_COUNT += 1
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
