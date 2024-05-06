"""
SmartSchool client API class
"""
import json
import logging
from xml.etree import ElementTree
from uuid import uuid4
import colorlog
import requests
import websocket

OFFICE365_SSO_INIT_URI = "/login/sso/init/office365"


class ApiException(Exception):
    """
    Api exception
    """


class AuthException(ApiException):
    """
    Auth exception
    """


class SmartSchoolClient:
    """
    SmartSchool client

    Args:
        domain: SmartSchool domain
        loglevel: logging level

    Attributes:
        domain: SmartSchool domain
        phpsessid: PHPSESSID
        pid: pid
        user_id: user id
        received_message_callback: callback function

        api_logger: logger for API
        websocket_logger: logger for Websocket
        auth_logger: logger for Authentication

    Methods:
        get_token_from_api()
        get_messages_from_api()
        get_message_by_id(message_id)
        list_messages()
        authenticate()
        run_websocket()
    """

    def __init__(self, domain, loglevel=logging.DEBUG):
        self.domain = domain
        self.phpsessid = None
        self.pid = None
        self.user_id = None
        self.received_message_callback = None
        self.user_token = None

        colorlog_handler = colorlog.StreamHandler()
        colorlog_handler.setFormatter(
            colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )

        self.api_logger = colorlog.getLogger("Core/API")
        self.api_logger.addHandler(colorlog_handler)
        self.api_logger.setLevel(loglevel)

        self.websocket_logger = colorlog.getLogger("Core/Websocket")
        self.websocket_logger.addHandler(colorlog_handler)
        self.websocket_logger.setLevel(loglevel)

        self.auth_logger = colorlog.getLogger("Core/Authentication")
        self.auth_logger.addHandler(colorlog_handler)
        self.auth_logger.setLevel(loglevel)

    def get_token_from_api(self):
        """
        Get token from API
        """
        self.api_logger.info("Requesting token from API")
        self.api_logger.debug("Sending request to get token")
        response = requests.get(
            f'https://{self.domain}/Topnav/Node/getToken',
            headers={
                'Cookie': f'PHPSESSID={self.phpsessid}; pid={self.pid}'
            },
            json={
                'userID': self.user_id
            },
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Token received")
            self.user_token = response.text
            return self.user_token
        self.api_logger.error("Could not get token")
        raise ApiException("Could not get token")

    def find_users_by_name(self, name):
        """
        Find users by name
        """
        self.api_logger.info("Requesting user from API")
        self.api_logger.debug("Sending request to get user")
        response = requests.post(
            f'https://{self.domain}/?module=Messages&file=searchUsers',
            headers={
                "Cookie": f"pid={self.pid}; PHPSESSID={self.phpsessid}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=f"val={name}&type=0&parentNodeId=insertSearchFieldContainer_0_0&xml=<results></results>",
            timeout=10
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

        response = requests.post(
            f'https://{self.domain}/?module=Messages&file=dispatcher',
            headers=headers,
            data=data,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Messages received")
            return self.parse_message_response(response.text)
        self.api_logger.error("Could not get messages")
        raise ApiException("Could not get messages")

    @staticmethod
    def parse_single_message_response(response_text):
        """
        Parse a single message from API response
        """
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
            'bccreceivers': [receiver.text for receiver in
                             message_elem.findall('bccreceivers/bcc')],
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
        """
        Parse messages from API response
        """
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
        """
        Get message by ID
        """
        self.api_logger.info("Requesting message from API")
        self.api_logger.debug("Sending request to get message with ID %s", message_id)
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

        response = requests.post(
            f'https://{self.domain}/?module=Messages&file=dispatcher',
            headers=headers,
            data=data,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Message received")
            return self.parse_single_message_response(response.text)
        self.api_logger.error("Could not get message")
        raise ApiException("Could not get message")

    def get_courses(self):
        """
        Get courses
        """
        self.api_logger.info("Requesting courses from API")
        self.api_logger.debug("Sending request to get courses")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/json, text/javascript, */*;',
            'X-Requested-With': 'XMLHttpRequest',
        }
        response = requests.post(
            f'https://{self.domain}/Topnav/getCourseConfig',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Courses received")
            courses_json = json.loads(response.text)
            return courses_json['own']
        self.api_logger.error("Could not get courses")
        raise ApiException("Could not get courses")

    # websockets
    def ws_on_error(self, _, error):
        """
        Websocket error
        """
        self.websocket_logger.error("Error: %s", error)

    def ws_on_close(self, _, close_status_code, close_msg):
        """
        Websocket close
        """
        self.websocket_logger.info("WebSocket connection closed: %s - %s", close_status_code,
                                   close_msg)

    def ws_on_open(self, ws):
        """
        Websocket open
        """
        self.websocket_logger.info("WebSocket connection opened")
        auth_message = {
            "type": "auth",
            "request": "checkToken",
            "token": self.user_token
        }
        ws.send(json.dumps(auth_message))

    def ws_on_message(self, ws, message):
        """
        Websocket message
        """
        self.websocket_logger.debug("Received message: %s", message)
        message_data = json.loads(message)
        message_type = message_data.get("type", None)
        message_text = message_data.get("text", None)
        message_request = message_data.get("request", None)

        if message_type is not None:
            if message_type == "auth" and message_request == "getToken":
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
                            user_id = message.get("userID", None)
                            if sender is not None and description is not None and url is not None and user_id is not None:
                                url = f"https://{self.domain}{url[1:]}"
                                self.api_logger.debug(
                                    "Received message from %s: %s (%s)",
                                    sender, description, url
                                )
                                if self.received_message_callback is not None:
                                    self.received_message_callback(message_data)

    def run_websocket(self):
        """
        Run Websocket
        """
        self.websocket_logger.info("Connecting to WebSocket")
        ws = websocket.WebSocketApp(
            "wss://nodejs-gs.smartschool.be/smsc/websocket",
            on_open=self.ws_on_open,
            on_message=self.ws_on_message,
            on_error=self.ws_on_error,
            on_close=self.ws_on_close
        )
        ws.run_forever()
