#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO:
#   Add Verification System
#   Consider including country in database
#   Finish EditBarber/EditUser
#   FUCK FORM VALIDATION
#       Must have At Least 1 Service
#       No semicolon in username
#   Barber personal blurb
#   Unix time stamp
#   Consider Time Zones Day Light Savings (Long, Lat)
#   Shop hours
#   Favorite Barber
#       Issue when no favorites. Look into this.
#   Quality Control on Approx Cost
#   Check if Gql queries are faster
#   Include phone # on necessary pages

import cgi
import logging
import csv
import urllib
import random
import webapp2
import jinja2
import json
import os
import hashlib
import math
from django.utils import simplejson
from datetime import datetime, timedelta, time
import logging
from google.appengine.ext import deferred
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+'/'),
    extensions=['jinja2.ext.autoescape'])
# application settings
account_id = 860764059    # your app's account_id
access_token = 'PRODUCTION_7d635086b74e2bb90d8a13c0046bee6adba703b362d06e27645a12a5da553d59' # your app's access_token
BATCH_SIZE = 100  # ideal batch size may vary based on entity size.
client_id =147330
client_secret ="75d19ee2f1"

production =True
# set production to True for live environments

#WEPAY STUFF ====================================================================================
#================================================================================================
class WePay(object):

    """
    A client for the WePay API.
    """

    def __init__(self, production=True, access_token=None, api_version=None):
        """
        :param bool production: When ``False``, the ``stage.wepay.com`` API
            server will be used instead of the default production.
        :param str access_token: The access token associated with your
            application.
        """
        self.access_token = access_token
        self.api_version = api_version

        if production:
            self.api_endpoint = "https://wepayapi.com/v2/"
            self.browser_endpoint = "https://www.wepay.com/v2/"
        else:
            self.api_endpoint = "https://stage.wepayapi.com/v2"
            self.browser_endpoint = "https://stage.wepay.com/v2"

    def call(self, uri, params=None, token=None):
        """
        Calls wepay.com/v2/``uri`` with ``params`` and returns the JSON
        response as a python dict. The optional token parameter will override
        the instance's access_token if it is set.

        :param str uri: The URI on the API endpoint to call.
        :param dict params: The parameters to pass to the URI.
        :param str token: Optional override for this ``WePay`` object's access
            token.
        """

        headers = {'Content-Type': 'application/json',
                   'User-Agent': 'WePay Python SDK'}
        url = self.api_endpoint + uri

        if self.access_token or token:
            headers['Authorization'] = 'Bearer ' + \
                (token if token else self.access_token)

        if self.api_version:
            headers['Api-Version'] = self.api_version

        if params:
            params = json.dumps(params)

        try:
            response = urlfetch.fetch(
                url=url,payload=params, method=urlfetch.POST,headers=headers)
            return response.content
        except:
            if 400 <= response.status_code <= 599:
                raise Exception('Unknown error. Please contact support@wepay.com '+response.content)

    def get_token(self, redirect_uri, client_id, client_secret, code, callback_uri=None):
        """
        Calls wepay.com/v2/oauth2/token to get an access token. Sets the
        access_token for the WePay instance and returns the entire response
        as a dict. Should only be called after the user returns from being
        sent to get_authorization_url.
        :param str redirect_uri: The same URI specified in the
        :py:meth:`get_authorization_url` call that preceeded this.
        :param str client_id: The client ID issued by WePay to your app.
        :param str client_secret: The client secret issued by WePay
        to your app.
        :param str code: The code returned by :py:meth:`get_authorization_url`.
        :param str callback_uri: The callback_uri you want to receive IPNs for
        this user on.
        """
        params = {
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        }
        #response = 'client_id : '+str(client_id)
        if callback_uri:
            params.update({'callback_uri': callback_uri})
        response = self.call('/oauth2/token', params)
        #self.access_token = response['access_token']
        return json.loads(response)



wepay = WePay(production, access_token)


SERVICES = ['Haircuts/Trims','Shades','Tapers','Brush Cuts','Design Haircuts','Clipper Shaves','Razor Shaves','Edge Shape Ups','Facial Trims','Eyebrow Arches','Neck Tapers','Shampoo','Conditionings','Natural Dyes','Beard Trims','Strengthening Therapies','Relaxers','Twists','Braids','Curls','Locs','Perms','Weaves','Extensions','Coloring Highlights','Updos','Formal Hairstyles']

POINT_PERCENT = .1
def getUser(username,password):
    if not(username):
        return None
    users = User.query(User.email == username)
    for user in users:
        return user
    return None
def getUser2(username,password):
    user = User.get_by_id(username)
    if not(user):
        return None
    if not(user.password == hashlib.sha224(password).hexdigest()):
        return None
    return user

def generateVerifyCode():
    alphanumeric = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    string = ""
    for i in range(50):
        string+=alphanumeric[random.randint(0,len(alphanumeric)-1)]
    return string

def generatePassword():
    alphanumeric = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    string = ""
    for i in range(16):
        string+=alphanumeric[random.randint(0,len(alphanumeric)-1)]
    return string

def getBarber(username,password):
    user = getUser(username,password)
    if not(user):
        return None
    if not(user.barber):
        return None
    return user
class Flag (ndb.Model):
    userid = ndb.StringProperty(default= 0)
    barberid =ndb.StringProperty(default= 0)
def getFlag(user):
    flags = Flag.query(Flag.userid== user.email)
    for flag in flags:
        return flag
class Shop (ndb.Model):
    name = ndb.StringProperty()
    location = ndb.GeoPtProperty()
    owner = ndb.IntegerProperty()
    logo =  ndb.BlobKeyProperty()
def createshop(newname, newlocation, newowner,user):
   
    newshop = Shop(id =newname,
                   name = newname,
                   location = newlocation,
                   owner = newowner)
    user.shopName = newname;
    Shop_user_array = [Shop,user]
    return newshop

    
    
class User(ndb.Model):
    #key_name is log in name
    verify = ndb.StringProperty()
    wepayuid = ndb.StringProperty(default='') #default sets it to empty
    wepayat = ndb.StringProperty(default='') #default sets it to empty
    firstName = ndb.StringProperty()
    lastName = ndb.StringProperty()
    email = ndb.StringProperty()
    password = ndb.StringProperty()
    phone = ndb.StringProperty()
    location = ndb.GeoPtProperty()
    city = ndb.StringProperty()
    street = ndb.StringProperty()
    state = ndb.StringProperty()
    barber = ndb.BooleanProperty()
    certified = ndb.BooleanProperty()
    services = ndb.StringProperty()
    shopName = ndb.StringProperty()
    photo = ndb.BlobKeyProperty()
    favorite = ndb.StringProperty()
    totalScore = ndb.IntegerProperty()
    totalReviews = ndb.IntegerProperty()
    currentRating = ndb.FloatProperty()
    haircutsTrims = ndb.FloatProperty()
    shades = ndb.FloatProperty()
    tapers = ndb.FloatProperty()
    brushCuts = ndb.FloatProperty()
    designHaircuts = ndb.FloatProperty()
    clipperShaves = ndb.FloatProperty()
    razorShaves  = ndb.FloatProperty()
    edgeShapeUps  = ndb.FloatProperty()
    facialTrims  = ndb.FloatProperty()
    eyebrowArches = ndb.FloatProperty()
    neckTapers  = ndb.FloatProperty()
    shampoo = ndb.FloatProperty()
    conditionings  = ndb.FloatProperty()
    naturalDyes = ndb.FloatProperty()
    beardTrims  = ndb.FloatProperty()
    strengtheningTherapies = ndb.FloatProperty()
    relaxers = ndb.FloatProperty()
    twists = ndb.FloatProperty()
    braids = ndb.FloatProperty()
    curls  = ndb.FloatProperty()
    locs = ndb.FloatProperty()
    perms = ndb.FloatProperty()
    weaves= ndb.FloatProperty()
    extensions = ndb.FloatProperty()
    coloringHighlights = ndb.FloatProperty()
    updos = ndb.FloatProperty()
    formalHairstyles  = ndb.FloatProperty()
    occupation = ndb.StringProperty()
    license = ndb.StringProperty()
#reward points to keep track of users points
    rewardpoints = ndb.IntegerProperty()
#float is price #Have mamadou implement all of these
    aboutMe = ndb.StringProperty()

class BarberCalendar(ndb.Model):
    #parent is corresponding barber
    sundayStart = ndb.TimeProperty() 
    sundayEnd = ndb.TimeProperty()
    mondayStart = ndb.TimeProperty()
    mondayEnd = ndb.TimeProperty()
    tuesdayStart = ndb.TimeProperty()
    tuesdayEnd = ndb.TimeProperty()
    wednesdayStart = ndb.TimeProperty()
    wednesdayEnd = ndb.TimeProperty()
    thursdayStart = ndb.TimeProperty()
    thursdayEnd = ndb.TimeProperty()
    fridayStart = ndb.TimeProperty()
    fridayEnd = ndb.TimeProperty()
    saturdayStart = ndb.TimeProperty()
    saturdayEnd = ndb.TimeProperty()

class Appointment(ndb.Model):
    #parent is corresponding barber
    services = ndb.StringProperty()
    user = ndb.StringProperty() #client's username
    startTime = ndb.DateTimeProperty()
    time = ndb.IntegerProperty()
    status = ndb.IntegerProperty()
    comment = ndb.StringProperty()
    checkoutid = ndb.IntegerProperty(default=0)  # checkout id in order to refund
    paid = ndb.BooleanProperty()
    checkoutid = ndb.IntegerProperty(default=0)  # checkout id in order to refund
#usedpoint thing for reward system
   #usedpoints = ndb.InterProrperty()
    price = ndb.FloatProperty()

class Review(ndb.Model):
    #parent is corresponding barber
    user = ndb.StringProperty() #client's username
    rating = ndb.IntegerProperty()
    comments = ndb.StringProperty()
    date = ndb.DateTimeProperty()
    

GEOCODE_BASE_URL = 'http://maps.googleapis.com/maps/api/geocode/json'

def geocode(address,sensor, **geo_args):
    geo_args.update({
        'address': address,
        'sensor': sensor  
    })
    url = GEOCODE_BASE_URL + '?' + urllib.urlencode(geo_args)
    result = simplejson.load(urllib.urlopen(url))
    try:
        result = result['results'][0]
        result = result['geometry']['location']
        result = [result['lat'],result['lng']]
        return result
    except:
        return geocode(address,sensor)

def getDist(loc1, loc2):
    R = 6371
    dLat = math.radians(float(loc2[0])-float(loc1[0]))
    dLon = math.radians(float(loc2[1])-float(loc1[1]))
    lat1 = math.radians(float(loc2[0]))
    lat2 = math.radians(float(loc2[0]))
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2);
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
    d = R * c;
    d = d * 0.62137
    return d

def getProfileButton(user):

    a =""
    b = "Register"
    string= '<a   class="dropdown-toggle"data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">'+b+'</a>'
    if user:
        a ="/MainPage"
        b = "DashBoard"
        string = '<a href="'+a+'"  class="dropdown-toggle" rel="external" aria-haspopup="true" aria-expanded="false">'+b+'</a>'
    return string
########################mamadous addditions

class ForgotPass(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get('user',''),self.request.cookies.get('pass',''))
        if user:
            self.redirect('/')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect(''),
            'action': "/sendPass",
            'entry': "Email:",
            'button': "Reset Password",
            'message': "Enter in your Email, and we will reset your password.",
            'query': "username",
            'error': "The username you have entered is not registered in our database."
        }
        template = JINJA_ENVIRONMENT.get_template('forgot.html')
        self.response.write(template.render(template_values))

class SendPass(webapp2.RequestHandler):
    def post(self):
        username = self.request.get('entry')
        password = generatePassword()
        user = User.get_by_id(username)
        user.password = hashlib.sha224(password).hexdigest()
        user.put()
        mail.send_mail("HeadWay  <mamadouwann@gmail.com>",
                       "<"+user.email.__str__()+">",
                       "Your New Password",
                       "Thank you for using our services. Your new password is "+password)
        self.redirect('/')
class Verify(webapp2.RequestHandler):
    def get(self):
        code = self.request.get('code')
        username = self.request.get('username')
        user = User.get_by_id(username)
        if not(user):
            self.redirect('/')
            return
        if not(user.verify==code):
            self.redirect('/')
            return
        user.verify = ""
        user.put()
        mail.send_mail("Headway <mamadouwann@gmail.com>",
                       "Headway <mamadouwann@gmail.com>",
                       "New Account Verified!",
                       "A new user has been verified. username: "+self.request.get('username'))
        template_values = {
            'name': user.firstName.__str__()+" "+user.lastName.__str__()
        }
        template = JINJA_ENVIRONMENT.get_template('verify.html')
        self.response.write(template.render(template_values))
    
       
######################################################################
def typeofprof(occupation):
    if occupation =="Barber":
        return "Barber"
    if occupation =="Hairdresser":
        return "Hairdresser"
#REDUNDENCY
    
def getStateSelect(state):
    states = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado",
     "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois",
     "Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
     "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana",
     "Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York",
     "North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
     "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah",
     "Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"]
    string = '<label for="state">State:</label><select name="state" class="form-control" style="color=black!important;" id="state">'
    for i in range(len(states)):
        if state==states[i]:
            string+='<option class="form-control" style="color=black!important;" selected>'+states[i]+'</option>'
        else:
            string+='<option >'+states[i]+'</option>'
    return string+'</select>'


class SaveHours(webapp2.RequestHandler):
    def post(self):
        barber = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(barber):
            self.redirect('/')
            return
        calendars = BarberCalendar.query(ancestor=barber.key)
        c = None
        for cal in calendars:
            c = cal
        c.sundayStart = getTime(self.request.get("1Start"))
        c.sundayEnd = getTime(self.request.get("1End"))
        c.mondayStart = getTime(self.request.get("2Start"))
        c.mondayEnd = getTime(self.request.get("2End"))
        c.tuesdayStart = getTime(self.request.get("3Start"))
        c.tuesdayEnd = getTime(self.request.get("3End"))
        c.wednesdayStart = getTime(self.request.get("4Start"))
        c.wednesdayEnd = getTime(self.request.get("4End"))
        c.thursdayStart = getTime(self.request.get("5Start"))
        c.thursdayEnd = getTime(self.request.get("5End"))
        c.fridayStart = getTime(self.request.get("6Start"))
        c.fridayEnd = getTime(self.request.get("6End"))
        c.saturdayStart = getTime(self.request.get("7Start"))
        c.saturdayEnd = getTime(self.request.get("7End"))
        c.put()
        self.redirect('/viewBarber/'+barber.key.integer_id().__str__())

class ChangeHours(webapp2.RequestHandler):
    def get(self):
        barber = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(barber):
            self.redirect('/')
            return
        calendars = BarberCalendar.query(ancestor=barber.key)
        calendar = None
        for c in calendars:
            calendar = c
        template_values = {
            "profilebutton": getProfileButton(barber),
            "sundayStart": getHourSelectList(c.sundayStart),
            "sundayEnd": getHourSelectList(c.sundayEnd),
            "mondayStart": getHourSelectList(c.mondayStart),
            "mondayEnd": getHourSelectList(c.mondayEnd),
            "tuesdayStart": getHourSelectList(c.tuesdayStart),
            "tuesdayEnd": getHourSelectList(c.tuesdayEnd),
            "wednesdayStart": getHourSelectList(c.wednesdayStart),
            "wednesdayEnd": getHourSelectList(c.wednesdayEnd),
            "thursdayStart": getHourSelectList(c.thursdayStart),
            "thursdayEnd": getHourSelectList(c.thursdayEnd),
            "fridayStart": getHourSelectList(c.fridayStart),
            "fridayEnd": getHourSelectList(c.fridayEnd),
            "saturdayStart": getHourSelectList(c.saturdayStart),
            "saturdayEnd": getHourSelectList(c.saturdayEnd)
        }
        template = JINJA_ENVIRONMENT.get_template('changeHours.html')
        self.response.out.write(template.render(template_values))

def getHourSelectList(time):
    string = '<option value="-1">OFF</option>'
    for i in range(17):
        h = i+6
        selected1 = ''
        selected2 = ''
        var1 = ''
        if time:
            if time.hour == h:
                if time.minute == 0:
                    selected1 = 'selected'
                else:
                    selected2 = 'selected'
        ampm = ' AM'
        if h>=12:
            ampm = ' PM'
        if h>12:
            h = h - 12
        string+='<option value="'+str((i+6))+'" '+selected1+'>'+str(h)+':00'+ampm+'</option>'
        string+='<option value="'+str((i+6))+'.5" '+selected2+'>'+str(h)+':30'+ampm+'</option>'
    return string

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_page = 'index.html'
        editRef = "editUser"
        favoritebutton =  '<a  class="btn btn-lg btn-block registerbutton" href="/favorites" style="width:90%" >Favorites</a> <br/>'
        appt = ''
        fullname = ''
        photo = ''
        profilepage = ''
        number = 0
        if user:
            fullname = user.firstName+' '+user.lastName
            appt = '/userViewAppt'
            template_page = 'mainpage.html'
            number = getnumberofBarberAppt(getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass","")))
            if user.barber:
                
                photo = user.photo
                profilepage = '<a  class="btn btn-lg btn-primary btn-block registerbutton"type="button"   style="width:90%" href="/viewBarber/'+user.email+'">My Profile</a> </button><br/> <br/>'
                profilepage+=' <a  class="btn btn-lg btn-primary btn-block registerbutton"type="button" style="width:90%"  href="/setPhoto">Change Profile Picture</a><br/><br/>'
                profilepage+='<a  class="btn btn-lg btn-primary btn-block registerbutton"type="button" style="width:90%" href="/changeHours">Change Availability</a>'
                editRef = "editBarber"
                favoritebutton = ''
                template_page='mainpage.html'
                appt = '/barberViewAppt'
        if not(photo) or photo == '':
            photo = '<img class="img-rounded" src="/statics/silhouette.png" style="max-height: 100px; max-width: 100px;"  >  <br/>'
        else:
            photo = '<img class="img-rounded"  src="/viewPhoto/'+photo.__str__()+'" style=" max-height: 100px; max-width: 100px;"> <br/>'
        template_values = {
            "profilebutton": getProfileButton(user),
            "editref": editRef,
            "favoritebutton": favoritebutton,
            "appt": appt,
            "rewards": User.rewardpoints,
            "fullname": fullname,
            "photo": photo,
            "profilepage": profilepage,
            "numofappts": number
        }
        #THIS USED TO BE IN THE TEMPLATE VALUES(I think its on the wrong page): 
        template = JINJA_ENVIRONMENT.get_template(template_page)
        self.response.out.write(template.render(template_values))

class RegisterUser(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('registerUser.html')
        self.response.out.write(template.render(template_values))

class RegisterPage1(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('register_page1.html')
        self.response.out.write(template.render(template_values))

class RegisterBarber(webapp2.RequestHandler):
    def post(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect(''),
            "email": self.request.get('email'),
            "password": self.request.get('password'),
            "cpassword": self.request.get('cpassword'),
            "fname": self.request.get('fname'),
            "lname": self.request.get('lname')
        }
        template = JINJA_ENVIRONMENT.get_template('registerBarber.html')
        self.response.out.write(template.render(template_values))
    def get(self):
        self.redirect('/map')

class RegisterPage3(webapp2.RequestHandler):
    def post(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect(''),
            "email": self.request.get('email'),
            "password": self.request.get('password'),
            "cpassword": self.request.get('confirm'),
            "fname": self.request.get('firstName'),
            "occupation": self.request.get('occupation'),
            "shopName": self.request.get('shopName'),
            "aboutMe": self.request.get('aboutMe'),
            "phone": self.request.get('phone'),
            "street": self.request.get('street'),
            "city": self.request.get('city'),
            "state": self.request.get('state'),
            "lname": self.request.get('lastName')
        }
        template = JINJA_ENVIRONMENT.get_template('register_page3.html')
        self.response.out.write(template.render(template_values))
    def get(self):
        self.redirect('/map')


class AddUser(webapp2.RequestHandler):
    def post(self):
        userAddress = self.request.get('street')+','+self.request.get('city')+','+self.request.get('state')
        verifyCode = generateVerifyCode()
        message = "Thank you for creating an account at HeadWay!\n"
        message+="Click The following link to veryify your account!\n"
        message+="www.headwayapp.net/verify?username="+self.request.get('email')
        message+="&code="+verifyCode
        message+="&code="+verifyCode
        result = geocode(address=userAddress,sensor="false")
        user = User(id = self.request.get('email'),
                    password = hashlib.sha224(self.request.get('password')).hexdigest(),
                    firstName = self.request.get('firstName'),
                    lastName = self.request.get('lastName'),
                    email = self.request.get('email'),
                    phone = self.request.get('phone'),
                    state = self.request.get('state'),
                    street = self.request.get('street'),
                    city = self.request.get('city'),
                    location = ndb.GeoPt(result[0],result[1]),
                    verify = verifyCode,
                    favorite = '',
                    barber = False,
                    rewardpoints = 0)
        user.put()
        mail.send_mail("HeadWay <mamadouwann@gmail.com>",
                           "<"+self.request.get('email')+">",
                           "Verify Your  Account!",
                           message)
        self.redirect('/')


class AddBarber(webapp2.RequestHandler):
    def post(self):
        userAddress = self.request.get('street')+','+self.request.get('city')+','+self.request.get('state')
        verifyCode = generateVerifyCode()
        message = "Thank you for creating an account at HeadWay!\n"
        message+="Click The following link to veryify your account!\n"
        message+="www.headwayapp.net/verify?username="+self.request.get('email')
        message+="&code="+verifyCode
        message+="&code="+verifyCode
        result = geocode(address=userAddress,sensor="false")
        mail.send_mail("HeadWay <mamadouwann@gmail.com>",
                           "<"+self.request.get('email')+">",
                           "Verify Your  Account!",
                           message)
        #self.response.write('Services: '+self.request.get('serviceNum')+'<br />')
        floatList = [-1.0 for x in range(len(SERVICES))]
        for i in range(int(self.request.get('serviceNum'))):
            self.response.write(self.request.get('service'+str(i+1))+': ')
            for i2 in range(len(SERVICES)):
                if SERVICES[i2]==self.request.get('service'+str(i+1)):
                    floatList[i2] = float(self.request.get('price'+str(i+1)))
                    self.response.write(self.request.get('price'+str(i+1))+'<br />')
        user = User(id = self.request.get('email'),
                     verify = verifyCode,
                    password = hashlib.sha224(self.request.get('password')).hexdigest(),
                    firstName = self.request.get('firstName'),
                    lastName = self.request.get('lastName'),
                    shopName = self.request.get('shopName'),
                    email = self.request.get('email'),
                    phone = self.request.get('phone'),
                    state = self.request.get('state'),
                    street = self.request.get('street'),
                    city = self.request.get('city'),
                    aboutMe = self.request.get('aboutMe'),
                    services = "",
                    location = ndb.GeoPt(result[0],result[1]),
                    barber = True,
                    certified = False,
                    totalScore = 0,
                    totalReviews = 0,
                    currentRating = 0,
                    haircutsTrims = floatList[0],
                    shades = floatList[1],
                    tapers = floatList[2],
                    brushCuts = floatList[3],
                    designHaircuts = floatList[4],
                    clipperShaves = floatList[5],
                    razorShaves  = floatList[6],
                    edgeShapeUps  = floatList[7],
                    facialTrims  = floatList[8],
                    eyebrowArches = floatList[9],
                    neckTapers  = floatList[10],
                    shampoo = floatList[11],
                    conditionings  = floatList[12],
                    naturalDyes = floatList[13],
                    beardTrims  = floatList[14],
                    strengtheningTherapies = floatList[15],
                    relaxers = floatList[16],
                    twists = floatList[17],
                    braids = floatList[18],
                    curls  = floatList[19],
                    locs = floatList[20],
                    perms = floatList[21],
                    weaves = floatList[22],
                    extensions = floatList[23],
                    coloringHighlights = floatList[24],
                    updos = floatList[25],
                    formalHairstyles = floatList[26],
                    
                    occupation = self.request.get('occupation'))
        user.put()
        calendar = BarberCalendar(
            parent = user.key,
            sundayStart = getTime(self.request.get("1Start")),
            sundayEnd = getTime(self.request.get("1End")),
            mondayStart = getTime(self.request.get("2Start")),
            mondayEnd = getTime(self.request.get("2End")),
            tuesdayStart = getTime(self.request.get("3Start")),
            tuesdayEnd = getTime(self.request.get("3End")),
            wednesdayStart = getTime(self.request.get("4Start")),
            wednesdayEnd = getTime(self.request.get("4End")),
            thursdayStart = getTime(self.request.get("5Start")),
            thursdayEnd = getTime(self.request.get("5End")),
            fridayStart = getTime(self.request.get("6Start")),
            fridayEnd = getTime(self.request.get("6End")),
            saturdayStart = getTime(self.request.get("7Start")),
            saturdayEnd = getTime(self.request.get("7End")))
        calendar.put()
        mail.send_mail("HeadWay <mamadouwann@gmail.com>",
                           "<"+self.request.get('email')+">",
                           "Verify Your  Account!",
                           message)
        self.redirect('/')

def getTime(data):
    if data == '-1':
        return None
    hour = int(float(data))
    minute = "0"
    if float(data) != hour:
        minute = "30"
    return (datetime.strptime(str(hour)+" "+minute,"%H %M")).time()

def checkifcalendarexists(user):
    entity =BarberCalendar.query(ancestor=user.key)
    hasEntry = False
    for cal in entity:
        hasEntry = True
  
    return hasEntry
        
class LogIn(webapp2.RequestHandler):
    def post(self):
        username = self.request.get('username')
        password =self.request.get('password')
        
        user = getUser(username,password)
        if not(user):
            email = self.request.get('username')
            user = User.get_by_id(email)
            if not(user):
                self.redirect('/map')

            return
        if not(user.verify==""):
            self.redirect('/')
        if not(hashlib.sha224(password).hexdigest()==user.password):
            self.redirect('/map')
            return
        self.response.headers.add_header( "Set-Cookie","user=%s; path=/" % username.__str__())
        self.response.headers.add_header( "Set-Cookie","pass=%s; path=/" % self.request.get('password').__str__())
        if self.request.get('remember',default_value='no') != 'no':
            self.response.headers.add_header( "Set-Cookie","saveuser=%s; path=/" % username.__str__())
            self.response.headers.add_header( "Set-Cookie","savepass=%s; path=/" % self.request.get('password').__str__())
        else:
            self.response.headers.add_header( "Set-Cookie","saveuser=%s; path=/" % '')
            self.response.headers.add_header( "Set-Cookie","savepass=%s; path=/" % '')
        if(user.barber == True):
            if not(checkifcalendarexists(user)):
                newuser = User(id =user.email,
                               password = user.password,
                               firstName = user.firstName,
                               lastName = user.lastName,
                               email = user.email,
                               phone = user.phone,
                               state = user.state,
                               street = user.street,
                               city = user.city,
                               aboutMe = user.aboutMe,
                               services = user.services,
                               location =user.location,
                               favorite = user.favorite,
                               barber = True,
                               certified = user.certified,
                               totalScore = user.totalScore,
                               totalReviews = user.totalReviews,
                               currentRating = user.currentRating,
                               haircutsTrims = user.haircutsTrims,
                               shades = user.shades,
                               tapers = user.tapers,
                               brushCuts = user.brushCuts,
                               designHaircuts = user.designHaircuts,
                               clipperShaves = user.clipperShaves,
                               razorShaves  = user.razorShaves,
                               edgeShapeUps  = user.edgeShapeUps,
                               facialTrims  = user.facialTrims ,
                               eyebrowArches = user.eyebrowArches ,
                               neckTapers  = user.neckTapers,
                               shampoo =user.shampoo,
                               conditionings  = user.conditionings ,
                               naturalDyes = user.naturalDyes,
                               beardTrims  = user.beardTrims ,
                               strengtheningTherapies = user.strengtheningTherapies,
                               relaxers = user.relaxers,
                               twists = user.twists,
                               braids = user.braids,
                               curls  = user.curls,
                               locs = user.locs,
                               perms = user.perms,
                               weaves = user.weaves,
                               extensions = user.extensions,
                               coloringHighlights = user.coloringHighlights,
                               updos = user.updos,
                               formalHairstyles = user.formalHairstyles,
                               occupation = user.occupation)
                calendar = BarberCalendar(
                        parent = newuser.key,
                        sundayStart = time(9,0,0),
                        sundayEnd = time(9,0,0),
                        mondayStart = time(9,0,0),
                        mondayEnd = time(9,0,0),
                        tuesdayStart = time(9,0,0),
                        tuesdayEnd = time(9,0,0),
                        wednesdayStart = time(9,0,0),
                        wednesdayEnd =time(9,0,0),
                        thursdayStart = time(9,0,0),
                        thursdayEnd = time(9,0,0),
                        fridayStart = time(9,0,0),
                        fridayEnd = time(9,0,0),
                        saturdayStart = time(9,0,0),
                        saturdayEnd = time(9,0,0))
                userkey =user.key
                user.key.delete()
                newuser.key = userkey
                newuser.put()
                calendar.put()
        
            #else:
                #self.redirect('/search')
            #self.redirect('/search')
        self.redirect('/MainPage')
       

class LogOut(webapp2.RequestHandler):
    def get(self):
        self.response.headers.add_header( "Set-Cookie","user=%s; path=/" % "")
        self.response.headers.add_header( "Set-Cookie","pass=%s; path=/" % "")
        self.redirect('/map')


class SetPhoto(webapp2.RequestHandler):
    def get(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/map')
            return
        upload_url = blobstore.create_upload_url('/uploadPhoto')
        template_values = {
            "profilebutton": getProfileButton(user),
            'url': upload_url
        }
        template = JINJA_ENVIRONMENT.get_template('setPhoto.html')
        self.response.out.write(template.render(template_values))

    
class UploadPhoto(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/map')
            return
        old_key = user.photo
        if old_key:
            blobstore.delete(old_key)
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        upload = upload_files[0]
        user.photo = upload.key()
        user.put()
        self.redirect('/map')

class ViewPhotoHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)

def getScore(score,reviews):
    if reviews==0:
        return 0
    return int(score*100.0/reviews+.5)/100.0

def getStars(score, reviews):
    if reviews==0:
        return 0
    return int(score*2/reviews+.5)/2.0

def priceFormat(num):
    dollars = int(num)
    cents = int(num*100+.5)-dollars*100
    if cents < 10:
        return str(dollars)+".0"+str(cents)
    return str(dollars)+"."+str(cents)

def getBarberServices(barber):
    string = ""
    data = [barber.haircutsTrims,
            barber.shades,
            barber.tapers,
            barber.brushCuts,
            barber.designHaircuts,
            barber.clipperShaves,
            barber.razorShaves,
            barber.edgeShapeUps,
            barber.facialTrims,
            barber.eyebrowArches,
            barber.neckTapers,
            barber.shampoo,
            barber.conditionings,
            barber.naturalDyes,
            barber.beardTrims,
            barber.strengtheningTherapies,
            barber.relaxers,
            barber.twists,
            barber.braids,
            barber.curls,
            barber.locs,
            barber.perms,
            barber.weaves,
            barber.extensions,
            barber.coloringHighlights,
            barber.updos,
            barber.formalHairstyles]
    for i in range(len(SERVICES)):
        if data[i] >= 0:
            string+='<br />'+SERVICES[i]+': $'+priceFormat(data[i])
    if string=="":
        return string
    string = '<div data-role="collapsible-set"><div data-role="collapsible"><h3 style="color:white">Offered Services</h3>'+string[6:]

    #need to make the string return the service * .01 percent
    
    return string+'</div></div>'

def certifiedbutton(barber):
    if (barber.certified == True):
        return  "Premium User"
    if (barber.certified == False):
        return '<a href="/" rel="external" data-role="button">Get A Premium Account</a>'

def getcertified(barber):
    if (barber.certified == True):
        if barber.occupation == "Hairdresser":
            return "Premium Hairdresser"
        else:
            return "Premium Barber"
    else:
        return "<br/>"
def getApptButton(user,barber_key):
    if not(user):
        return ""
    if user.barber:
        return ""
    return '<a  class="btn btn-lg btn-block registerbutton" type="button" style="width:90%" href="/MakeAppt/'+barber_key.email+'" data-role="button">Make an Appointment</a>'

    
def getFavoriteButton(user,barber_key):
    if not(user):
        return ""
    if user.barber:
        return ""
    size = '"24"'
    favs = user.favorite.split(";")
    for fav in favs:
        if fav == barber_key:
            return '<img src="../statics/favicon2.png" width='+size+' height='+size+'>'
#    return string+": "+str(len(favs))
    return 'Click star to add favorite<img onclick="favorite();" style="cursor: pointer;" src="../statics/favicon.png" width='+size+' height='+size+'>  '

class ViewBarber(webapp2.RequestHandler):
    def get(self, barber_key):
        flagbutton = ''
        flag =""
        ceritify="This Barber is not Certified"
        if not(barber_key):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber =getUser(barber_key,"nopoint")
        
        if not(barber):
            self.redirect('/')
            return
        if not(barber.barber):
            self.redirect('/')
            return
        review = "<br/> <a href='/MainPage'> SIGN UP/LOGIN TO REVIEW THIS PROFILE</a>"
        if user:
            flag = getFlag(user)
            if user.barber:
                review = ""
            else:
                review = getReviewForm(barber.email)
                if not flag:
                    flagbutton ='<form method="post" action="/flag/'+barber_key+'"><button class="btn registerbutton" style="margin:0;"> Flag  inappropriate </button></form>'
                if flag:
                    flagbutton = 'You have flagged this user'
        numReviews = barber.totalReviews
        rating = "No Rating"
        numstars = 0
        if numReviews>0:
            rating = str(getScore(barber.totalScore,numReviews))+" out of "+str(numReviews)+" review(s)."
            numstars = str(getStars(barber.totalScore,numReviews))
        photo = '<img    src="/viewPhoto/'+barber.photo.__str__()+'" class="img-circle"  style=" position:absolute; width:42%; top:9%;left:29%; "/>'
        if barber.certified == True:
            ceritify = "This Barber is Ceritified"
        if (barber.photo == '' or not(barber.photo)):
            photo = '<img  class="img-circle"  style=" position:absolute; width:42%; top:9%;left:29%; "src="/statics/silhouette.png" " />'
        template_values = {
            "typeofprof":typeofprof(barber.occupation),
            "profilebutton": getProfileButton(user),
            'photo': photo,
            'flagbutton':flagbutton,
            'rating': rating,
            'rateme': review,
            'fullName': barber.firstName+" "+barber.lastName,
            'services': getBarberServices(barber),
            'reviews': getReviews(barber),
            'shop': barber.shopName,
            'certified':getcertified(barber),
            'barberusername':barber_key,
            'starnum': numstars,
            'appt': getApptButton(user,barber),
            'favButton': getFavoriteButton(user,barber_key),
            'barberkey': barber_key,
            'tel': "tel:"+barber.phone,
            'phone':barber.phone,
            'mailto':"mailto:"+barber.email,
            'email': barber.email,
            'address': barber.street+', '+barber.city+', '+barber.state,
            'aboutMe': barber.aboutMe,
            'hours': getAvailability(barber),
            'certify':ceritify
        }
        template = JINJA_ENVIRONMENT.get_template('Viewbarber.html')
        self.response.out.write(template.render(template_values))


def getReviews(barber):
    string = ""
    reviews = Review.query(ancestor=barber.key).order(Review.date, -Review.date)
    for review in reviews:
        user = User.get_by_id(review.user)
        getUser(user.email,"nopoint")

        string+="<h4 style='color:white!important;'>"+user.firstName+" "+user.lastName+" - "+str(review.rating)+"/5 <span style='font-weight: normal; color:white!important; font-size: 12px;'>"+formatDateTime2(review.date)+"</span></h4>"
        string+=" <p class='form-control' style='text-indent: 25px; color:black!important;'>Comment: "+review.comments+"</p>"
    string ='<br/><button class="btn btn-primary btn-lg registerbutotn" style="margin:0" data-toggle="collapse" data-target="#mycomment" ><span class="glyphicon glyphicon-comment"> Reviews</span> </button> <br/><div class="collapse" data-role="collapsible" id="mycomment">'+string+'</div>'
    return string+''

def getAvailability(barber):
    string ='<div data-role="collapsible-set"><div  style=" color:white!important;" data-role="collapsible" ><h3>Availability</h3>'
    calendarList = (BarberCalendar.query(ancestor=barber.key))
    calendar = ''
    for c in calendarList:
        calendar = c
    times = [['Sunday',calendar.sundayStart,calendar.sundayEnd],
             ['Monday',calendar.mondayStart,calendar.mondayEnd],
             ['Tuesday',calendar.tuesdayStart,calendar.tuesdayEnd],
             ['Wednesday',calendar.wednesdayStart,calendar.wednesdayEnd],
             ['Thursday',calendar.thursdayStart,calendar.thursdayEnd],
             ['Friday',calendar.fridayStart,calendar.fridayEnd],
             ['Saturday',calendar.saturdayStart,calendar.saturdayEnd]]
    string+='<table width="70%">'
    for day in times:
        if day[1] and day[2]:
            string+='<tr> <th>'+day[0]+'</th><td>'+day[1].strftime("%I:%M %p")+'</td><td> to </td><td>'  +day[2].strftime("%I:%M %p")+'</td></tr>'
        else:
            string+='<tr><th>'+day[0]+'</th><td colspan=2>Closed</td></tr>'
    return string+'</table></div></div>'

def getReviewForm(barber_key):
    string = '<form  method="post" action="/reviewBarber/'+barber_key+'">'
    string+='<label for="rating">Rating: </label>'
    string+='<select   class="form-control" id="rating" name="rating"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select>'
    string+='<br /><textarea   class="form-control" id="comments" name="comments" rows="5" cols="80"></textarea>'
    string+='<br /><input  class="form-control"  type="submit" value="Send Review" />'
    string ='<div style="color:white!important;"data-role="collapsible-set"><div data-role="collapsible"><h3>Rate me</h3>'+string
    return string+'</form></div></div>'

class ReviewBarber(webapp2.RequestHandler):
    def post(self, barber_key):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber =getUser(barber_key,"nopoint")

        if not(user):
            self.redirect('/')
            return
        if user.barber:
            self.redirect('/')
            return
       
        if not(barber):
            self.redirect('/'+barber.email)
            return
        if not(barber.barber):
            self.redirect('/')
            return
        existing = Review.query(ancestor=barber.key).filter(ndb.GenericProperty("user")==user.key.string_id()).fetch()
        if len(existing)>0:
            review = existing[0]
            oldScore = review.rating
            newScore = int(self.request.get('rating'))
            barber.totalScore+=newScore-oldScore
            barber.currentRating = getScore(barber.totalScore,barber.totalReviews)
            barber.put()
            review.rating = newScore
            review.comments = self.request.get('comments')
            review.date = datetime.now()
            review.put()
            self.redirect('/viewBarber/'+barber_key)
            return
        review = Review(parent = barber.key,
                        user = user.email,
                        rating = int(self.request.get('rating')),
                        comments = self.request.get('comments'),
                        date = datetime.now())
        review.put()
        barber.totalScore+=review.rating
        barber.totalReviews+=1
        barber.currentRating = getScore(barber.totalScore,barber.totalReviews)
        barber.put()
        self.redirect('/viewBarber/'+barber_key)

class Register(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user)
        }
        template = JINJA_ENVIRONMENT.get_template('register.html')
        self.response.out.write(template.render(template_values))

def getBarberData(barber,miles):
    string =""
    photo ="statics/silhouette.png"
    numStars = 0
    if barber.totalScore>0:
        numStars = (int)(barber.totalScore*2.0/barber.totalReviews+.5)
        numStars = numStars/2.0
    if barber.photo:
        photo ='/viewPhoto/'+ str(barber.photo)
        
    string = ' {"type":"Feature","geometry":{ "type":"Point","coordinates":['+str(barber.location.lon)+','+str(barber.location.lat)+  ']},'
    string +='"properties":{"user":0.0 ,"marker-symbol": "star","marker-color":"#4E6E80","marker-size": "large","mystars":'+str(getStars(barber.totalScore,barber.totalReviews))+',"username":"'+str(barber.email)+'","title":"'+barber.shopName+'","starnum":'+str(numStars)+',"image":"'+photo+'"}'
   

   # string = '{"type":"Feature",'
   # string +='"geometry":{ "type":"Point","coordinates":['+str(barber.location.lon)+','+str(barber.location.lat)+ "]},"
    #string +='"properties":{"title":'+barber.shopName+',"barbername":'+barber.firstName+' '+barber.lastName+', "starnum":'+str(numStars)+', "distance":'+str(miles)+',"rating":'+str(barber.currentRating)+', "photo":'+photo+', "user":0, "distance":50,"description":"","marker-color":"#ff8888"}'
    
    #string+='{ "latitude":'+str(barber.location.lat)+', "longitude":'+str(barber.location.lon)
   # string+=', "title":"'+barber.email+'", "barbername":"'+barber.firstName+' '+barber.lastName+'", '
    #string+='"description":"'+barber.shopName+'", "starnum":'+str(numStars)+', '
    ##string+='"rating":"'+str(barber.currentRating)+'", '
    #string+='"user":0, "distance":'+str(miles)+', '
    
    return string

class Search(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        address = "Enter Your Address"
        if user:
            address = user.street+", "+user.city+", "+user.state
        template_values = {
            "profilebutton": getProfileButton(user),
            "address": address
        }
        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.out.write(template.render(template_values))
        

def getModifyServiceData(barber):
    num = 1
    string = ""
    data = [barber.haircutsTrims,
            barber.shades,
            barber.tapers,
            barber.brushCuts,
            barber.designHaircuts,
            barber.clipperShaves,
            barber.razorShaves,
            barber.edgeShapeUps,
            barber.facialTrims,
            barber.eyebrowArches,
            barber.neckTapers,
            barber.shampoo,
            barber.conditionings,
            barber.naturalDyes,
            barber.beardTrims,
            barber.strengtheningTherapies,
            barber.relaxers,
            barber.twists,
            barber.braids,
            barber.curls,
            barber.locs,
            barber.perms,
            barber.weaves,
            barber.extensions,
            barber.coloringHighlights,
            barber.updos,
            barber.formalHairstyles]
    for i in range(len(SERVICES)):
        if data[i] >= 0:
            #string+='<br />'+SERVICES[i]+': $'+priceFormat(data[i])
            string+='<center><div data-role="fieldcontain"><label for="service'+str(num)+'">Service #'+str(num)
            string+=': </label><select class="form-control" name="service'+str(num)+'" id="service'+str(num)+'">'
            for i2 in range(len(SERVICES)):
                if i==i2:
                    string+='<option selected>'+SERVICES[i2]+'</option>'
                else:
                    string+='<option>'+SERVICES[i2]+'</option>'
            
            string+='</select></div><div data-role="fieldcontain"><label for="price'+str(num)+'"> Price: </label>'
            string+='<input class="form-control required number" name="price'+str(num)+'" id="price'+str(num)+'" value="'
            string+=priceFormat(data[i])+'"/></div> <br/> <br/><button  class="form-control registerbutton" type="button" onClick="removeService('+str(num)+');">Remove</button><br /><br /></center>'
            num+=1
    if string=="":
        return [string,num,num-1]
    return [string,num,num-1]
    

class EditBarber(webapp2.RequestHandler):
    def get(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/map')
            return
        data = getModifyServiceData(user)
        template_values = {
            "profilebutton": getProfileButton(user),
            "firstName": user.firstName,
            "lastName": user.lastName,
            "shopName": user.shopName,
            "email": user.email,
            "phone": user.phone,
            "street": user.street,
            "city": user.city,
            "states": getStateSelect(user.state),
            "serviceNum": data[1],
            "services": data[0],
            "serviceInput": data[2],
            "certified":certifiedbutton(user),
            "aboutMe": user.aboutMe
        }
        template = JINJA_ENVIRONMENT.get_template('editBarber.html')
        self.response.out.write(template.render(template_values))



class Map(webapp2.RequestHandler):
    def post(self):
        photo =''
        number =''
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        location = self.request.get("location")
        registerbutton ='<button class="btn-lg btn-block dropdown-toggle registerbutton"   aria-haspopup="true" aria-expanded="false" data-toggle="dropdown"  style=" font-family:webfont; padding-top:-4px" >Register For Free</button>'
        numReviews =0
        numstars = 0
        if numReviews>0:
            rating = str(getScore(user.totalScore,numReviews))+" out of "+str(numReviews)+" review(s)."
            numstars = str(getStars(user.totalScore,numReviews))
        if user:
            number = getnumberofBarberAppt(user)
            registerbutton = ''
            photo = user.photo
            if user.barber:
                numReviews = user.totalReviews
        string = getJsonString(self.request.get("location"),
                               float(self.request.get('range')),
                               float(self.request.get("rating")))
        if not(photo) or photo == '':
            photo = '<img class="img-rounded" src="/statics/silhouette.png" style="max-height: 100px; max-width: 100px;"  >  <br/>'
        else:
            photo = '<img class="img-rounded"  src="/viewPhoto/'+photo.__str__()+'" style=" max-height: 100px; max-width: 100px;"> <br/>'
        template_values = {
            "jsonobject": string,
            "sidemenu" : mapmenu(user),
            "starnum":numstars,
            "profilebutton": getProfileButton(user),
            "Registerbutton":registerbutton
        }
        template = JINJA_ENVIRONMENT.get_template('map.html')
        self.response.out.write(template.render(template_values))
    def get(self):
        self.redirect('/MainPage')
def mapmenu(user):
    string=""
    number =''
    photo = ''
    if not(photo) or photo == '':
        photo = '<img class="img-rounded" src="/statics/silhouette.png" style="max-height: 100px; max-width: 100px;"  >  <br/>'
    elif photo:
        photo = '<img class="img-rounded"  src="/viewPhoto/'+photo.__str__()+'" style=" max-height: 100px; max-width: 100px;"> <br/>'
    if user:
        photo =user.photo
        number = getnumberofBarberAppt(user)
        string ='<li >Welcome back, '+user.firstName + user.lastName +'</li><li>Number of appointments: '+number.__str__()+' </li><li style="border-bottom:dashed; border-color:rgb(57,57,57); background:rgb(78,110,128);"><a href="/editUser" style="color:white;font-family:web-font; font-size:1.2em">Edit my profile</a></li><li style="border-bottom:dashed; border-color:rgb(57,57,57);background:rgb(78,110,128);"><a href="/userViewAppt" style="color:white;font-family:web-font; font-size:1.2em">My Appointments</a> </li><li style="border-bottom:dashed; border-color:rgb(57,57,57);background:rgb(78,110,128);"><a href="/favorites" style="color:white;font-family:web-font; font-size:1.2em">View My favorites</a></li><li style="border-bottom:dashed; border-color:rgb(57,57,57);background:rgb(78,110,128);"><a href="/logout" style="color:white;font-family:web-font; font-size:1.2em">Logout</a></li>'
        if user.barber:
         
            string ='<li>Welcome back, '+user.firstName + user.lastName +'</li><li><img class="img-rounded"  src="/viewPhoto/'+photo.__str__()+'" style=" max-height: 60px; max-width: 60px;"> <br/></li><li>Number of appointments: '+number.__str__()+' </li><li><a href="/changeHours" id="iconbox"  class="btn registerbutton" style="width:60%; background:blue"><span style="display:block"><img src="statics/Clock.png" style="width:32px"/> <h5>Update Hours</h5></span></a></li> <br/> <li> <a href="/setPhoto" id="iconbox"  class="btn registerbutton" style="width:60%; background:blue"><span style="display:block"><img src="statics/gallery.png"/> <h5>Change Avatar</h5></li></span></a></li> <br/> <li> <a href="/editBarber" id="iconbox"  class="btn registerbutton" style="width:60%;"><span style="display:block"><img src="statics/portfolio.png"/> <h5>Edit Profile</h5></li></span></a></li> <br/> <li> <a href="/barberViewAppt"  id="iconbox"  class="btn registerbutton" style="width:60%;"><span style="display:block"><img src="statics/appt.png" style="width:32px" /> <h5>My Appointments</h5></li></span></a></li> <br/> <li style="border-bottom:dashed; border-color:rgb(57,57,57);background:rgb(78,110,128);"><a href="/logout" style="color:white;font-family:web-font; font-size:1.2em">Logout</a></li>'
            if user.wepayuid =='':
                string+='<li style="border-bottom:dashed; border-color:rgb(57,57,57);background:rgb(78,110,128);"><a  style="background-color=rgb(57,57,57);width:90%;" id="start_oauth2">Add payment system</a></li>'
    if not user:
        string ='<br/><br/><br/>  <br/><br/> <br/><br/><a href="/MainPage" id="iconbox"  class="btn registerbutton" data-target="/MainPage" style="width:60%; background:blue"><span style="display:block"><img src="statics/login.png"/> <h3>LOGIN</h3></span></a> <br/><br/> <br/><button id="iconbox"   role="button" aria-haspopup="true" aria-expanded="false" class="btn registerbutton dropdown-toggle"  data-toggle="dropdown" style="width:60%;"><span style="display:block"><img src="statics/sign-up.png"/> <h3>SIGN UP</h3></span></button><br/> <br/> <br/> <a href="/about" id="iconbox"   role="button" aria-haspopup="true" aria-expanded="false" class="btn registerbutton dropdown-toggle" style="width:60%;"><span  class="glyphicon glyphicon-info-sign" style=" display:block"> <h3 style="font-family:webfont!important;">INFO</h3></span></a>  <ul class="dropdown-menu"><li class="active btn-xl" style=""><a style=""href="/registerUser" rel="external" data-iconpos="center" data-icon="search"><span class="glyphicon glyphicon-search"></span>As a user</a></li><li class="active btn-xl" style=""><a style=""href="/registerPage1" rel="external" data-iconpos="center" data-icon="search"><span class="glyphicon glyphicon-search"></span>As a Hair Dresser</a></li></ul>'
    return string
        
class EditUser(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        if user.barber:
            self.redirect('/editBarber')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "phone": user.phone,
            "street": user.street,
            "city": user.city,
            "states": getStateSelect(user.state)
        }
        template = JINJA_ENVIRONMENT.get_template('editUser.html')
        self.response.out.write(template.render(template_values))

class SaveUser(webapp2.RequestHandler):
    def post(self):
        
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        if user.barber:
            self.redirect('/')
            return
        userAddress = self.request.get('street')+','+self.request.get('city')+','+self.request.get('state')
        result = geocode(address=userAddress,sensor="false")
        user.location = ndb.GeoPt(result[0],result[1])
        user.firstName = self.request.get("firstName")
        user.lastName = self.request.get("lastName")
        user.email = self.request.get("email")
        user.phone = self.request.get("phone")
        user.street = self.request.get("street")
        user.city = self.request.get("city")
        user.state = self.request.get("state")
        user.put()
        self.redirect("/map")

class SaveBarber(webapp2.RequestHandler):
    def post(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        floatList = [-1.0 for x in range(len(SERVICES))]
        for i in range(int(self.request.get('serviceNum'))):
            for i2 in range(len(SERVICES)):
                if SERVICES[i2]==self.request.get('service'+str(i+1)):
                    floatList[i2] = float(self.request.get('price'+str(i+1)))
        userAddress = self.request.get('street')+','+self.request.get('city')+','+self.request.get('state')
        result = geocode(address=userAddress,sensor="false")
        user.location = ndb.GeoPt(result[0],result[1])
        user.firstName = self.request.get("firstName")
        user.lastName = self.request.get("lastName")
        user.shopName = self.request.get("shopName")
        user.email = user.email
        user.phone = self.request.get("phone")
        user.street = self.request.get("street")
        user.city = self.request.get("city")
        user.state = self.request.get("state")
        user.aboutMe = self.request.get("aboutMe")
        user.haircutsTrims = floatList[0]
        user.shades = floatList[1]
        user.tapers = floatList[2]
        user.brushCuts = floatList[3]
        user.designHaircuts = floatList[4]
        user.clipperShaves = floatList[5]
        user.razorShaves = floatList[6]
        user.edgeShapeUps = floatList[7]
        user.facialTrims = floatList[8]
        user.eyebrowArches = floatList[9]
        user.neckTapers = floatList[10]
        user.shampoo = floatList[11]
        user.conditionings = floatList[12]
        user.naturalDyes = floatList[13]
        user.beardTrims = floatList[14]
        user.strengtheningTherapies = floatList[15]
        user.relaxers = floatList[16]
        user.twists = floatList[17]
        user.braids = floatList[18]
        user.curls = floatList[19]
        user.locs = floatList[20]
        user.perms = floatList[21]
        user.weaves = floatList[22]
        user.extensions = floatList[23]
        user.coloringHighlights = floatList[24]
        user.updos = floatList[25]
        user.formalHairstyles = floatList[26]
        user.put()
        self.redirect("/viewBarber/"+user.email)



class Calendar(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user)
        }
        template = JINJA_ENVIRONMENT.get_template('calendar.html')
        self.response.out.write(template.render(template_values))

class Database(webapp2.RequestHandler):
    def __init__(self, *args, **kwargs):
        webapp2.RequestHandler.__init__(self, *args, **kwargs)
        self.methods = RPCMethods()
    def get(self):
        func = None
        action = self.request.get('action')
        if action:
            if action[0]=='_':
                self.error(403)
                return
            else:
                func = getattr(self.methods,action, None)
        if not(func):
            self.error(403)
            return
        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args += (val,)
            else:
                break
        result = func(*args)
        self.response.out.write(result)

def getBarberString(barber, miles):
    string = '<div class="ui-bar-c ui-corner-all ui-shadow" style="padding:1em;">'
    string+='<table width="100%" border="0"><tr><th width="38%" scope="col">'
    href = '<a href="/viewBarber/'+barber.key.integer_id().__str__()+'">'
    string+=href
    if barber.photo=="" or not(barber.photo):
        string+='<img src="/statics/silhouette.png" width="100px" height="100px" />'
    else:
        string+='<img src="/viewPhoto/'+str(barber.photo)+'" style="max-height: 100px; max-width: 100px;" />'
    string+='</a></th><th width="62%" scope="col"><table width="100%" border="0"><tr>'
    string+='<th scope="col">'+href+barber.firstName+" "+barber.lastName+'</a></th></tr><tr>'
    string+='<th scope="row"><center><span class="stars s-'+str(getStars(barber.totalScore,barber.totalReviews))+'" data-default="'+str(getStars(barber.totalScore,barber.totalReviews))+'" style="text-align:right">0 stars</span></center>'
    string+=str(barber.currentRating)+' out of '+str(barber.totalReviews)+' review(s)</th></tr><tr>'
    string+='<th scope="row">'+str(((int)(miles*10+.5))/10.0)+' miles away</th></tr><tr>'
    string+='<th  style="color:white;" scope="row">'+barber.services+'</th></tr></table></th></tr></table></div>'
    return string

def getJsonString(myLocation,minRange,minRating):
    string =""
    length = len(myLocation)
    defaultlocation =[40.5788246,-105.0977983]
    if length>1:
        if myLocation[0] == "[":
            string = (myLocation)[1:-1]
            strings = string.split(",")
            myLocation = [float(strings[0]),float(strings[1])]
      ##  else:
           ## myLocation = geocode(address=myLocation,sensor="false")
    else:
        myLocation =defaultlocation
    string = '[ {"type":"Feature","geometry":{ "type":"Point","coordinates":['+str(myLocation[1])+ ','+ str(myLocation[0]) + ']},'
    string +='"properties":{"title":"My Location", "username":"","user":1.0,"starnum":0.0,"rating":0.0,"image":"","distance":50.0,"barbername":"","marker-symbol": "circle","marker-color":"#4E6E80"}'
   
    barbers = User.query(User.barber == True)
    barbers = barbers.filter(User.currentRating >= 0)
    for barber in barbers:
        miles = getDist(myLocation,[barber.location.lat,barber.location.lon])
        if miles <= 50:
            string+=' },'+getBarberData(barber,miles)
    string+=' } ]'


    logging.info(string)
    return string

class RPCMethods():
    def getListData(self, *args):
        try:
            myLocation = ""
            if (args[0])[0]=="[":
                string = (args[0])[1:-1]
                strings = string.split(",")
                myLocation = [float(strings[0]),float(strings[1])]
            else:
                myLocation = geocode(address=args[0],sensor="false")
            string = ""
            barbers = User.query(User.barber == True)
            barbers = barbers.filter(User.currentRating >= float(args[1]))
            if args[3] == "false":
                barbers = barbers.filter(User.occupation == 'Hairdresser')
            if args[4] == "false":
                barbers = barbers.filter(User.occupation == 'Barber')
            barbers = barbers.order(-User.currentRating, User.currentRating)
            for barber in barbers:
                miles = getDist(myLocation,[barber.location.lat,barber.location.lon])
                if miles <= float(args[2]):
                    string+=getBarberString(barber,miles)
            if string=="":
                return "Your search has not returned any results.<br />Try changing your search criteria."
            return string
        except:
            return "Try reentering your address"
    def favorite(self, *args):
        user = User.key.integer_id(args[0])
        barber = User.key.integer_id(args[1])
        user.favorite = args[0]
        user.put()
    def getStreetAddress(self, *args):
        url = GEOCODE_BASE_URL + '?latlng='+args[0]+"&sensor=false"
        result = simplejson.load(urllib.urlopen(url))
        try:
            result = result['results'][0]
            result = result['formatted_address']
            return result
        except:
            return '['+args[0]+']'
    def usernameTaken(self, *args):
        user = User.key.integer_id(args[0])
        if user:
            return "True"
        return "False"
    def wrongPassword(self, *args):
        user = User.key.integer_id(args[0])
        if not(user):
            return "False"
        if user.password == hashlib.sha224(args[1]).hexdigest():
            return "False"
        return "True"

class howtocertify(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('howtocertify.html')
        self.response.out.write(template.render(template_values))

class About(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('about.html')
        self.response.out.write(template.render(template_values))

class Trying(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('trying.html')
        self.response.out.write(template.render(template_values))
class License(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user", ""), self.request.cookies.get("pass", ""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('agreement.html')
        self.response.out.write(template.render(template_values))
class Privacy(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('privacy.html')
        self.response.out.write(template.render(template_values))


class homepage(webapp2.RequestHandler):
    def get(self):
       
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('/landing.html')
        self.response.out.write(template.render(template_values))
class facebooklogin(webapp2.RequestHandler):
     def post(self):
        username = self.request.get('username')
        user = getUser(username,'hahahah')
        if not(user):
            email = self.request.get('username')
            user = User.get_by_id(email)
            if not(user):
                self.redirect('/map')

            return
        self.response.headers.add_header( "Set-Cookie","user=%s; path=/" % username.__str__())
        self.response.headers.add_header( "Set-Cookie","pass=%s; path=/" % self.request.get('password').__str__())
        if self.request.get('remember',default_value='no') != 'no':
            self.response.headers.add_header( "Set-Cookie","saveuser=%s; path=/" % username.__str__())
            self.response.headers.add_header( "Set-Cookie","savepass=%s; path=/" % self.request.get('password').__str__())
        else:
            self.response.headers.add_header( "Set-Cookie","saveuser=%s; path=/" % '')
            self.response.headers.add_header( "Set-Cookie","savepass=%s; path=/" % '')
        if(user.barber == True):
            if not(checkifcalendarexists(user)):
                newuser = User(id =user.email,
                               password = user.password,
                               firstName = user.firstName,
                               lastName = user.lastName,
                               email = user.email,
                               phone = user.phone,
                               state = user.state,
                               street = user.street,
                               city = user.city,
                               aboutMe = user.aboutMe,
                               services = user.services,
                               location =user.location,
                               favorite = user.favorite,
                               barber = True,
                               certified = user.certified,
                               totalScore = user.totalScore,
                               totalReviews = user.totalReviews,
                               currentRating = user.currentRating,
                               haircutsTrims = user.haircutsTrims,
                               shades = user.shades,
                               tapers = user.tapers,
                               brushCuts = user.brushCuts,
                               designHaircuts = user.designHaircuts,
                               clipperShaves = user.clipperShaves,
                               razorShaves  = user.razorShaves,
                               edgeShapeUps  = user.edgeShapeUps,
                               facialTrims  = user.facialTrims ,
                               eyebrowArches = user.eyebrowArches ,
                               neckTapers  = user.neckTapers,
                               shampoo =user.shampoo,
                               conditionings  = user.conditionings ,
                               naturalDyes = user.naturalDyes,
                               beardTrims  = user.beardTrims ,
                               strengtheningTherapies = user.strengtheningTherapies,
                               relaxers = user.relaxers,
                               twists = user.twists,
                               braids = user.braids,
                               curls  = user.curls,
                               locs = user.locs,
                               perms = user.perms,
                               weaves = user.weaves,
                               extensions = user.extensions,
                               coloringHighlights = user.coloringHighlights,
                               updos = user.updos,
                               formalHairstyles = user.formalHairstyles,
                               occupation = user.occupation)
                calendar = BarberCalendar(
                        parent = newuser.key,
                        sundayStart = time(9,0,0),
                        sundayEnd = time(9,0,0),
                        mondayStart = time(9,0,0),
                        mondayEnd = time(9,0,0),
                        tuesdayStart = time(9,0,0),
                        tuesdayEnd = time(9,0,0),
                        wednesdayStart = time(9,0,0),
                        wednesdayEnd =time(9,0,0),
                        thursdayStart = time(9,0,0),
                        thursdayEnd = time(9,0,0),
                        fridayStart = time(9,0,0),
                        fridayEnd = time(9,0,0),
                        saturdayStart = time(9,0,0),
                        saturdayEnd = time(9,0,0))
                userkey =user.key
                user.key.delete()
                newuser.key = userkey
                newuser.put()
                calendar.put()
        
            #else:
                #self.redirect('/search')
            #self.redirect('/search')
        self.redirect('/map')
class facebook(webapp2.RequestHandler):
    def get(self):
       
        template_values = {

        }
        template = JINJA_ENVIRONMENT.get_template('/facebook.html')
        self.response.out.write(template.render(template_values))
class BarberProfilepage(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('BarberProfile.html')
        self.response.out.write(template.render(template_values))
        
class makeappt(webapp2.RequestHandler):
    def get(self, barber_key):
        
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber = User.get_by_id(barber_key)
        if not(user):
            self.redirect('/viewBarber/'+barber_key)
            return
        if user.barber:
            self.redirect('/viewBarber/'+barber_key)
        
        if not(barber):
            self.redirect('/')
            return
        if not(barber.barber):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect(''),
            "services": barberServicePickList(barber),
            "barberkey": barber_key
        }
        template = JINJA_ENVIRONMENT.get_template('makeappt.html')
        self.response.out.write(template.render(template_values))

def barberServicePickList(barber):
    string = ""
    string2 = "<script>var prices=["
    data = [barber.haircutsTrims,
            barber.shades,
            barber.tapers,
            barber.brushCuts,
            barber.designHaircuts,
            barber.clipperShaves,
            barber.razorShaves,
            barber.edgeShapeUps,
            barber.facialTrims,
            barber.eyebrowArches,
            barber.neckTapers,
            barber.shampoo,
            barber.conditionings,
            barber.naturalDyes,
            barber.beardTrims,
            barber.strengtheningTherapies,
            barber.relaxers,
            barber.twists,
            barber.braids,
            barber.curls,
            barber.locs,
            barber.perms,
            barber.weaves,
            barber.extensions,
            barber.coloringHighlights,
            barber.updos,
            barber.formalHairstyles]
    for i in range(len(SERVICES)):
        if data[i] >=0:
            string+='<input type="checkbox" style="color:white!important;" onclick="toggleService('+str(i)+');" name="service'+str(i)+'" id="service'+str(i)
            string+='" class="custom" value="" /><label  style="color:white !important;"for="service'+str(i)+'">'+SERVICES[i]
            string+=': $'+priceFormat(data[i])+'</label>'
            string2+=str(data[i])
        else:
            string2+='0'
        if i<26:
            string2+=','
    return string+'\n'+string2+'];</script>'

class SaveAppt(webapp2.RequestHandler):
    def post(self, barber_key):
        if not(barber_key):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber = User.get_by_id(barber_key)
        if not(barber):
            self.redirect('/')
            return
        if not(barber.barber):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        serviceList = ""
        for i in range(27):
            data = self.request.get("service"+str(i),default_value="no")
            if data != 'no':
                if len(serviceList)>0:
                    serviceList+=","
                serviceList+=SERVICES[i]
        dateString = self.request.get('mydate')
        appt = Appointment(parent = barber.key,
                           user = user.email,
                           startTime = datetime.strptime(dateString, '%Y-%m-%d-%H:%M'),
                           time = 0,
                           status = 0,
                           comment = self.request.get('comment'),
                           services = serviceList,
                           price = 0.0)
        appt.put()
        mail.send_mail("HeadWay <mamadouwann@gmail.com>", #TODO CHANGE THIS EMAIL ADDRESS
                        barber.firstName+" "+barber.lastName+" <"+barber.email+">",
                        "New Appointment",
                        user.firstName+" "+user.lastName+" has requested an appointment. Log on to Head Way to review it!")
        mail.send_mail("HeadWay <mamadouwann@gmail.com>", #TODO CHANGE THIS EMAIL ADDRESS
                        "Your Appointment with"+barber.firstName+" "+barber.lastName+" <"+user.email+">",
                        " Your new Appointment With",
                        "Your appointment for "+ dateString+" has been requested with "+barber.firstName+" "+barber.lastName+" Log on to Head Way to edit it!")
        self.redirect('/viewBarber/'+barber_key)

class FavBarber(webapp2.RequestHandler):
    def get(self, barber_key):
        if not(barber_key):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber = User.get_by_id(barber_key)
        if not(barber):
            self.redirect('/')
            return
        if not(barber.barber):
            self.redirect('/')
            return
        if not(user):
            self.redirect('/viewBarber/'+barber_key)
            return
        if user.barber:
            self.redirect('/viewBarber/'+barber_key)
            return
        if user.favorite == "":
            user.favorite = barber_key
            user.put()
            self.redirect('/viewBarber/'+barber_key)
        favs = user.favorite.split(';')
        for fav in favs:
            if fav == barber_key:
                self.redirect('/viewBarber/'+barber_key)
                return
        user.favorite = user.favorite +';'+barber_key
        user.put()
        self.redirect('/viewBarber/'+barber_key)

class Favorites(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        if user.barber:
            self.redirect('/')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "favorites": getAllFavorites(user)
        }
        template = JINJA_ENVIRONMENT.get_template('favorites.html')
        self.response.out.write(template.render(template_values))

class UserViewAppt(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        if user.barber:
            self.redirect('/')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "appts": getUserApptList(user)
        }
        template = JINJA_ENVIRONMENT.get_template('userViewAppt.html')
        self.response.out.write(template.render(template_values))

class BarberViewAppt(webapp2.RequestHandler):
    def get(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "appts": getBarberApptList(user)
        }
        template = JINJA_ENVIRONMENT.get_template('barberviewappt.html')
        self.response.out.write(template.render(template_values))

class BarberRewardAppt(webapp2.RequestHandler):
    def get(self, appt_id):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        appt = Appointment.get_by_id(long(appt_id), user.key)
        if not(appt):
            self.redirect('/')
            return
        customer = User.get_by_id(appt.user)
        points = int(appt.price*POINT_PERCENT*1)
        customer.rewardpoints = customer.rewardpoints + points
        customer.put()
        appt.status = 3
        appt.put()
        template_values = {
            "profilebutton": getProfileButton(user),
            "customername": customer.firstName+" "+customer.lastName,
            "points": points
        }
        template = JINJA_ENVIRONMENT.get_template('barberRewardAppt.html')
        self.response.out.write(template.render(template_values))


class BarberApproveAppt(webapp2.RequestHandler):
    def get(self, appt_id):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        appt = Appointment.get_by_id(long(appt_id), user.key)
        if not(appt):
            self.redirect('/')
            return
        customer = User.get_by_id(appt.user)
        template_values = {
            "profilebutton": getProfileButton(user),
            "apptID": appt_id,
            "customername": customer.firstName+" "+customer.lastName,
            "datetime": formatDateTime(appt.startTime),
            "services": appt.services.replace(',',', '),
            "comments": appt.comment
        }
        template = JINJA_ENVIRONMENT.get_template('barberapproveappt.html')
        self.response.out.write(template.render(template_values))


class BarberDeleteAppt(webapp2.RequestHandler):
    def get(self, appt_id):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        appt = Appointment.get_by_id(long(appt_id), user.key)
        if not(appt):
            self.redirect('/')
            return
        #customer = User.get_by_id(appt.user)
        appt.key.delete()
        self.redirect('/barberViewAppt')

class BarberRejectAppt(webapp2.RequestHandler):
    def get(self, appt_id):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        appt = Appointment.get_by_id(long(appt_id), user.key)
        if not(appt):
            self.redirect('/')
            return
        #customer = User.get_by_id(appt.user)
        appt.key.delete()
        self.redirect('/barberViewAppt')

class UserConfirmAppt(webapp2.RequestHandler):
    def get(self, barber_key, appt_id):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        barber = User.get_by_id(barber_key)
        appt = Appointment.get_by_id(long(appt_id), barber.key)
        if not(appt):
            self.redirect('/')
            return
        if appt.user != user.key.integer_id().__str__():
            self.redirect('/')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "barberkey": barber_key,
            "apptID": appt_id,
            "barbername": barber.firstName+" "+barber.lastName,
            "datetime": formatDateTime(appt.startTime),
            "services": appt.services.replace(',',', '),
            "comments": appt.comment,
            "time": appt.time,
            "price": priceFormat(appt.price),
        }
        template = JINJA_ENVIRONMENT.get_template('UserConfirmAppt.html')
        self.response.out.write(template.render(template_values))

class UserEditAppt(webapp2.RequestHandler):
    def get(self, barber_key, appt_id):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        barber = User.get_by_id(barber_key)
        appt = Appointment.get_by_id(long(appt_id), barber.key)
        if not(appt):
            self.redirect('/')
            return
        if appt.user != user.key.integer_id().__str__():
            self.redirect('/')
            return
        if appt.status != 0:
            self.redirect('/')
            return
        template_values = {
            "profilebutton": getProfileButton(user),
            "barberkey": barber_key,
            "apptID": appt_id,
            "services": barberServicePickList(barber),
            "comments": appt.comment,
            "datetime": appt.startTime.strftime('%Y-%m-%d-%H:%M')
            
        }
        template = JINJA_ENVIRONMENT.get_template('userEditAppt.html')
        self.response.out.write(template.render(template_values))

class UserCancelAppt(webapp2.RequestHandler):
    def get(self, barber_key, appt_id):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        barber = User.get_by_id(barber_key)
        appt = Appointment.get_by_id(long(appt_id), barber.key)
        if not(appt):
            self.redirect('/')
            return
        if appt.user != user.key.integer_id().__str__():
            self.redirect('/')
            return
        if appt.status == 2:
            self.redirect('/')
            return
        if appt.status == 1:
            #TODO change sender address
            mail.send_mail("HeadWay <mamadouwann@gmail.com>",
                           barber.firstName+" "+barber.lastName+" <"+barber.email+">",
                           "Appointment Cancellation",
                           user.firstName+" "+user.lastName+" has cancelled his appointment. You can contact him at "+user.email+".")
        appt.key.delete()
        self.redirect('/userViewAppt')

class UserEditsAppt(webapp2.RequestHandler):
    def post(self, barber_key, appt_id):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        barber = User.get_by_id(barber_key)
        appt = Appointment.get_by_id(long(appt_id), barber.key)
        if not(appt):
            self.redirect('/')
            return
        if appt.user != user.key.integer_id().__str__():
            self.redirect('/')
            return
        if appt.status != 0:
            self.redirect('/')
            return
        serviceList = ""
        for i in range(27):
            data = self.request.get("service"+str(i),default_value="no")
            if data != 'no':
                if len(serviceList)>0:
                    serviceList+=","
                serviceList+=SERVICES[i]
        dateString = self.request.get('mydate').replace('-',' ')
        appt.startTime = datetime.strptime(dateString, '%Y %m %d %H:%M')
        appt.comment = self.request.get('comment')
        appt.services = serviceList
        appt.put()
        self.redirect('/userViewAppt')
class flagbarber(webapp2.RequestHandler):
    def post(self,barber_key):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber =getUser(barber_key,"nopoint")
        newflag = Flag(barberid = barber_key,
                       userid = user.key.string_id())
        newflag.put()
        self.redirect('/viewBarber/'+barber.email)
        
    
class UserConfirmsAppt(webapp2.RequestHandler):
    def post(self, barber_key, appt_id):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        barber = User.get_by_id(barber_key)
        appt = Appointment.get_by_id(long(appt_id), barber.key)
        if not(appt):
            self.redirect('/')
            return
        if appt.user != user.key.integer_id().__str__():
            self.redirect('/')
            return
        appt.status = 2
        appt.put()
        self.redirect('/userViewAppt')


class BarberApprovesAppt(webapp2.RequestHandler):
    def post(self, appt_id):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
            return
        appt = Appointment.get_by_id(long(appt_id), user.key)
        if not(appt):
            self.redirect('/')
            return
        appt.status = 1
        appt.time = int(self.request.get('time'))
        appt.price = float(self.request.get('price'))
        appt.put()
        self.redirect('/barberViewAppt')

def formatDateTime(datetime):
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    hour = datetime.hour
    ampm = 'A.M.'
    if hour>=12:
        ampm = 'P.M.'
    hour = (hour+11)%12+1
    string = str(hour)+":"
    if datetime.minute < 10:
        string+='0'
    string+=str(datetime.minute)+' '+ampm
    string+=' '+days[datetime.weekday()]+', '+months[datetime.month-1]+' '+str(datetime.day)+', '+str(datetime.year)
    return string

def formatDateTime2(datetime):
    hour = datetime.hour
    ampm = 'A.M.'
    if hour>=12:
        ampm = 'P.M.'
    hour = (hour+11)%12+1
    string = str(hour)+":"
    if datetime.minute < 10:
        string+='0'
    string+=str(datetime.minute)+' '+ampm
    string = str(datetime.month)+'/'+str(datetime.day)+'/'+str(datetime.year%100)+' '+string
    return string
def getnumberofBarberAppt(user):
    x=0
    if user.barber:
        appts = Appointment.query(ancestor=user.key)
        for appt in appts:
            x+=1
    else:
        appts=Appointment.query(Appointment.user == user.key.integer_id().__str__())
        for appt in appts:
            x+=1
        
    return x

def getBarberApptList(barber):
    string = ''
    appts = Appointment.query(ancestor=barber.key)
    addbreak = False
    for appt in appts:
        if addbreak:
            string+='<br />'
        string+=getBarberAppt(appt)
        addbreak = True
    if string == '':
        return '<center><h3>You currently have no appointments</h3></center>'
    return string

def getBarberAppt(appt):
    user = User.get_by_id(appt.user)
    status = "Pending"
    if appt.status == 1:
        status = "Approved"
    if appt.status == 2:
        status = "Confirmed"
    if appt.status == 3:
        status = "Rewarded"
    string = '<div data-role="content" data-theme="b" style=" color:#fff !important;"><center>'
    string+='<table><tr><td>Customer:</td><td>'+user.firstName+' '+user.lastName+'</td></tr>'
    string+='<tr><td>Phone: </td><td>'+user.phone+'</td></tr>'
    string+='<tr><td>Email: </td><td>'+user.email+'</td></tr>'
    string+='<tr><td>Date/Time:</td><td>'+formatDateTime(appt.startTime)+'</td></tr>'
    string+='<tr><td>Status:</td><td>'+status+'</td></tr>'
    string+='<tr><td>Services:</td><td>'+appt.services.replace(',',', ')+'</td></tr>'
    if appt.status > 0:
        string+='<tr><td>Time:</td><td>'+str(appt.time)+' minutes</td></tr>'
        string+='<tr><td>Price:</td><td>$'+priceFormat(appt.price)+'</td></tr>'
    string+='<tr><td>Comments:</td><td>'+appt.comment+'</td></tr>'
    string+='</table>'
    if appt.status == 0:
        string+='<input class="btn registerbutton" type="button" onclick="window.location=\'/barberApproveAppt/'+str(appt.key.id())+'\';" value="Approve" data-inline="true" /><br/> <br/>'
        string+='<input class="btn registerbutton" type="button" onclick="window.location=\'/barberRejectAppt/'+str(appt.key.id())+'\';" value="Reject" data-inline="true" /> <br/> <br/>'
    if appt.status == 2:
        #string+='<input type="button" onclick="window.location=\'/barberRewardAppt/'+str(appt.key.id())+'\';" value="Give Reward" data-inline="true" />'
        string+='<input  class="btn registerbutton" type="button" onclick="window.location=\'/barberDeleteAppt/'+str(appt.key.id())+'\';" value="Delete Appointment" data-inline="true" />'
    return string+'</div><hr/>'

def getUserApptList(user):
    string = ''
    appts = Appointment.query(Appointment.user == user.email)
    addbreak = False
    for appt in appts:
        if addbreak:
            string+='<br />'
        string+=getUserAppt(appt)
        addbreak = True
    if string == '':
        return '<center><h3>You currently have no appointments</h3></center>'
    return string
def checkoutbutton(user,appointment):
    string = '<form method="post" action="checkout.html"/>'
    string += '<input hidden name="amount" value="'+str(appointment.price)+'" />'
    string += '<input hidden name="comment" value="Payment of $'+moneyFormat(appointment.price)+' to '+user.firstName+'" />'
    string += '<input hidden name="accesstoken" value="'+user.wepayat+'" />'
    string += '<input hidden name="userid" value='+user.wepayuid+' />'
    string += '<input hidden name="appointment" value='+str(appointment.key.integer_id())+' />'
    string += '<input  class="btn  btn-lg registerbutton" type="submit" id="tutorbutton" value="PAY NOW " /></input>'
    return string
def moneyFormat(num):
    dollars = int(num)
    cents = int(num*100+.5-dollars*100)
    string = str(dollars)+"."
    if cents < 10:
        string += "0"
    return string + str(cents)


    
        
def getUserAppt(appt):
    barber = User.get_by_id(appt.key.parent().string_id())
    buttonstring = ''
    status = "Pending"
    if appt.status == 1:
        status = "Approved"
    if appt.status == 2:
        status = "Confirmed"

    if appt.status == 3:
        status = "Rewarded"
    string = '<div data-role="content" data-theme="b" style=" color:#fff !important;"><center>'
    string+='<table><tr><td>Barber: </td><td>'+barber.firstName+' '+barber.lastName+'</td></tr>'
    string+='<tr><td>Phone: </td><td>'+barber.phone+'</td></tr>'
    string+='<tr><td>Email: </td><td>'+barber.email+'</td></tr>'
    string+='<tr><td>Date/Time: </td><td>'+formatDateTime(appt.startTime)+'</td></tr>'
    string+='<tr><td>Status: </td><td>'+status+'</td></tr>'
    string+='<tr><td>Services: </td><td>'+appt.services.replace(',',', ')+'</td></tr>'
    string += '<tr><td>Comments: </td><td>' + appt.comment + '</td></tr>'
    if appt.status > 0:
        string+='<tr><td>Time: </td><td>'+str(appt.time)+' minutes</td></tr>'
        string+='<tr><td>Price: </td><td>$'+priceFormat(appt.price)+'</td></tr>'
        if not appt.paid:
            buttonstring = checkoutbutton(barber, appt);
            string += '<tr><td>' + buttonstring + '</td></tr>'


    string+='</table>'
    if appt.status == 0:
        string+='<input class="btn registerbutton" type="button" onclick="window.location=\'/userEditAppt/'+barber.email+'/'+str(appt.key.id())+'\';" value="Edit" data-inline="true" /> <br/> <br/>'
        string+='<input class="btn registerbutton"  type="button" onclick="window.location=\'/userCancelAppt/'+barber.email+'/'+str(appt.key.id())+'\';" value="Cancel" data-inline="true" /> <br/> <br/>'
    if appt.status == 1:
        string+='<inputclass="btn registerbutton" type="button" onclick="window.location=\'/userConfirmAppt/'+barber.email+'/'+str(appt.key.id())+'\';" value="Confirm" data-inline="true" /> <br/> <br/>'
        string+='<input class="btn registerbutton" type="button" onclick="window.location=\'/userCancelAppt/'+barber.email+'/'+str(appt.key.id())+'\';" value="Cancel" data-inline="true" /> <br/> <br/>'
    return string+'</div>'


def getAllFavorites(user):
    if user.favorite == '':
        return '<h2>You currently have no favorites</h2>'
    favs = user.favorite.split(';')
    string = ''
    addbreak = False
    for fav in favs:
        if addbreak:
            string+='<br/>'
        string+=getFavoriteBarberString(User.get_by_id(fav))
        addbreak = True
    return string

def getFavoriteBarberString(barber):
    string = '<div class="ui-bar-c ui-corner-all ui-shadow" style="padding:1em;">'
    string+='<table width="100%" border="0"><tr><th width="38%" scope="col">'
    href = '<a href="/viewBarber/'+barber.key.integer_id().__str__()+'">'
    string+=href
    if barber.photo=="" or not(barber.photo):
        string+='<img src="/statics/silhouette.png" width="100px" height="100px" />'
    else:
        string+='<img src="/viewPhoto/'+str(barber.photo)+'" style="max-height: 100px; max-width: 100px;" />'
    string+='</a></th><th width="62%" scope="col"><table width="100%" border="0"><tr>'
    string+='<th scope="col">'+href+barber.firstName+" "+barber.lastName+'</a></th></tr><tr>'
    string+='<th scope="row"><center><span class="stars s-'+str(getStars(barber.totalScore,barber.totalReviews))+'" data-default="'+str(getStars(barber.totalScore,barber.totalReviews))+'" style="text-align:right">0 stars</span></center>'
    string+=str(barber.currentRating)+' out of '+str(barber.totalReviews)+' review(s)</th></tr><tr>'
    string+='<th scope="row">'+barber.services+'</th></tr><tr>'
    string+='<th scope="row"><a class="btn registerbutton" style="font-size: 8pt; " href="/unfavBarber/'+barber.email+'">Unfavorite</a>'
    string+='</tr></table></th></tr></table></div>'
    return string
class sendermail(webapp2.RequestHandler):
    def post(self):
            mail.send_mail(self.request.get('name')+"<"+self.request.get('email')+">",
                           "Headway <mamadouwann@gmail.com",
                           "Complaint",
         
                           self.request.get('message'))
            self.redirect('/')
class UnfavBarber(webapp2.RequestHandler):
    def get(self, barber_key):
        if not(barber_key):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber = User.get_by_id(barber_key)
        if not(barber):
            self.redirect('/')
            return
        if not(barber.barber):
            self.redirect('/')
            return
        if not(user):
            self.redirect('/viewBarber/'+barber_key)
            return
        if user.barber:
            self.redirect('/viewBarber/'+barber_key)
            return
        if user.favorite == "":
            user.favorite = barber_key
            user.put()
            self.redirect('/viewBarber/'+barber_key)
        newfavs = ''
        favs = user.favorite.split(';')
        for fav in favs:
            if fav != barber_key:
                if newfavs != '':
                    newfavs+= ';'
                newfavs+=fav
        user.favorite = newfavs
        user.put()
        self.redirect('/MainPage')
class Checkout(webapp2.RequestHandler):
    def post(self):
        at = ""
        at = self.request.get('accesstoken',"")
        #raise Exception(len(at))
        if len(at) < 6:
            self.redirect('/error2.html')
        else:
            amount = ""
            amount = self.request.get('amount',1)
            resp = ""
            resp = self.request.get('comment',"")
            myuid = ""
            myuid = self.request.get('userid',"")
            url = ""
            url = self.request.host+'/payappointment.html?appt='+self.request.get('appointment')+'&at='+at
            if(amount == ""):
                amount = 1
            if(resp == ""):
                resp = "TEST DESCRIPTION"
            mywepay = WePay(production, at)
            respon = makeCheckout(mywepay, myuid, amount, resp,'http://'+url)
            myson = json.loads(respon)
            resp = myson['hosted_checkout']['checkout_uri']
            template_values = {
               # 'logo': au.getLogo(),
                #'emblem': au.getEmblem(),
                'checkout' : resp
            }
            template = JINJA_ENVIRONMENT.get_template('checkout.html')
            self.response.write(template.render(template_values))

class PayAppointment(webapp2.RequestHandler):
    def get(self):
        apptid = self.request.get('appt')
        appt = Appointment.get_by_id(int(apptid))
        if appt == None:
            self.redirect('/')
            return
        checkoutid = self.request.get('checkout_id')
        accesstoken = self.request.get('at')
        json = getpaymentinfo(checkoutid,accesstoken)
        if appt.price == json['amount']:
            appt.paid = True
            appt.checkoutid = int(checkoutid)
            appt.put()
            template_values = {
            }
            template = JINJA_ENVIRONMENT.get_template('thankyou.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect('/')

class UpdateHandler(webapp2.RequestHandler):
    def get(self):
        deferred.defer(UpdateSchema)
        self.response.out.write('Schema migration successfully initiated.')

class WepayAccountCreate(webapp2.RequestHandler):
    def get(self):
        template_values = {
        }
        template = JINJA_ENVIRONMENT.get_template('createaccount.html')
        self.response.write(template.render(template_values))


class CreateWepayAccount(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get('user',''),self.request.cookies.get('pass',''))
        # oauth2 parameters
        code = ''
        code = self.request.get('code',''); # the code parameter from step 2
        redirect_uri = "http://www.headwayapp.net/map"; # this is the redirect_uri you used in step 1
        if(code != ''):
            # create an account for a user
            resp = wepay.get_token(redirect_uri, client_id, client_secret, code)
            self.response.write(resp);
            mywepay = WePay(production, resp['access_token'])
            # create an account for a user
            response2 = mywepay.call('/account/create', {
                'name': user.firstName,
                'description': 'A payment account for HeadWay'
            })
            response2 = json.loads(response2)
            #raise Exception('RESPONSE: '+str(response2['account_id']))
            #self.response.out.write(str(response2))
        else:
            self.response.out.write('Error')
        user.wepayuid=str(response2['account_id'])
        user.wepayat =str(resp['access_token'])
        user.put()
###############################################################################################################
 ###New stuff 
        
class checklicense(webapp2.RequestHandler):
    def post(self):
         newlicense =''
         stringed = str(self.request.get("license"))
         query = ndb.gql("Select * from License_DB Where license ='"+self.request.get("license")+"'")
         for item in query:
             newlicense = item
         user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))    
         if query:
            if newlicense:
                if  newlicense.Last_Name== user.lastName:
                    if newlicense.license_state == 'Active':
                        user.certified = True
                        user.license = self.request.get('license')
                        user.put()
                        self.redirect("/certificationcomplete.html")
            else:
                self.redirect("/")
         else:
            self.response.redirect("/error") #add error page soon!!!! 
class certificationcomplete(webapp2.RequestHandler):
    def get(self):
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        template_values = {
            "profilebutton": getProfileButton(user),
            "states": getStateSelect('')
        }
        template = JINJA_ENVIRONMENT.get_template('certificationcomplete.html')
        self.response.out.write(template.render(template_values))

class UploadCsv(webapp2.RequestHandler):
    def get(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
        if user.email!= "mwann@conssol.net":
            self.redirect('/')
        else:
            upload_url = blobstore.create_upload_url('/upload')

            html_string = """
             <form action="%s" method="POST" enctype="multipart/form-data">
            Upload File:
            <input type="file" name="file"> <br>
            <input type="submit" name="submit" value="Submit">
            </form>""" % upload_url

            self.response.write(html_string)


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        process_csv(blob_info)

        blobstore.delete(blob_info.key())  # optional: delete file after import
        self.redirect("/")


def process_csv(blob_info):
    blob_reader = blobstore.BlobReader(blob_info.key())
    reader = csv.reader(blob_reader, delimiter=',')
    for row in reader:
        
        lastname = row[0]
        first_name = row[1]
        middle_name = row[2]
        city = row[9]
        State = row[10]
        County = row[11]
        zip_code = row[12]
        license = row[16]
        license_state = row[20]

        entry = License_DB(Last_Name= lastname, first_name = first_name, middle_name = middle_name, city=city, State=State,County= County, zip_code = zip_code, license=license, license_state = license_state)
        entry.put()

class License_DB(ndb.Model):
    Last_Name = ndb.StringProperty()
    first_name = ndb.StringProperty()
    middle_name = ndb.StringProperty()
    city = ndb.StringProperty()
    State = ndb.StringProperty()
    County = ndb.StringProperty()
    zip_code = ndb.StringProperty()
    license = ndb.StringProperty()
    license_state = ndb.StringProperty()

def getEmblem():
    query = ndb.gql("Select * from Settings")
    settings = None
    for item in query:
        settings = item
    if not(settings.emblem):
        return '../statics/images/symbol.png'
    return '/viewPhoto/'+str(settings.emblem)

#makeCheckout(wepayclass, number, number, string,redirect_url-string-)
def makeCheckout(wepay,account_id,amount,note,redirect_url):
    # create the checkout
    response = wepay.call('/checkout/create', {
        'account_id': account_id,
        'amount': amount,
        "currency": "USD",
        'short_description': note,
        'type': 'service'
    })
    return response

def getCheckout(checkout_id):
    response = wepay.call('/checkout', {
        'checkout_id': checkout_id
    })
    return response

def refund(checkout_id,at):
    mywepay = WePay(False, at)
    response = mywepay.call('/checkout/refund', {
        'checkout_id': str(checkout_id),
        'refund_reason': 'Refunded through Tutorsbin'
    })
    resp = str(response)
    count = resp.count('error')
    if(count > 0):
        return "Error"
    return response

def wepayinformation(user):
    string =' <tr> <td>Wepay Information:</td> </tr>'
   # string+= '<tr> <td class="info_fields"><input value="'+str(user.wepayaccount)+'"/></td> </tr>'
   # string+= '<tr> <td class="info_fields"><input value="'+str(user.wepaycheckout)+'"/></td></tr>'
    string+= '<tr><td width=10% colspan="1"><a id="start_oauth2">Click here to create your WePay account</a> </td></tr>'
    return string

def getpaymentinfo(checkout_id,at):
    mywepay = WePay(True, at)
    response = mywepay.call('/checkout', {
        'checkout_id': checkout_id
    })
    return json.loads(response)

def UpdateSchema(cursor=None, num_updated=0):
    query =User.query()
    if cursor:
        query.with_cursor(cursor)

    to_put = []
    for p in query.fetch_page(BATCH_SIZE):
        # In this example, the default values of 0 for num_votes and avg_rating
        # are acceptable, so we don't need this loop.  If we wanted to manually
        # manipulate property values, it might go something like this:
        p.aboutme = 'iwin'
        to_put.append(p)

    if to_put:
        ndb.put_multi(to_put)
        num_updated += len(to_put)
        logging.debug(
            'Put %d entities to Datastore for a total of %d',
            len(to_put), num_updated)
        deferred.defer(
            UpdateSchema, cursor=p.fetch_page(BATCH_SIZE), num_updated=num_updated)
    else:
        logging.debug(
            'UpdateSchema complete with %d updates!', num_updated)
app = webapp2.WSGIApplication([
    ('/', homepage),
    ('/facebook',facebook),
    ('/fblogin',facebooklogin),
    ('/MainPage', MainPage),
    ('/registerUser',RegisterUser),
    ('/registerPage1',RegisterPage1),
    ('/registerBarber',RegisterBarber),
    ('/registerPage3',RegisterPage3),
    ('/addUser',AddUser),
    ('/addBarber',AddBarber),
    ('/login',LogIn),
    ('/logout',LogOut),
    ('/checkout.html', Checkout),
    ('/update_schema', UpdateHandler),
    ('/createaccount.html', WepayAccountCreate),
    ('/useraccountcreate', CreateWepayAccount),
    ('/setPhoto',SetPhoto),
    ('/uploadPhoto',UploadPhoto),
    ('/viewPhoto/([^/]+)?', ViewPhotoHandler),
    ('/viewBarber/([^/]+)?', ViewBarber),
    ('/reviewBarber/([^/]+)?', ReviewBarber),
    ('/register', Register),
    ('/search', Search),
    ('/editBarber', EditBarber),
    ('/editUser', EditUser),
    ('/saveUser',SaveUser),
    ('/saveBarber',SaveBarber),
    ('/verify',Verify),
    ('/database',Database),
    ('/map',Map),
    ('/about',About),
    ('/calendar',Calendar),
    ('/howtocertify',howtocertify),
    ('/MakeAppt/([^/]+)?', makeappt),
    ('/UserSaveAppt/([^/]+)?',SaveAppt),
    ('/favBarber/([^/]+)?',FavBarber),
    ('/favorites', Favorites),
    ('/userViewAppt', UserViewAppt),
    ('/barberViewAppt', BarberViewAppt),
    ('/barberApproveAppt/([^/]+)?', BarberApproveAppt),
    ('/barberRejectAppt/([^/]+)?', BarberRejectAppt),
    ('/barberApprovesAppt/([^/]+)?', BarberApprovesAppt),
    ('/userConfirmAppt/([^/]+)?/([^/]+)?', UserConfirmAppt),
    ('/userConfirmsAppt/([^/]+)?/([^/]+)?', UserConfirmsAppt),
    ('/userEditAppt/([^/]+)?/([^/]+)?', UserEditAppt),
    ('/userEditsAppt/([^/]+)?/([^/]+)?', UserEditsAppt),
    ('/userCancelAppt/([^/]+)?/([^/]+)?', UserCancelAppt),
    ('/barberRewardAppt/([^/]+)?',BarberRewardAppt),
    ('/barberDeleteAppt/([^/]+)?',BarberDeleteAppt),
    ('/BarberProfile', BarberProfilepage),
    ('/unfavBarber/([^/]+)?',UnfavBarber),
    ('/sendmail', sendermail),
    ('/forgotPassword',ForgotPass),
    ('/sendPass',SendPass),
    ('/changeHours',ChangeHours),
    ('/saveHours',SaveHours),
    ('/privacy',Privacy),
    ('/eula',License),
    ('/payappointment.html', PayAppointment),
    ('/certificationcomplete.html',certificationcomplete),
    ('/trying',UploadCsv),
    ('/checklicense',checklicense),
    ('/upload', UploadHandler),
    ('/flag/([^/]+)?',flagbarber)
    
], debug=True)
