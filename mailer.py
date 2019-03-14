# coding: utf-8

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
def sendMail(attach, credentials):
        text = "something moved !"
        msg = MIMEMultipart()
        msg['From'] = "pywatcher"
        msg['To'] = recv
        msg['Subject'] = "MotionDetect Alert !"
        msg.attach(MIMEText(text))
        msg.attach(MIMEImage(file(attach).read()))

        serv = smtplib.SMTP_SSL('smtp.domain.tld', 465)  # le server smtp
        serv.ehlo()
        serv.login(user, passwd)
        serv.sendmail(user, recv, msg.as_string())
        serv.close()
