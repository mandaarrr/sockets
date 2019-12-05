#Reference for handling sockets: https://pythonprogramming.net/sockets-tutorial-python-3
#2019-AC31008-Networks-Dignan-Duguid-Tamhane

#import various libraries for use later in code
import socket
import select
import string
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
    
else:
    print("Only {} arguments given".format(len(arg_split)))
    print("Please enter arguments in form 'python3 server.py IP PORT'")
    exit(0)

PORT = int(PORT)
print("IP: {}".format(IP))
print("PORT: {}".format(PORT))

#get IP dynamically
#try:
  #  host_name = socket.gethostname()
 #   IP = socket.gethostbyname(host_name)
#except:
    #print("Couldn't get dynamic IP")


#create server socket, bind to IP and PORT, then tell it to listen
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]

# Dictionary of connected clients - socket info as a key, username and nickname as data
clients = {}

# Dictionary of channels - channel as key, list of client ports as data
channels = {"#test":[]}


print("\nListening for connections on {}:{} \n".format(IP, PORT))

#Method for sending a message from one person to another
def sendMessage(client_socket, notified_socket, notified_details, message):
    
    #Get client port from client socket details via string manipulation
    client_details = str(client_socket)
    client_details = client_details[client_details.find("raddr"):]
    client_details = client_details[client_details.find(",")+1:-2]
    client_details = ''.join(client_details.split())   
    
    #Split message into different sections 
    message_split = message.decode("utf-8")
    message_split = message_split.split(" ")
    
    #If PRVIMSG is found by the server
    if message_split[0].find("PRIVMSG") != -1:

        #For each client in clients dictionary, get the port number and get rid of whitespace
        #i = client socket info in clients dictionary
        #v = nickname:username info in clients dictionary
        for i, v in  clients.items():
            temp = str(i)
            temp = temp[temp.find("raddr"):]
            temp = temp[temp.find(",")+1:-2]
            temp = ''.join(temp.split())

            #If the client's port is the one who's sending the details            
            if temp in notified_details:

                #Form the message that's to be returned to hexchat/bot client. Get username from v
                message_value = ":" + v[v.find(":") + 1:] + "!" + v[:v.find(":")] + "@" + str(IP) + " PRIVMSG " + str(message_split[1]) + " " + message_split[2] + "\r\n"
                message_value = message_value.encode("utf-8")

                #Send message
                client_socket.send(message_value)

#Function for listing channels in server console
def listChannels():

    #output all items in channels dictionary
    print("List of Channels:")
    for i,v in channels.items():
        print(i,v)
    print("")

#Program goes here to add entry to channel dictionary, and send info to hexchat.
#Receives the person asking to join channel via sender details parameter, and the channel name via message_data
def addChannel(sender_details, message_data):

    channelName = message_data

    #get rid of whitespace
    channelName = ''.join(channelName.split())

    #add a hashtag at the start of the channel name if not already there
    if channelName[0] != "#":
        channelName = "#" + channelName

    #check if channel is new or not by looping through channels and counting how mamy times it appears
    count = 0
    for i, v in channels.items():

        if i != channelName:
            count += 1
            if count == len(channels):
                print("{} is now joining {}".format(sender_details, channelName))

                channels[channelName] = [sender_details]
                break
        else:
            #User is already in dictionary
            if sender_details in v:
                print("Already in channel")
            else:
                print("{} is joining {}".format(sender_details, channelName))
                channels[channelName].append(sender_details) #Add new details to channels dictionary
                break

    print("")

    #Send neccesary info back to hexchat to join the channel
    for i, v in clients.items():
        if sender_details in str(i):
            #Form the message code to be sent back, getting names from the dictionarys
            line = ":" + v[v.find(":") + 1:] + "!" + v[:v.find(":")] + "@" + str(IP) + " JOIN " + channelName + "\r\n"
            line = line.encode('utf-8')
            if "ProBot" not in v: 
                print("JOINING: {}".format(line))
                notified_socket.send(line)

    #call remove user with new channel user details to see if they're in any other channels, and remove if so     
    removeUser(sender_details, channelName, nickname, username)
    listChannels()

#Method used to delete any channels with no clients in them
def checkChannels():
    
    for i,v in channels.items():
        if len(v) == 0:
            if i != "#test":
                print('Deleting {}'.format(i))
                del channels[i]
                break

#Method removes a user from channel when they join another channel
def removeUser(sender_details, channelName, nickname, username):
    
    for i,v in channels.items():
        if i != channelName:
            if sender_details in v:
                v.remove(sender_details)
                print("Removed {} from {}".format(sender_details, i))

    checkChannels()

#Command check is used to call neccesary functions whenever a command message is sent from client
def commandCheck(sender_details, message_data):
    if message_data.find("JOIN") == 0:
        addChannel(sender_details, message_data[5:])
        
# Handles message receiving
def receive_message(client_socket):

    #If client sent message, return it. Otherwise, the client left abruptly (ctr-c, etc) and handle error 
    try:
        return client_socket.recv(1024)
    except:
        print("Client exited abruptly")
        return False

#When hexchat user leaves, get rid of their details from channels dictioanry
def wipeUser(notified_details):

    for i, v in channels.items():
        if notified_details in v:
            v.remove(notified_details)

    checkChannels()

#Main loop, looks for joining sockets
while True:

    #Receive socket information 
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    # Loop continously through notified sockets
    for notified_socket in read_sockets:

        # If any of the sockets is a new socket, get their details into the system
        if notified_socket == server_socket:
            
            #Get the new connection, and store its unique details in client_socket and client_address, respectively
            client_socket, client_address = server_socket.accept()

            print('\Received new connection from {}:{}\n'.format(*client_address))
            
            #Get user ino from socket via receive message method
            user = receive_message(client_socket)

            #If message includes CAP LS 302 and NICK in same line, it will be the bot sending the information
            if str(user).find("CAP") != -1:
                if str(user).find("NICK") != -1:

                    username = "ProBot"
                    nickname = "ProBot"
                #Otherwise, if get next line of message for hexchat client information (NICK and USER)
                else:
                    user = receive_message(client_socket)

                    realname = str(user)
                    realname = realname[realname.find(":") + 1: -5 ]
                    print("Real Name: {}".format(realname))

                    username = str(user)
                    username = username.split(" ")
                    username = username[2]
                    print("Username: {}".format(username))

                    nickname = str(user)
                    nickname = nickname[nickname.find("NICK") + 5: nickname.find("\\")]
                    print("Nickname: {}".format(nickname))


            # If user is false, the client left without setting their name 
            if user is False:
                continue

            # Add new socket to socket list
            sockets_list.append(client_socket)

            #Save the new client socket details in client dictionary, with client socket as key and username:nickname as data
            clients[client_socket] = username + ":" + nickname
            
            #Get client's unique port
            client_details = str(client_address)
            client_details = client_details[client_details.find(",")+1:-1]
            client_details = ''.join(client_details.split())

            #If the bot is connecting, get his details and add him to the default #test channel
            if "ProBot" in username:
                addChannel(client_details, "#test")
                bot_details = client_details

            #List the channels for the server log
            listChannels();

        #If socket already in server, it means they're sending a message
        else:
            # Receive message
            message = receive_message(notified_socket)

            #Get the messaging socket's port number
            notified_details = str(notified_socket)
            notified_details = notified_details[notified_details.find("raddr"):]
            notified_details = notified_details[notified_details.find(",")+1:-2]
            notified_details = ''.join(notified_details.split())

            # If the message is false or the client sent back "QUIT", close their connection and wipe their details from the program
            if message is False or str(message).find("QUIT") != -1:
                
                print('Closed connection from: {}'.format(nickname))

                wipeUser(notified_details)

                # Remove from socket list
                sockets_list.remove(notified_socket)
            
                # Remove them from our list of clients
                del clients[notified_socket]

                continue
            
            # Get the client from notified socket, so we will know who sent the message
            user = clients[notified_socket]

            print("Received message from {}".format(notified_details))

            #Decode the message            
            message_data = message.decode('utf-8')

            #if the message has a keyword, call commandCheck to deal with it
            if message_data.find("JOIN") != -1:
                commandCheck(notified_details, message_data)
            #Otherwise, its a normal message
            else:
                # Iterate over connected clients and broadcast message
                for client_socket in clients:

                    # Make sure the person sneding the message doesn't receive it, only the other clients
                    if client_socket != notified_socket:
                        #If everything went fine, don't loop again, just break out of the loop and wait again
                        if sendMessage(client_socket, notified_socket, notified_details, message) == 1:
                            break

#These lines handle exceptions incase something goes wrong in the loop
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]