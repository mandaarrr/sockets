import socket
import select
import string

currentChannel = ""

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 8000


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()


# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}
channels = {"#global":[]}

'''
- user joins a channel
- program checks if they are in any channel besides the channel they just joined
- if they're in other channel, kick them out and append them to new one
'''

print(f'Listening for connections on {IP}:{PORT}...')

def listChannels():

    print("")
    print("List of Channels:")
    for i in range(len(channels)):
        print("{} - {}".format(i + 1, channels[i]))
    print("")

def addChannel(user_data, message_data):
    global currentChannel
    channelName = message_data

    #get rid of whitespace
    channelName = ''.join(channelName.split())

    #add a hashtag at the start of the channel name if not already there
    if channelName[0] != "#":
        channelName = "#" + channelName


    count = 0
    for i in channels:
        if i != channelName:
            count += 1
            if count == len(channels):
                channels[channelName] = [user_data]
                print("{} is joining {}".format(user_data, channelName))
                break
        else:
            print("{} is joining {}".format(user_data, channelName))
            channels[channelName].append(user_data)

    removeUser(user_data, channelName)
    

    '''
    for k, v in user.items():
        if v.decode('utf-8').find(user_data) != -1:
            user['ChannelName'] = currentChannel
            print("yeet")
            break
    '''

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


def getChannelInfo():
    if currentChannel != "":
        print("You are in {}".format(currentChannel))
    else:
        print("You are not in a channel")

def leaveChannel():
    global currentChannel
    print("You have left {}".format(currentChannel))
    currentChannel = ""


def commandCheck(user_data, message_data):
    if message_data.find("JOIN") == 0:
        addChannel(user_data, message_data[5:])
    elif message_data.find("LIST") == 0:
        listChannels()
    elif message_data.find("INFO") == 0:
        getChannelInfo()
    elif message_data.find("LEAVE") == 0:
        leaveChannel()
    elif message_data.find("LOOP") == 0:
        for i,v in channels.items():
            print(i,v)
        

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

            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            user_data = user["data"].decode('utf-8')
            message_data = message["data"].decode('utf-8')
        
            commandCheck(user_data, message_data)
 
            # Iterate over connected clients and broadcast message
            for client_socket in clients:

                # But don't sent it to sender
                if client_socket != notified_socket:

                    # Send user and message (both with their headers)
                    # We are reusing here message header sent by sender, and saved username header send by user when he connected
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]

