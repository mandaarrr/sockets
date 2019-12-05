#Reference for Sockets: https://pythonprogramming.net/sockets-tutorial-python-3
#2019-AC31008-Networks-Dignan-Duguid-Tamhane

import socket
import select
import errno
import sys
import datetime
import random
import sys


#Get IP and PORT from user from command line
IP = ""
PORT = 0
arg_split = str(sys.argv).split(" ")

if len(arg_split) == 3:
    IP = str(arg_split[1])
    IP = IP[IP.find("'") + 1: IP.find(",") -1]
    PORT = str(arg_split[2])
    PORT = PORT[PORT.find("'") + 1: PORT.find("'") -2]
    PORT = int(PORT)
    
else:
    print("Only {} arguments given".format(len(arg_split)))
    print("Please enter arguments in form 'python3 server.py IP PORT'")
    exit(0)

print("IP: {}".format(IP))
print("PORT: {}".format(PORT))

my_username = "ProBot"


#Function to get Day of the Week from dictionary via key paramter, i
def getDayOfTheWeek(i):
    dayDict={
            0:'Sunday',
            1:'Monday',
            2:'Tuesday',
            3:'Wednesday',
            4:'Thursday',
            5:'Friday',
            6:'Saturday'
            }
    return dayDict.get(i,"Today is someday. I'm just a bot and I forgot the days of the week.")

#function used to get random vact from a dictionary, via a key (i parameter)
def randomFactGenerator(i):
    #Facts - Source: https://www.thefactsite.com/top-100-random-funny-facts/
    factDict={
        0:'The_average_person_will_spend_six_months_of_their_life_waiting_for_red_lights_to_turn_green',
        1:'Nearly_30,000_rubber_ducks_were_lost_at_sea_in_1992_and_are_still_being_discovered_today',
        2:'Bottled_water_expiration_dates_are_for_the_bottle,_not_the_water.',
        3:'Rich_Russians_hire_fake_ambulances',
        4:'NASCAR_drivers_can_lose_up_to_10_pounds_in_sweat_due_to_high_temperatures_during_races',
        5:'29th_May_is_officially_“Put_a_Pillow_on_Your_Fridge_Day"',
        6:'The_United_States_Navy_has_started_using_Xbox_controllers_for_their_periscopes',
        7:'Honeybees_can_recognize_human_faces',
        8:'A_swarm_of_20,000_bees_followed_a_car_for_two_days_because_their_queen_was_stuck_inside',
        }
    return factDict.get(i,"Well, I'm just an awkward fact-stating ProBot")


# Creating a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connecting to a given ip and port
client_socket.connect((IP, PORT))

#Sending neccesary details to server so bot can join
nickname = "CAP LS 302\r\n"
user = "NICK " + my_username + "\r\nUSER " + my_username + " " + my_username + " " + str(IP) + " :" + my_username + "\r\n"

#Joining the #test channel - Change "test" to change the bot channel
channel = "JOIN " + "#test\r\n"

#Sending the set parameters through the socket
client_socket.send(nickname.encode("UTF-8"))
client_socket.send(user.encode("UTF-8"))
client_socket.send(channel.encode("UTF-8"))

#Creating an empty string for the bot to send
botmessage = ""

#Loop to recieve messages
while True:

    #While there is a message
    while True:

            #receiv message from server/hex chat, decode, get sender information (nickname), and usern (username), using string manipulation on the message and assigning the values
            message = client_socket.recv(2048)
            message = message.decode("utf-8")
            sender = message[message.find(":") + 1:message.find("!")]
            usern = message[message.find("!") + 1:message.find("@")]
            
            print(message)

            # Replying to the !time command via datetime library
            if message.find("!time") != -1:
                currenthour = datetime.datetime.now().time().hour
                currentminute = datetime.datetime.now().time().minute
                currentsecond = datetime.datetime.now().time().second
                botmessage = (f'{currenthour}:{currentminute}:{currentsecond}')
            
            #Replying to the !day command 
            elif message.find("!day") != -1:
                dayindex = datetime.datetime.now().isoweekday()
                currentday = getDayOfTheWeek(dayindex)
                botmessage = (f'{currentday}.')
            
            #Replying to the !date command
            elif message.find("!date") != -1:
                currentdate = datetime.datetime.now().day
                currentmonth = datetime.datetime.now().month
                currentyear = datetime.datetime.now().year
                botmessage = (f'{currentdate}-{currentmonth}-{currentyear}')
            
            #Replying to the !help command, sends back list of commands that bot can perform
            elif message.find("!help") != -1:
                botmessage = (f'!time,!date,!day')
            
            #Checking if botmessage is still empty or filled with one of the command outputs
            if botmessage:  
                message = "PRIVMSG " + "#test" + " :" + botmessage + "\r\n"
                botmessage = "" #Resetting the bot output message before ending the loop
                message = message.encode('utf-8')
                client_socket.send(message)

            #Replying with a random fact if the message sent isn't a command
            elif message.find("#test") == -1:
                botmessage = randomFactGenerator(random.randint(0,8)) #get fact from method
                botmessage = "PRIVMSG " + sender + " :" + botmessage #form message to client
                botmessage = botmessage.encode('utf-8') 
                client_socket.send(botmessage) #send message via socket