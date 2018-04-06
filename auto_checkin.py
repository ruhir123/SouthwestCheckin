import re, sys, sched, datetime, urllib, urllib2, urlparse
import time as timeModule
from datetime import datetime,date,timedelta,time
from pytz import timezone,utc

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

dictCode = {}
fname = "Airport_TZ.info"

with open(fname) as f:
    content = f.read().splitlines()

for line in content:
	val = line.split('\t')
	dictCode[val[0]] = val[1]

#print dictCode
utc = timezone('UTC')

def is_dst (tzone):
    """Determine whether or not Daylight Savings Time (DST)
    is currently in effect"""
    x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=timezone(tzone)) # Jan 1 of this year
    y = datetime.now(timezone(tzone))
    # if DST is in effect, their offsets will be different
    return not (y.utcoffset() == x.utcoffset())


def find_times(firstName, lastName, confirmation):
	baseUrl = 'https://www.southwest.com'
	infoUrl = '/flight/view-air-reservation.html?confirmationNumberFirstName='+firstName+'&confirmationNumberLastName='+lastName+'&confirmationNumber='+confirmation
	retrieveUrl = urlparse.urljoin(baseUrl, infoUrl)
	print(retrieveUrl)

	browser = webdriver.Firefox()
	browser.get(retrieveUrl)
	html = browser.page_source
	timeModule.sleep(10)

	flightSegments  = browser.find_elements_by_class_name('checkout-flight-detail')
	print("Found Segments ", len(flightSegments))
	retval=[]
	for fSegment in flightSegments:
		fdate = fSegment.find_elements_by_class_name('flight-detail--heading-date')[0].text.split(' ')[0].split('/')
		ftime = fSegment.find_elements_by_class_name('time--value')[0].text
		ft = ftime[:-2].split(':')
		if ftime[-2:] == "PM":
			ft[0] = int(ft[0]) + 12

		fCode = fSegment.find_elements_by_class_name('flight-segments--airport-code')[0].text

		fDateTime = datetime(int('20' + fdate[2]), int(fdate[0]), int(fdate[1]), int(ft[0]), int(ft[1]), 0, 0, tzinfo=timezone(dictCode[fCode]))

		#print (fdate, ftime, fCode, fDateTime)
		retval.append([fDateTime, fdate, ftime, fCode])


	print retval
	browser.quit()
	return retval



def auto_checkin(firstName, lastName, confirmation, flightDateTime=None):

	baseUrl = 'https://www.southwest.com'
	dataUrl = '/flight/retrieveCheckinDoc.html?firstName='+firstName+'&lastName='+lastName+'&confirmationNumber='+confirmation
	checkinUrl = urlparse.urljoin(baseUrl, dataUrl)
	print(checkinUrl)

	waitTime = (flightDateTime - timedelta(days=1)) - utc.localize(datetime.utcnow())

	#print waitTime

	wtime = waitTime.total_seconds()
	print("Waiting for ", wtime, "time", waitTime)
	while (wtime > 0):
		wtime = wtime -10
		timeModule.sleep(10)
		wdays = int(wtime/60/60/24)
		whours = int((wtime - wdays*60*60*24)/60/60)
		wmins = int((wtime - wdays*60*60*24 - whours*60*60)/60)
		wsecs = int(wtime - wdays*60*60*24 - whours*60*60 - wmins*60)
		print 'Waiting to check in for ',  wdays, " Days ", whours, " Hours ", wmins, " Minutes ", wsecs, " Seconds "
		#timeModule.sleep(waitTime.total_seconds()-1)

	print("Time to Checkin ...", checkinUrl)

	loop = True
	# Launch Firefox GUI
	browser = webdriver.Firefox()
	browser.get(checkinUrl)
	html = browser.page_source

	while loop:

		err = browser.find_element_by_class_name('error-reservation-not-found')
		if err:
			print("Found Element Error ", err)
			button = browser.find_element_by_class_name('submit-button')
			button.click()
			html = browser.page_source
		else:
			loop = False

		print ("Sleeping 10 Seconds ...")
		timeModule.sleep(10)

	#browser.quit()

	
if __name__ == '__main__':
	firstName = raw_input("First Name: ")
	lastName = raw_input("Last Name: ")
	confirmation = raw_input("Confirmation Number: ")

	flightinfo = find_times(firstName, lastName, confirmation)
	for flight in flightinfo:
		if is_dst(dictCode[flight[3]]):
			flight[0] = flight[0] - timedelta(hours=1)		
		auto_checkin(firstName, lastName, confirmation, flight[0])


