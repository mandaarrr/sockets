import socket
import select
import string

currentChannel = ""

HEADER_LENGTH = 10

IP = ""

# Function to display hostname and 
# IP address 
def get_Host_name_IP(): 
    global IP
    try: 
        host_name = socket.gethostname() 
        IP = socket.gethostbyname(host_name)
    except: 
        print("Unable to get Hostname and IP") 
  
# Driver code 
get_Host_name_IP() #Function call 

PORT = 8000
#hello


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()


# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}
channels = {"#global":[]}

print("Listening for connections on {}:{}".format(IP, PORT))

def sendMessage(client_socket, user_header, user_value, message_header, message_value):
    user_value = user_value.decode("utf-8")

    user_channel = ""

    for i, v in channels.items():
        if user_value in v:
            user_channel = i

    


def listChannels():

    print("")
    print("List of Channels:")
    for i,v in channels.items():
        print(i,v)

def addChannel(user_data, message_data):
    global currentChannel
    channelName = message_data

    #get rid of whitespace
    channelName = ''.join(channelName.split())

    #add a hashtag at the start of the channel name if not already there
    if channelName[0] != "#":
        channelName = "#" + channelName

    #check if channel is new or not
    count = 0
    for i in channels:

        if i != channelName:
            count += 1
            if count == len(channels):
                channels[channelName] = [user_data]
                break
        else:
            channels[channelName].append(user_data)

    print("{} is joining {}".format(user_data, channelName))

    removeUser(user_data, channelName)

def checkChannels():
    
    for i,v in channels.items():
        if len(v) == 0:
            if i != "#global":
                print('Deleting {}'.format(i))
                del channels[i]
                break

def removeUser(user_data, channelName):

    for i,v in channels.items():
        if i != channelName:
            if user_data in v:
                v.remove(user_data)
                print("Removed {} from {}".format(user_data, i))

    checkChannels()

def leaveChannel():
    global currentChannel
    print("You have left {}".format(currentChannel))
    currentChannel = ""


def commandCheck(user_data, message_data):
    if message_data.find("JOIN") == 0:
        addChannel(user_data, message_data[5:])
    elif message_data.find("LIST") == 0:
        listChannels()
    elif message_data.find("LEAVE") == 0:
        leaveChannel()
        

# Handles message receiving
def receive_message(client_socket):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

while True:

    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            # Accept new connection
            # That gives us new socket - client socket, connected to this given client only, it's unique for that client
            # The other returned object is ip/port set
            client_socket, client_address = server_socket.accept()

            # Client should send his nameright away, receive it
            user = receive_message(client_socket)
            realname = receive_message(client_socket)

            # If False - client disconnected before he sent his name
            if user is False:
                continue

            # Add accepted socket to select.select() list
            sockets_list.append(client_socket)

            # Also save username and username header
            clients[client_socket] = user

            print('Accepted new connection from {}:{}'.format(*client_address))
            print('Username: {}, Real Name: {}'.format(user['data'].decode('utf-8'), realname['data'].decode('utf-8')))
            addChannel(user['data'].decode('utf-8'), "#global")
        # Else existing socket is sending a message
        else:
            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue
            
            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            user_data = user["data"].decode('utf-8')
            message_data = message["data"].decode('utf-8')

            print("Received message from {}: {}".format(user_data, message_data))
            #print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}'

            commandCheck(user_data, message_data)
 
            # Iterate over connected clients and broadcast message
            for client_socket in clients:

                # But don't sent it to sender
                if client_socket != notified_socket:

                    print("Client socket: {}".format(client_socket))
                    
                    
                    """print("")
                    print("Clients: {}".format(clients))
                    print("")
                    print("User: {}".format(user))"""

                    sendMessage(client_socket, user['header'], user['data'], message['header'], message['data'])

                    # Send user and message (both with their headers)
                    # We are reusing message header sent by sender, and saved username header send by user when he connected
                    
                    #HERE
                    #client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]