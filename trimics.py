#!/usr/bin/python3

"""
Python script to open and load an iCal calendar file, parse through it
to remove unnecessary crap, extract events that will end after a certain
date in the past, and write the reduced set out to a new file.

usage: trimics.py [-h] -i INFILE -o OUTFILE [-v] [-s] [-m MONTHSBEFORE]

options:
  -h, --help            show this help message and exit
  -i INFILE, --infile INFILE
                        Input filename (.ics)
  -o OUTFILE, --outfile OUTFILE
                        Output filename (.ics)
  -v, --verbose         Extra output
  -s, --strip-application-specific
                        Strip application-specific subcomponents from file ("X--..." sub-components)
  -m MONTHSBEFORE, --months-before MONTHSBEFORE
                        How long to go back

"""

from icalendar import Calendar, Event
from dateutil.relativedelta import relativedelta
import datetime
import os
import argparse
import sys

"""
Class to do a few specific things to an iCal-formatted calendar file:
+ load an iCal from file
+ create a new iCal from events
+ do some arbitrary manipulation
"""
class ical(object):
    """
    Instantiate the class with a file name.  Could be input or output file,
    decide later.  Also, a bool to indicate extra output.
    """
    def __init__(self, fname : str, verbosity : bool):
        self._fname = fname
        self._verbosity = verbosity
        self._file = None
        self._calendar = Calendar()
        self._events = []

    """
    Clear all data from the calendar
    """
    def reset(self):
        if not self._calendar.is_empty():
            self._calendar.clear()

    """
    Create a new calendar, iCal version 2
    """
    def createNew(self):
        self.reset()
        self._calendar = Calendar()
        self._calendar.add('prodid', 'Matty cleaned calendar')
        self._calendar.add('version', '2.0')

    """
    Write this calendar out to an .ical file
    """
    def writeToFile(self) -> bool:
        if not self._calendar.is_empty():
            try:
                outfile = open(self._fname, 'wb')
                outfile.write(self._calendar.to_ical())
                outfile.close()

                print ('Wrote {} events to \'{}\''
                    .format(self.getEventCount(), self._fname))

                return (True)
        
            except Exception as ex:
                print (ex)
        
        return (False)

    """
    Read an .ical file and populate this calendar object.  Will also
    fill the internal list<Events> with all events in the calendar
    """
    def readFromFile(self) -> bool:
        if self._calendar.is_empty():
            try:
                if self._verbosity:
                    print ('\'{}\' size is {} bytes'.format(self._fname, os.stat(self._fname).st_size))
                
                self._file = open(self._fname, 'rb')
            except FileNotFoundError:
                print ('Input file \'{}\' not found!'.format(self._fname))
                return (False)
            except PermissionError:
                print ('No read permissions for file \'{}\''.format(self._fname))
                return (False)
            
            if self._verbosity:
                print ('Reading calendar entries from \'{}\''.format(self._fname))
            
            self._calendar = Calendar.from_ical(self._file.read())
            self._file.close()

            self._events = self._calendar.walk('VEVENT')

            print ('Read {} events from \'{}\''
                    .format(self.getEventCount(), self._fname))

            return (True)
        else:
            print ('Error - clear calendar before loading new data')
            return (False)
    
    """
    How many events in this calendar?
    """
    def getEventCount(self) -> int:
        return (len(self._events))
    
    """
    Return the specified event by index.  Arbitrary; just the 
    order in which they exist in the calendar.  There's no sorting
    """
    def getEvent(self, eventID : int) -> Event | None:
        if not self._calendar.is_empty():
            try:
                return (self._events[eventID])
            except IndexError:
                if self._verbosity:
                    print ('Tried to get Event {} (calendar has {} events)'
                        .format(eventID, self.getEventCount()))
        
        return (None)
    
    """
    Add an event component to the calendar
    """
    def addEvent(self, e : Event) -> bool:
        if self._calendar.is_empty():
            self.createNew()

        self._calendar.add_component(e)
        self._events.append(e)

        return (True)

    """
    Return a list of Events.  The events to be returned either:
    + have an end date later than today minus 'months' months
    + are recurring with no end date
    + are recurring, but have an end date later than today minus
      'months' months.

    This is a bit hokey because the DTEND and RRULE subcomponents
    of an .ical might be dates, might be date/times, might be timezone
    aware or naive.  Sigh.
    """
    def findEventsByDateAfter(self, months : int) -> list[Event]:
        retList = []

        # cutoff date is today minus some number of months
        cutoff = datetime.datetime.now().date() - relativedelta(months=months)

        if self._verbosity:
            print ('Finding all events that end after {}'.format(cutoff))

        # iterate over all the Event objects in the list
        for event in self._events:

            # assume no recurrence
            recurring = False

            try:
                x = event['RRULE']
                # if there is an 'RRULE' subcomponent, then it is recurring
                
                # if there's no end date, add it
                if 'UNTIL' not in x:
                    recurring = True
                else:
                    d = event['RRULE']['UNTIL'][0]
                    if isinstance(d, datetime.datetime):
                        d = d.date()

                    # if the end date is after our cutoff, add it
                    if d >= cutoff:
                        recurring = True

            except KeyError:
                pass

            # if DTEND subcomponent is a date/time, convert it to just a date
            if isinstance(event['DTEND'].dt, datetime.datetime):
                end = event['DTEND'].dt.date()
            else:
                end = event['DTEND'].dt

            # if end is after our cutoff (or a qualifying recurrence), add it
            # to the output list
            if end >= cutoff or recurring:
                if self._verbosity:
                    print ('Adding event {}'.format(event['SUMMARY']))

                retList.append(event)

        return (retList)

    """
    String matching to find an event based on summary text.  Return type is a tuple of
    Event index and either the event or None.  You can use the return index as a start
    to implement a 'find next' 
    """
    def findEventBySummary(self, srch : str, startInx = 0) -> tuple[int, Event | None] :
        ret = (startInx, None)

        if not self._calendar.is_empty():
            found = False
            while not found:
                thisEvent = self.getEvent(startInx)

                if srch.upper() in thisEvent['SUMMARY'].upper():
                    ret = (startInx, thisEvent)
                    break
                
                startInx += 1

                if startInx >= self.getEventCount():
                    break

        return (ret)

    """
    Strip all non-standard subcomponents from the passed event.  For example,
    Apple iOS and MacOS calendar applications add a crap load of non-standard
    stuff.  By standard defined by RFC for ical, these all begin with 'X-'; kind
    of like email header extensions.  They can add up to a lot of space in the 
    file.
    """
    @staticmethod
    def stripApplicationSpecificSubcomponents(event : Event) -> Event | None:
        retEvent = Event()
        for subComponent in event:
            if 'X-' not in subComponent:
                retEvent[subComponent] = event[subComponent]

        return (retEvent)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile', dest='infile', required=True, help='Input filename (.ics)')
    parser.add_argument('-o', '--outfile', dest='outfile', required=True, help='Output filename (.ics)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Extra output')
    parser.add_argument('-s', '--strip-application-specific', dest='stripAppSpecific', action='store_true', help='Strip application-specific subcomponents from file ("X--..." sub-components)')
    parser.add_argument('-m', '--months-before', dest='monthsBefore', type=int, default=12, help='How long to go back')
    args = parser.parse_args()

    # create and load a calendar from the input .ical file
    incal = ical(args.infile, args.verbose)
    if not incal.readFromFile():
        print ('error loading input file')
        sys.exit(1)

    # create a new empty calendar
    outcal = ical(args.outfile, args.verbose)
    outcal.createNew()

    # go through the input calendar.  For every Event that ends after 
    # today minus specified monts, add it to the output calendar.
    # Optionally, strip application specific crap to reduce output file size.
    for event in incal.findEventsByDateAfter(args.monthsBefore):
        if args.stripAppSpecific:
            outcal.addEvent(ical.stripApplicationSpecificSubcomponents(event))
        else:
            outcal.addEvent(event)

    outcal.writeToFile()
