from django.shortcuts import render
from django.http import HttpResponse
import requests
import os
from django.views.decorators.csrf import csrf_exempt
import csv
import json
import pyrebase
import datetime
import numpy as np
from datetime import datetime

config = {
  "apiKey": "AIzaSyDLoKVCsTpcVHcG7QwnX-3ksBuZQRyf9ros",
  "authDomain": "feedemote.firebaseapp.com",
  "databaseURL": "https://feedemote.firebaseio.com",
  "storageBucket": "feedemote.appspot.com",
  "messagingSenderId": "13469760655"
}

tips = {
	"joy" : "Audience are enjoying!", 
	"fear" : "Audience are freaking out!", 
	"disgust" : "This is disgusting!", 
	"sadness" : "It's more sad now!", 
	"anger" : "They'r becoming angry!", 
	"surprise" : "It's surprising!", 
	"engagement" : "Your presentation is engaging", 
	"attention" : "Good attention to your presentation"
}

firebase = pyrebase.initialize_app(config)

db = firebase.database()

@csrf_exempt
def upload(request):
	userID = request.POST.get('userid', '')
	pr_id = request.POST.get('pr_id', '')
	for key, sfile in request.FILES.iteritems():
		with open(sfile.name, 'wb+') as destination:
			for chunk in sfile.chunks():
					destination.write(chunk)
	os.system("~/build/video-demo/video-demo -i ~/feedemote/"+sfile.name+" -d ~/affdex-sdk/data/ --draw=0 --numFaces=50")
	csvname = sfile.name.split(".")[0]
	csvfile = open(csvname+'.csv', 'r')
	fieldnames = ("TimeStamp", "faceId", "joy", "fear", "disgust", "sadness", "anger", "surprise", "engagement", "attention")
	reader = csv.DictReader( csvfile)
	rowdict = {}
	for row in reader:
		for key, value in row.iteritems():
			if key in fieldnames and value != 'nan':
				if key in rowdict:
					rowdict[key].append(float(value))
				else:
					rowdict[key] = [float(value)]
	resultdict = {}
	for key, value in rowdict.iteritems():
		if key in ["TimeStamp", "faceId"]:
			continue
		print value
		avg = np.mean(value)
		resultdict[key] = avg
	if resultdict:
		max_val = 0
		max_key = ''
		for key, value in resultdict.iteritems():
			if max_val < value:
				max_val = value
				max_key = key
		tip = tips[max_key]
		addToLog(userID, pr_id, resultdict, tip)
	return HttpResponse("uploaded!")


def addpr(request):
	userID = request.GET.get('userid', '')
	presentation_key = getPresentationKey(userID)
	print presentation_key
	resp = json.dumps({'pr_key' : presentation_key})
	return HttpResponse(resp)

def endpr(request):
	pass

def addToLog(userID, presentation_id, data, tip):
	#add data to logs
	#print datetime.now().time()
	db.child("logs").push({
		"time" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		"user_id": userID,
		"presentation_id": presentation_id,
		"data": data
	})
	db.child("users").child(userID).child("presentation").set({
		"time" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
		"tip" : tip,
		"state": "running",
		"data": data,
		"id":presentation_id
	})

def getPresentationKey(userID):
	#check if presentation exists
	status = db.child("users").child(userID).child("presentation").child("state").get().val()
	if(status == "running"):
		return db.child("users").child(userID).child("presentation").child("id").get().val()
	else:
		return db.generate_key()
