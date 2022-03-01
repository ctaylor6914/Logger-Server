#	FILE			: server.py
#	PROJECT			: NAD_A03
#	PROGRAMMER		: Mita Das & Colby Taylor
#	FIRST VERSION	: 2022-02-15
#	DESCRIPTION		: This is the server program which accepts clients' data and sends back response
#                     to client. This server will run continuously being able to accept
#                     multiple clients to be able to log messages from multiple clients and
#                     be able to determine if the sent message is in the correct format to be able to
#                     comply with the logging format. if there is an error an error message will be returned
#                     to the client so that they are aware of the error
#
#   AUTHOR          : StackOverflow (Ganesh Jagdale)
#   SOURCE          : https://stackoverflow.com/questions/20913440/connecting-python-socket-and-java-socket

import jpysocket
import socket
import helper
import time
import os
import datetime


def server_program():
    config = helper.read_config()
    host = config['IPSettings']['ipaddress']
    port = int(config['IPSettings']['port'])

    fileDir = config['Log']['filepath']
    fileName = config['Log']['filename']
    filePath = fileDir + fileName

    statsDir = config['Statistics']['statspath']

    s = socket.socket()                                             # Create Socket
    s.bind((host, port))                                            # Bind Port And Host
    s.listen(5)                                                     # Socket is Listening

    rateLimErr = 0

    print("***** Server Is Started and Listening *****")

    # Getting the current date/time and formatting it
    currentDateTime = datetime.datetime.now()
    currentDateTimeFormatted = currentDateTime.strftime("%b-%d-%Y-%H-%M-%S")

    # Taking a backup of the log file
    if os.path.isfile(filePath):
        os.rename(filePath, fileDir + "/log_" + currentDateTimeFormatted + ".txt")

    # Writing the file with details. This will reset the log file
    with open(filePath, "w") as logFile:
        logFile.write("***** Server Started at " + currentDateTimeFormatted + " and Listening *****\n")

    clientTimeDict = {}                                             # rate limiter dict

    # Waiting loop for the connection
    while True:
        error = 0
        response = ""
        
        connection, address = s.accept()                            # Accept the Connection
        #print("Connected To ", address)

        msgrecv = connection.recv(1024)                             # Receive msg
        msgrecv = jpysocket.jpydecode(msgrecv)                      # Decrypt msg
        #print("Received Data: ", msgrecv)                           # print msg to screen

        parsedInput = msgrecv.split('_')                            # split string by '_'
        try:
            logLevel = int(parsedInput[0])              # if logLevel is not a number
        except:                                         # throw an exception
            error = 1                                   # there was an error
            logLevel = 10                               # set loglevel to 10
            response = "Log Level Not an integer"       # build response

        try:
            clientID = int(parsedInput[2])              # try to parse client id
        except:
            error = 1                                   # set error status
            clientID = 1                                # client id = 1 to indicate error
            response += "ID not an Integer"             # add to response

        currentDateTimeTemp = datetime.datetime.now()   # get current time
        if error == 0:
            x = clientTimeDict.get(clientID)            # check dictionary if client id is there

            if x is None:                               # if no client id
                clientTimeDict.update({clientID: currentDateTimeTemp})  # create new entry
            else:
                oldTime = str(x)                        # make old time object a string
                oldSecTemp = oldTime.split(":")         # split string to get seconds
                oldSec = oldSecTemp[2].split(".")       # remove the "."
                oldSec = int(oldSec[0])                 # turn into an integer

                newTime = str(currentDateTimeTemp)              # get current time into a string
                newSplit = newTime.split(":")                   # split to get seconds
                newSec = newSplit[2].split(".")                 # remove anything after the "."
                newSec = int(newSec[0])                         # make an integer
                clientTimeDict[clientID] = currentDateTimeTemp  # update time on the client dictionary
                dif = newSec - oldSec
                if newSec == oldSec:                            # if another log within 1 sec
                    if rateLimErr == 0:                         # if this client hasn't already been limited
                        print("skipping log due to repeat logger")  # update server screen
                        print("***** Server Listening *****")
                        with open(filePath, "a") as logFile:
                            logFile.write(newTime+"_Rate Limiting Client_" + str(clientID) + "\n")  # on the first rate limit - log clientID has been limited
                        rateLimErr = 1                              # set rateLimErr to 1 to indicate client has been limited

                    msgsend = jpysocket.jpyencode("Error: Rate Limiting")  # Encrypt The Msg
                    connection.send(msgsend)  # Send Msg
                    continue
                else:
                    rateLimErr = 0 # reset limiter to 0 id oldSec and newSec dont equal



        if not (1 <= logLevel <= 10):                               # if log level is within range or not
            # send error message that log level out of range
            error = 1
            response += "Error - Log Level not in range"

        if not (1 <= clientID <= 10000):                            # check unique client ID
            # send error message unique id out of range
            error = 1
            response += "Error - ClientID not in range"

        if error == 0:
            response = "Info - Logging successful"
            with open(filePath, "a") as logFile:
                logFile.write(msgrecv + "\n")

        msgsend = jpysocket.jpyencode(response)                     # Encrypt The Msg
        connection.send(msgsend)                                    # Send Msg
        print("Send Data: ", msgsend)                               # print sent data

        print("***** Server Listening *****")

        # Generating the stats details by reading from the log file
        currentDateTime = datetime.datetime.now()
        currentDateTimeFormatted = currentDateTime.strftime("%b-%d-%Y")

        # Get all lines from the log file
        lines = []
        with open(filePath, "r") as logFile:
            lines = logFile.readlines()

        # Setting the nested dictionary
        parentClientDict = {}
        parentLogDict = {}

        # Reading lines and putting it in dictionary
        for line in lines:
            val = line.split("_")
            if len(val) >= 4:
                # For client level
                if val[2] in parentClientDict:
                    temp = int(parentClientDict[val[2]])
                    temp = str(temp + 1)
                    childClientDict = {val[2]: temp}
                else:
                    childClientDict = {val[2]: "1"}
                
                parentClientDict.update(childClientDict)

                # For log level
                if val[0] in parentLogDict:
                    temp = int(parentLogDict[val[0]])
                    temp = str(temp + 1)
                    childLogDict = {val[0]: temp}
                else:
                    childLogDict = {val[0]: "1"}

                parentLogDict.update(childLogDict)

        # Write to the stats file
        statsFilePath = statsDir + "/stats_" + currentDateTimeFormatted + ".txt"
        with open(statsFilePath, "w") as statsFile:
            # For client level
            statsFile.write("********** Statistics Based on Clients **********\n")
            statsFile.write("-------------------------------------------------\n")
            for key in parentClientDict:
                statsFile.write("Client ID: " + key + " , Total Logs: " + parentClientDict[key] + "\n")

            # For log level
            statsFile.write("\n\n")
            statsFile.write("********* Statistics Based on Log-level *********\n")
            statsFile.write("-------------------------------------------------\n")
            for key in parentLogDict:
                statsFile.write("Log-level ID: " + key + " , Total Logs: " + parentLogDict[key] + "\n")

        # Close connection
        if msgrecv == 'quit':
            s.close()
            print("Connection Closed.")
            break


if __name__ == '__main__':
    server_program()                                                # main program call
