#!/usr/bin/python
# -*- coding: utf-8 -*-

import cv2.cv as cv
from datetime import datetime
import time

import smtplib
from email.mime.text import MIMEText


##
# TODO mailSending : - ne pas avoir à écrire en dur le mot de passe
#                    - piece jointe : une photo de la scene
#
class MotionDetectorAdaptative():
    """ detecteur de mouvement basé sur openCV"""    
    def onChange(self, val): #gere le changement de valeur par l'user, threshold = sensibilitée
        self.threshold = val
    
    def sendMail(self):
        user = 'mail@sending.tld' #adresse mail pour l'envoie
        passwd = 'your passwd' # mot de passe de l'adresse d'envoie
        recv = 'you@recveive.tld' # adresse qui va recevoir le mail 
        text = "something as moved behind me !"
        msg = MIMEText(text)
        msg['From'] = user
        msg['To'] = recv
        msg['Subject'] = "MotionDetect Alert !"
        serv = smtplib.SMTP('smtp.mailsever.tld', 587) #le server smtp de l'adresse d'envoi
        serv.ehlo()
        serv.login(user, passwd)
        serv.sendmail(user, recv, msg.as_string())
        serv.close()


    def __init__(self,threshold=10, doRecord=True, showWindows=True):
        self.writer = None
        self.font = None
        self.doRecord=doRecord #enregistrer en cas de mouvement ou pas
        self.show = showWindows #montrer la video ou pas
        self.frame = None
    
        self.capture=cv.CaptureFromCAM(0) #active et capture les mages depuis la webcam par defaut
        self.frame = cv.QueryFrame(self.capture) #prendre une frame par la cam
        if doRecord:#si on prévoit d'enregistrer, on prepare ce qu'il faut
            self.initRecorder()
        
        self.gray_frame = cv.CreateImage(cv.GetSize(self.frame), cv.IPL_DEPTH_8U, 1) #frame en noir et blanc
        self.average_frame = cv.CreateImage(cv.GetSize(self.frame), cv.IPL_DEPTH_32F, 3) # image moyenne de toute les image precedentes
        self.absdiff_frame = None
        self.previous_frame = None
        
        self.surface = self.frame.width * self.frame.height
        self.currentsurface = 0
        self.currentcontours = None
        self.threshold = threshold
        self.isRecording = False
        self.trigger_time = 0 #Hold timestamp of the last detection
        
        if showWindows:
            cv.NamedWindow("Image")#affichage de la video
            cv.CreateTrackbar("Detection treshold: ", "Image", self.threshold, 100, self.onChange) # affichage de la barre de defilment
        
    def initRecorder(self): 
        """ cree le videoWriter"""
        codec = cv.CV_FOURCC('M', 'J', 'P', 'G') #format MJPG
        self.writer=cv.CreateVideoWriter(datetime.now().strftime("%b-%d_%H:%M:%S")+".avi", codec, 5, cv.GetSize(self.frame), 1)
        #FPS set to 5 because it seems to be the fps of my cam but should be ajusted to your needs
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 2, 8) #Creates a font

    def run(self):
        """ boucle principale d'execution"""
        started = time.time()
        while True:
            
            currentframe = cv.QueryFrame(self.capture)
            instant = time.time() #Get timestamp o the frame
            
            self.processImage(currentframe) #Process the image
            
            if not self.isRecording: #si on n'enregistre pas
                if self.somethingHasMoved(): #et que quelquechose bouge ... 
                    self.trigger_time = instant #Update trigger
                    if instant > started +10:# on laisse 10 secondes a la cam pour qu'elle  s'ajuste en luminosité etc ... 
                        print "Something is moving !"
                        self.sendMail()
                        if self.doRecord: #set isRecording=True only if we record a video
                            self.isRecording = True
                #on dessine les contours en temps réel
                cv.DrawContours (currentframe, self.currentcontours, (0, 0, 255), (0, 255, 0), 1, 2, cv.CV_FILLED) 
            else:
                if instant >= self.trigger_time +10: #Record during 10 seconds
                    print "Stop recording"
                    self.isRecording = False
                else:
                    cv.PutText(currentframe,datetime.now().strftime("%b %d, %H:%M:%S"), (25,30),self.font, 0) #Put date on the frame
                    cv.WriteFrame(self.writer, currentframe) #Write the frame
            
            if self.show:
                cv.ShowImage("Image", currentframe) #créé la fenetre
                
            c=cv.WaitKey(5) % 0x100 #on attends une entrée clavier ou 5sec avant de relancer

            if c==27 or c == 10: #Break if user enters 'Esc'.
                break            
    
    def processImage(self, curframe):
        """ methode modifiant l'image de maniere a la rendre utilisable par qu'atres fonctions """
        cv.Smooth(curframe, curframe) #permet de ne pas prendre en compte les pixels isolés
            
        if not self.absdiff_frame: #For the first time put values in difference, temp and moving_average
            self.absdiff_frame = cv.CloneImage(curframe)
            self.previous_frame = cv.CloneImage(curframe)
            cv.Convert(curframe, self.average_frame) #Should convert because after runningavg take 32F pictures
        else:
            cv.RunningAvg(curframe, self.average_frame, 0.05) #calcul de la moyenne
            
        cv.Convert(self.average_frame, self.previous_frame) #Convert back to 8U frame
            
        cv.AbsDiff(curframe, self.previous_frame, self.absdiff_frame) # moving_average - curframe
            
        cv.CvtColor(self.absdiff_frame, self.gray_frame, cv.CV_RGB2GRAY) #Convert en gris pour appliquer le threshold
        cv.Threshold(self.gray_frame, self.gray_frame, 50, 255, cv.CV_THRESH_BINARY)

        cv.Dilate(self.gray_frame, self.gray_frame, None, 15) #to get object blobs
        cv.Erode(self.gray_frame, self.gray_frame, None, 10)

            
    def somethingHasMoved(self):
        """ methode gerant l'apparition d'un mouvement devant la cam """
        
        # Find contours
        storage = cv.CreateMemStorage(0)
        contours = cv.FindContours(self.gray_frame, storage, cv.CV_RETR_EXTERNAL, cv.CV_CHAIN_APPROX_SIMPLE)

        self.currentcontours = contours #Save contours
        
        while contours: #For all contours compute the area
            self.currentsurface += cv.ContourArea(contours)
            contours = contours.h_next()
        
        avg = (self.currentsurface*100)/self.surface #Calculate the average of contour area on the total size
        self.currentsurface = 0 #Put back the current surface to 0
        
        if avg > self.threshold:
            return True
        else:
            return False

        
if __name__=="__main__":
    detect = MotionDetectorAdaptative(doRecord=True)
    detect.run()
