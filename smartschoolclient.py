import json
import logging
import colorlog
import requests
from xml.etree import ElementTree
import websocket
from uuid import uuid4


class ApiException(Exception):
    pass


class SmartSchoolClient:
    def __init__(self, domain, phpsessid, pid, user_id, loglevel=logging.DEBUG, received_message_callback=None):
        self.domain = domain
        self.phpsessid = phpsessid
        self.pid = pid
        self.user_id = user_id
        self.received_message_callback = received_message_callback

        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )

        self.api_logger = colorlog.getLogger("Core/API")
        self.api_logger.addHandler(handler)
        self.api_logger.setLevel(loglevel)

        self.websocket_logger = colorlog.getLogger("Core/Websocket")
        self.websocket_logger.addHandler(handler)
        self.websocket_logger.setLevel(loglevel)

        self.user_token = self.get_token_from_api()

    # general stuff
    def get_token_from_api(self):
        self.api_logger.info("Requesting token from API")
        self.api_logger.debug("Sending request to get token")
        response = requests.get(
            f'https://{self.domain}/Topnav/Node/getToken',
            headers={
                'Cookie': f'PHPSESSID={self.phpsessid}; pid={self.pid}'
            },
            json={
                'userID': self.user_id
            }
        )
        if response.status_code == 200:
            self.api_logger.info("Token received")
            return response.text
        else:
            self.api_logger.error("Could not get token")
            raise ApiException("Could not get token")

    def find_users_by_name(self, name):
        self.api_logger.info("Requesting user from API")
        self.api_logger.debug("Sending request to get user")
        response = requests.post(
            f'https://{self.domain}/?module=Messages&file=searchUsers',
            headers={
                "Cookie": f"pid={self.pid}; PHPSESSID={self.phpsessid}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=f"val={name}&type=0&parentNodeId=insertSearchFieldContainer_0_0&xml=<results></results>"
        )
        if response.status_code == 200:
            self.api_logger.info("User received")
            root = ElementTree.fromstring(response.text)
            users = []
            for user_elem in root.findall('.//user'):
                user = {
                    'userID': user_elem.find('userID').text,
                    'text': user_elem.find('text').text,
                    'value': user_elem.find('value').text,
                    'selectable': user_elem.find('selectable').text,
                    'ssID': user_elem.find('ssID').text,
                    'classname': user_elem.find('classname').text,
                    'schoolname': user_elem.find('schoolname').text,
                    'picture': user_elem.find('picture').text
                }
                users.append(user)
            return users
        else:
            self.api_logger.error("Could not get user")
            raise ApiException("Could not get user")

    def list_messages(self):
        """
        Request messages from API
        Currently limited to maximum 50 messages
        :return:
        """
        self.api_logger.info("Requesting messages from API")
        self.api_logger.debug("Sending request to get messages")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'command': (
                '<request>'
                '<command>'
                '<subsystem>postboxes</subsystem>'
                '<action>message list</action>'
                '<params>'
                '<param name="boxType"><![CDATA[inbox]]></param>'
                '<param name="boxID"><![CDATA[0]]></param>'
                '<param name="sortField"><![CDATA[date]]></param>'
                '<param name="sortKey"><![CDATA[desc]]></param>'
                '<param name="poll"><![CDATA[false]]></param>'
                '<param name="poll_ids"><![CDATA[]]></param>'
                '<param name="layout"><![CDATA[new]]></param>'
                '</params>'
                '</command>'
                '</request>'
            )
        }

        response = requests.post(f'https://{self.domain}/?module=Messages&file=dispatcher', headers=headers, data=data)
        if response.status_code == 200:
            self.api_logger.info("Messages received")
            return self.parse_message_response(response.text)
        else:
            self.api_logger.error("Could not get messages")
            raise ApiException("Could not get messages")

    @staticmethod
    def parse_single_message_response(response_text):
        root = ElementTree.fromstring(response_text)
        message_elem = root.find('.//message')
        message = {
            'id': message_elem.find('id').text,
            'from': message_elem.find('from').text,
            'to': message_elem.find('to').text,
            'subject': message_elem.find('subject').text,
            'date': message_elem.find('date').text,
            'body': message_elem.find('body').text,
            'status': message_elem.find('status').text,
            'attachment': message_elem.find('attachment').text,
            'unread': message_elem.find('unread').text,
            'label': message_elem.find('label').text,
            'receivers': [receiver.text for receiver in message_elem.findall('receivers/to')],
            'ccreceivers': [receiver.text for receiver in message_elem.findall('ccreceivers/cc')],
            'bccreceivers': [receiver.text for receiver in message_elem.findall('bccreceivers/bcc')],
            'senderPicture': message_elem.find('senderPicture').text,
            'markedInLVS': message_elem.find('markedInLVS').text,
            'fromTeam': message_elem.find('fromTeam').text,
            'totalNrOtherToReciviers': message_elem.find('totalNrOtherToReciviers').text,
            'totalnrOtherCcReceivers': message_elem.find('totalnrOtherCcReceivers').text,
            'totalnrOtherBccReceivers': message_elem.find('totalnrOtherBccReceivers').text,
            'canReply': message_elem.find('canReply').text,
            'hasReply': message_elem.find('hasReply').text,
            'hasForward': message_elem.find('hasForward').text,
            'sendDate': message_elem.find('sendDate').text,
        }
        return message

    @staticmethod
    def parse_message_response(response_text):
        root = ElementTree.fromstring(response_text)
        messages = []
        for message_elem in root.findall('.//message'):
            message = {
                'id': message_elem.find('id').text,
                'from': message_elem.find('from').text,
                'from_image': message_elem.find('fromImage').text,
                'subject': message_elem.find('subject').text,
                'date': message_elem.find('date').text,
                'status': message_elem.find('status').text,
                'attachment': message_elem.find('attachment').text,
                'unread': message_elem.find('unread').text,
                'label': message_elem.find('label').text,
                'deleted': message_elem.find('deleted').text,
                'allow_reply': message_elem.find('allowreply').text,
                'allow_reply_enabled': message_elem.find('allowreplyenabled').text,
                'has_reply': message_elem.find('hasreply').text,
                'has_forward': message_elem.find('hasForward').text,
                'real_box': message_elem.find('realBox').text,
                'send_date': message_elem.find('sendDate').text
            }
            messages.append(message)
        return messages

    def get_message_by_id(self, message_id):
        self.api_logger.info("Requesting message from API")
        self.api_logger.debug(f"Sending request to get message with ID: {message_id}")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'command': (
                f'<request>'
                f'<command>'
                f'<subsystem>postboxes</subsystem>'
                f'<action>show message</action>'
                f'<params>'
                f'<param name="msgID"><![CDATA[{message_id}]]></param>'
                f'<param name="boxType"><![CDATA[inbox]]></param>'
                f'<param name="limitList"><![CDATA[true]]></param>'
                f'</params>'
                f'</command>'
                f'</request>'
            )
        }

        response = requests.post(f'https://{self.domain}/?module=Messages&file=dispatcher', headers=headers, data=data)
        if response.status_code == 200:
            self.api_logger.info("Message received")
            return self.parse_single_message_response(response.text)
        else:
            self.api_logger.error("Could not get message")
            raise ApiException("Could not get message")

    # websockets
    def ws_on_error(self, ws, error):
        self.websocket_logger.error(f"Error: {error}")

    def ws_on_close(self, ws, close_status_code, close_msg):
        self.websocket_logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")

    def ws_on_open(self, ws):
        self.websocket_logger.info("WebSocket connection opened")
        auth_message = {
            "type": "auth",
            "request": "checkToken",
            "token": self.user_token
        }
        ws.send(json.dumps(auth_message))

    def ws_on_message(self, ws, message):
        self.websocket_logger.debug(f"Received message: {message}")
        message_data = json.loads(message)
        message_type = message_data.get("type", None)
        message_text = message_data.get("text", None)

        if message_type is not None:
            if message_type == "auth":
                self.websocket_logger.info("Authentication successful!")
            elif message_type == "notificationListStart":
                self.websocket_logger.info("Notification list started.")
            elif message_type == "getNotificationConfig":
                config_message = {
                    "type": "setConfig",
                    "queueUuid": uuid4().hex,
                }
                ws.send(json.dumps(config_message))
        elif message_text is not None:
            if message_text == "pubsub message":
                message = message_data.get("message", None)
                if message is not None:
                    message = json.loads(message)
                    if message.get("type", None) == "notificationAlert":
                        if message.get("module", None) == "Messages":
                            sender = message.get("title", None)
                            description = message.get("description", None)
                            url = message.get("url", None)
                            userID = message.get("userID", None)
                            if sender is not None and description is not None and url is not None and userID is not None:
                                url = "https://" + self.domain + url[1:]
                                self.api_logger.info(
                                    f"Received message from {sender}: {description} ({url})"
                                )
                                if self.received_message_callback is not None:
                                    self.received_message_callback(sender, description, url, userID)

    def run_websocket(self):
        self.websocket_logger.info("Connecting to WebSocket")
        ws = websocket.WebSocketApp(
            "wss://nodejs-gs.smartschool.be/smsc/websocket",
            on_open=self.ws_on_open,
            on_message=self.ws_on_message,
            on_error=self.ws_on_error,
            on_close=self.ws_on_close
        )
        ws.run_forever()
