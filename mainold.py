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
import urllib
import random
import webapp2
import jinja2
import os
import hashlib
import math
from django.utils import simplejson
from datetime import datetime, timedelta, time

from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+'/'),
    extensions=['jinja2.ext.autoescape'])

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
        return geocode(address,sensor, geo_args)

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
        mail.send_mail("GroomR  <mamadouwann@gmail.com>",
                       "<"+user.email.__str__()+">",
                       "Your New Password",
                       "Thank you for using our services. Your new password is "+password)
        self.redirect('/')
        
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
        self.redirect('/MainPage')

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
        self.redirect('/MainPage')


class AddUser(webapp2.RequestHandler):
    def post(self):
        userAddress = self.request.get('street')+','+self.request.get('city')+','+self.request.get('state')
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
                    
                    favorite = '',
                    barber = False,
                    rewardpoints = 0)
        user.put()
        self.redirect('/')
  
        

class AddBarber(webapp2.RequestHandler):
    def post(self):
        userAddress = self.request.get('street')+','+self.request.get('city')+','+self.request.get('state')
        result = geocode(address=userAddress,sensor="false")
        #self.response.write('Services: '+self.request.get('serviceNum')+'<br />')
        floatList = [-1.0 for x in range(len(SERVICES))]
        for i in range(int(self.request.get('serviceNum'))):
            self.response.write(self.request.get('service'+str(i+1))+': ')
            for i2 in range(len(SERVICES)):
                if SERVICES[i2]==self.request.get('service'+str(i+1)):
                    floatList[i2] = float(self.request.get('price'+str(i+1)))
                    self.response.write(self.request.get('price'+str(i+1))+'<br />')
        user = User(id = self.request.get('email'),
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
                self.redirect('/MainPage')

            return
        
        if not(hashlib.sha224(password).hexdigest()==user.password):
            self.redirect('/MainPage')
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
        self.redirect('/')


class SetPhoto(webapp2.RequestHandler):
    def get(self):
        user = getBarber(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        if not(user):
            self.redirect('/')
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
            self.redirect('/')
            return
        old_key = user.photo
        if old_key:
            blobstore.delete(old_key)
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        upload = upload_files[0]
        user.photo = upload.key()
        user.put()
        self.redirect('/viewBarber/%s' % user.key.integer_id().__str__())

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
    string = '<div data-role="collapsible-set"><div data-role="collapsible"><h3>Offered Services</h3>'+string[6:]

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
    return '<img onclick="favorite();" style="cursor: pointer;" src="../statics/favicon.png" width='+size+' height='+size+'>'

class ViewBarber(webapp2.RequestHandler):
    def get(self, barber_key):
        flagbutton = ''
        
        if not(barber_key):
            self.redirect('/')
            return
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        barber =getUser(barber_key,"nopoint")
        flag = getFlag(user)
        if not(barber):
            self.redirect('/')
            return
        if not(barber.barber):
            self.redirect('/')
            return
        review = "<br/>Log in to Review This Barber"
        if user:
            if user.barber:
                review = ""
            else:
                review = getReviewForm(barber.email)
                if not flag:
                    flagbutton ='<form method="post" action="/flag/'+barber_key+'"><button class="btn registerbutton"> Flag  inappropriate </button></form>'
                if flag:
                    flagbutton = 'You have flagged this user'
        numReviews = barber.totalReviews
        rating = "No Rating"
        numstars = 0
        if numReviews>0:
            rating = str(getScore(barber.totalScore,numReviews))+" out of "+str(numReviews)+" review(s)."
            numstars = str(getStars(barber.totalScore,numReviews))
        photo = '<img class="img-rounded"   src="/viewPhoto/'+barber.photo.__str__()+'" style=" width:60%;; margin-left:2%" />'
        if barber.photo.__str__() == '' or not(barber.photo):
            photo = '<img  class="img-rounded"  style="margin-left:2%;width:40%; "src="/statics/silhouette.png" " />'
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
            'phone': barber.phone,
            'email': barber.email,
            'address': barber.street+', '+barber.city+', '+barber.state,
            'aboutMe': barber.aboutMe,
            'hours': getAvailability(barber)
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
    string ='<br/><button class="btn btn-primary btn-lg registerbutotn" data-toggle="collapse" data-target="#mycomment" ><span class="glyphicon glyphicon-comment"> Reviews</span> </button> <br/><div class="collapse" data-role="collapsible" id="mycomment">'+string+'</div>'
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
    string = ""
    numStars = 0
    if barber.totalScore>0:
        numStars = (int)(barber.totalScore*2.0/barber.totalReviews+.5)
        numStars = numStars/2.0
    string+='{ "latitude":'+str(barber.location.lat)+', "longitude":'+str(barber.location.lon)
    string+=', "title":"'+barber.email+'", "barbername":"'+barber.firstName+' '+barber.lastName+'", '
    string+='"description":"'+barber.shopName+'", "starnum":'+str(numStars)+', '
    string+='"rating":"'+str(barber.currentRating)+'", '
    string+='"user":0, "distance":'+str(miles)+', '
    if barber.photo:
        string+='"photo":"'+str(barber.photo)+'"'
    else:
        string+='"photo":""'
    return string+' }'

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
            self.redirect('/')
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
        user = getUser(self.request.cookies.get("user",""),self.request.cookies.get("pass",""))
        string = getJsonString(self.request.get("location"),
                               float(self.request.get('range')),
                               float(self.request.get('rating')))
        template_values = {
            "jsonobject": string,
            "profilebutton": getProfileButton(user)
        }
        template = JINJA_ENVIRONMENT.get_template('map.html')
        self.response.out.write(template.render(template_values))
    def get(self):
        self.redirect('/MainPage')

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
        self.redirect("/")

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
    href = '<a href="/viewBarber/'+user.key.integer_id().__str__()+'">'
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
    string+='<th scope="row">'+barber.services+'</th></tr></table></th></tr></table></div>'
    return string

def getJsonString(myLocation,minRange,minRating):
    if myLocation[0]=="[":
        string = (myLocation)[1:-1]
        strings = string.split(",")
        myLocation = [float(strings[0]),float(strings[1])]
    else:
        myLocation = geocode(address=myLocation,sensor="false")
    string = '{"markers":['
    string+= '{ "latitude":'+str(myLocation[0])+', "longitude":'+str(myLocation[1])
    string+= ', "title":"", "barbername":"", "description":"", "starnum":0, "rating":0, "photo":"", "user":1, "distance":0}'
    barbers = User.query(User.barber == True)
    barbers = barbers.filter(User.currentRating >= minRating)
    for barber in barbers:
        miles = getDist(myLocation,[barber.location.lat,barber.location.lon])
        if miles <= minRange:
            string+=","+getBarberData(barber,miles)
    string+=']}'
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
        template = JINJA_ENVIRONMENT.get_template('howtoCertify.html')
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
        if data[i] >= 0:
            string+='<input type="checkbox" onclick="toggleService('+str(i)+');" name="service'+str(i)+'" id="service'+str(i)
            string+='" class="custom" value="" /><label for="service'+str(i)+'">'+SERVICES[i]
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
        mail.send_mail("GroomR <mamadouwann@gmail.com>", #TODO CHANGE THIS EMAIL ADDRESS
                        barber.firstName+" "+barber.lastName+" <"+barber.email+">",
                        "New Appointment",
                        user.firstName+" "+user.lastName+" has requested an appointment. Log on to Head Way to review it!")
        mail.send_mail("GroomR <groomr@gmail.com>", #TODO CHANGE THIS EMAIL ADDRESS
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
            mail.send_mail("GroomR <mamadouwann@gmail.com>",
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
        self.redirect('/viewBarber/'+barber_key)
        
    
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

    
        
def getUserAppt(appt):
    barber = User.get_by_id(appt.key.parent().string_id())
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
    if appt.status > 0:
        string+='<tr><td>Time: </td><td>'+str(appt.time)+' minutes</td></tr>'
        string+='<tr><td>Price: </td><td>$'+priceFormat(appt.price)+'</td></tr>'
    string+='<tr><td>Comments: </td><td>'+appt.comment+'</td></tr>'
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
                           "GroomR <mamadouwann@gmail.com",
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
       
app = webapp2.WSGIApplication([
    ('/', homepage),
    ('/MainPage', MainPage),
    ('/registerUser',RegisterUser),
    ('/registerPage1',RegisterPage1),
    ('/registerBarber',RegisterBarber),
    ('/registerPage3',RegisterPage3),
    ('/addUser',AddUser),
    ('/addBarber',AddBarber),
    ('/login',LogIn),
    ('/logout',LogOut),
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
    ('/database',Database),
    ('/map',Map),
    ('/calendar',Calendar),
    ('/howtoCertify',howtocertify),
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
    ('/flag/([^/]+)?',flagbarber)
    
], debug=True)
