# Motion detector


A snippet I found on a linux magazine back in 2012, to which I added the ability to send an email notification

        pip install -r requirement.txt
        ./MotionDetectAdaptative 


Dependencies : 

- python
- python-opencv
- a camera

use your camera as a motion detector, can record a (poor quality) 10s video and 
send mail with a capture as attachment.

## TODO 

 * refactor this Frankenstein monster
 * give it a more 2019ish flavor
 * polish email notification 
 * is sms alerting REALLY a good idea ? 
 * ensure it become as evil as a daemon 
 * find a container for this daemon and ask a docker to send it in high seas
