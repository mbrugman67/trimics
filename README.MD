# ICS calendar file trimmer
## tl;dr version
This python script will take in an `.ics` file and allow some manipulation before saving to another file.  For example, it can save only the events that end after a certain date, and can also remove application-specific components from the file.

This operates on [RFC 5545-compatible .ics files](https://datatracker.ietf.org/doc/html/rfc5545.html)

Skip down to the [usage information](#usage) to learn about using it.

# Background
I share an Apple iOS-based calendar with family; however, I'm the lone Android user.  I also subscribe to this calendar in Evolution email on a Linux box.  To be sure I have the most up-to-date calendar on my phone, I generally do something like this once a week:
+ Export the current calendar from Evolution as an `.ics` file
+ Open a web browser and go to my Google calendar (same account as the Android phone)
+ Delete all events in that calendar
+ Import the `.ics` file into the Google calendar

From there, my phone pulls in the latest and I'm up to date.  This has worked fine for years, but now the history and data in the calendar is causing the file to get too large to import into Google calendar via web.

This python script fixes that.  I still export the calendar as an `.ics` from Evolution, but then post-process it with this script.  I take only the events that have end dates that occur anytime after 12 months ago (that way I have a year of history on my phone).

In addition, the script also strips out any application-specific subcomponents from the Events in the calendar.  iOS adds a LOT of extra information that isn't strictly necessary, which takes up a lot of file space.  That extra space causes import issues.

# Usage
## Installation
Clone this repo.  The python script itself is written for Python3.  If you're still using Python (2), you really need to get up to date!

Once cloned, you'll need to install some modules.  I strongly suggest using a virtual environment for this; if you don't it's only a matter of time before your "main" python environment gets polluted and corrupt.  Save yourself the headache.

Set up the environment: 
```
$ python3 -m venv venv
```  
Enter the virtual environment:
```  
$ . ./venv/bin/activate
```  
Install necessary modules (Specific versions and output will vary):
```  
$ pip3 install -r requirements.txt
```  
## Running the script
From the virtual environment, you can run `python trimics.py -h` to see command help:
```
$ python trimics.py -h            
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
                                                 
```
Parameters:
+ `--infile FILENAME` - name of the `.ics` file with the starting calendar
+ `--outfile FILENAME` - name of the trimmed calendar `.ics` output file
+ `--verbose` - output the name of each event that is saved to the output file
+ `--strip-application-specific` - remove non-standard stuff.  This will clean a lot of extra crap out if the calendar events were created on an iOS device
+ `--months-before NUMBER` - the number of months to go back into the past when gathering calendar events.  If set to zero, the output calendar will only contain items that end after today

## Examples
Open an `.ics` calendar file and read all of the events.  Write an output file that contains all events that end anytime after 12 months ago (and into the future):
```  
$ python trimics.py --infile ./originalCalendar.ics --outfile trimmed.ics --months-before 12
Read 2693 events from './originalCalendar.ics'
Wrote 489 events to 'trimmed.ics'
```  
Of the 2693 items in the calendar, only 489 of those end after (12 months from right now).  The size of the two calendars are:
```   
$ ls -l *.ics     
-rw-rw-r-- 1 matty matty 2790543 May 12 14:41 originalCalendar.ics
-rw-rw-r-- 1 matty matty  702073 May 12 14:43 trimmed.ics
```  
The output file is 25% of the size of the input file.  That's a nice reduction.  To take that even further, remove all of the Apple-specific calendar extension crap:
```  
$ python trimics.py --infile ./originalCalendar.ics --outfile trimmed.ics --months-before 12 --strip-application-specific
Read 2693 events from './originalCalendar.ics'
Wrote 489 events to 'trimmed.ics'
```  
Again, 489 of the 2693 events were written out to the file.  The size difference, however, is more significant:
```  
$ ls -l *.ics                                                                               
-rw-rw-r-- 1 matty matty 2790543 May 12 14:41 originalCalendar.ics
-rw-rw-r-- 1 matty matty  196055 May 12 14:51 trimmed.ics
```  
The output file has the same number of events, but is only 7% the size of the input file!!  When that file is imported into another calendaring application (like Google calendar), all of the information, reminders, descriptions, etc. still exist - it's just missing the Apple-specific metadata that isn't needed.
