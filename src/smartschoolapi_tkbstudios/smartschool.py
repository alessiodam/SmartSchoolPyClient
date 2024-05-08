"""
SmartSchool client API class
"""
import json
import logging
from xml.etree import ElementTree
from uuid import uuid4
import re
import datetime
import urllib
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
        platform_id: platform id
        received_message_callback: callback function

        api_logger: logger for API
        websocket_logger: logger for Websocket
        auth_logger: logger for Authentication

    Methods:
        check_if_authenticated()
        get_token_from_api()
        get_messages_from_api()
        get_message_by_id(message_id)
        get_school_courses()
        get_planner(from_date=None, to_date=None)
        list_messages()
        run_websocket()
    """

    def __init__(self, domain: str = None, loglevel: int = logging.DEBUG):
        self.domain = domain
        self.platform_id = None
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

    def check_if_authenticated(self):
        """
        Check if authenticated
        """
        if self.pid is None or self.phpsessid is None:
            raise AuthException("PID or PHPSESSID are not set")
        response = requests.get(
            f'https://{self.domain}/',
            headers={
                'Cookie': f'PHPSESSID={self.phpsessid}; pid={self.pid}'
            },
            allow_redirects=False
        )
        if response.status_code == 302:
            raise AuthException("Not authenticated, invalid cookies (PID or PHPSESSID)")
        elif response.status_code == 200:
            pass
        else:
            raise ApiException("Could not check if authenticated")
        return True

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

    def delete_message_by_id(self, message_id):
        """
        Delete message by ID
        """
        self.api_logger.info("Deleting message from API")
        self.api_logger.debug("Sending request to delete message with ID %s", message_id)

        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }

        data_dict = {
            'command': '<request>\n'
                       '\t<command>\n'
                       '\t\t<subsystem>postboxes</subsystem>\n'
                       '\t\t<action>quick delete</action>\n'
                       '\t\t<params>\n'
                       f'\t\t\t<param name="msgID"><![CDATA[{message_id}]]></param>\n'
                       '\t\t</params>\n'
                       '\t</command>\n'
                       '</request>'
        }

        data = urllib.parse.urlencode(data_dict)

        response = requests.post(
            f'https://{self.domain}/?module=Messages&file=dispatcher',
            headers=headers,
            data=data,
            timeout=10
        )

        if response.status_code == 200:
            self.api_logger.info("Message deleted with ID %s", message_id)
            return True

        self.api_logger.error("Could not delete message")
        raise ApiException("Could not delete message")

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

    def get_school_courses(self):
        """
        WARNING: IN DEVELOPMENT
        Get school courses
        """
        self.api_logger.info("Requesting school courses from API")
        self.api_logger.debug("Sending request to get school courses")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Accept': 'application/json',
        }
        response = requests.get(
            f'https://{self.domain}/course-list/api/v1/courses',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("School courses received")
            courses_json = json.loads(response.text)
            return courses_json
        self.api_logger.error("Could not get school courses")
        raise ApiException("Could not get school courses")

    def get_results(self, page: int = 1, per_page: int = 50):
        """
        Get results
        """
        self.api_logger.info("Requesting results from API")
        self.api_logger.debug("Sending request to get results")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        response = requests.get(
            f'https://{self.domain}/results/api/v1/evaluations/?pageNumber={page}&itemsOnPage={per_page}',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Results received")
            results_json = json.loads(response.text)
            return results_json
        self.api_logger.error("Could not get results")

    def get_planner(self, from_date=None, to_date=None):
        """
        Get planner

        Args:
            from_date: from date (YYYY-MM-DD)
            to_date: to date (YYYY-MM-DD)
        """
        if from_date is not None and not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', from_date):
            raise ValueError("from_date must be in format YYYY-MM-DD")
        if to_date is not None and not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', to_date):
            raise ValueError("to_date must be in format YYYY-MM-DD")

        if from_date is None:
            from_date = datetime.date.today().strftime("%Y-%m-%d")
        if to_date is None:
            to_date = (
                    datetime.datetime.strptime(from_date, "%Y-%m-%d")
                    +
                    datetime.timedelta(days=7)
            ).strftime("%Y-%m-%d")

        self.api_logger.info("Requesting planner from API")
        self.api_logger.debug("Sending request to get planner")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        if from_date is None and to_date is None:
            url = f'https://{self.domain}/planner/api/v1/planned-elements/user/{self.platform_id}_{self.user_id}_0'
        else:
            url = f"https://{self.domain}/planner/api/v1/planned-elements/user/{self.platform_id}{self.user_id}_0?from={from_date}&to={to_date}"
        response = requests.get(
            url=url,
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Planner received")
            planner_json = response.json()
            return planner_json
        self.api_logger.error("Could not get planner")
        return None

    def get_live_sessions(self):
        """
        Get live sessions
        """
        self.api_logger.info("Requesting live sessions from API")
        self.api_logger.debug("Sending request to get live sessions")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
        }
        response = requests.get(
            f'https://{self.domain}/online-session/api/v1/meeting/',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Live sessions received")
            live_sessions_json = response.json()
            return live_sessions_json
        self.api_logger.error("Could not get live sessions")
        return None

    def get_course_live_session(self, course_id):
        """
        Get course live sessions
        """
        self.api_logger.info("Requesting course live sessions from API")
        self.api_logger.debug("Sending request to get course live sessions")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
        }
        response = requests.get(
            f'https://{self.domain}/course/api/v1/video-call/{self.platform_id}/{course_id}',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Course live sessions received")
            live_sessions_json = response.json()
            return live_sessions_json
        self.api_logger.error("Could not get course live sessions")
        return None

    def get_upload_zone_dir(self, course_id: int = None, dir_id: str = None):
        """
        Get upload zone dir
        """
        if course_id is None:
            raise ValueError("course_id is required")
        if dir_id is None:
            dir_id = "0"

        self.api_logger.info("Requesting upload zone dir from API")
        self.api_logger.debug("Sending request to get upload zone dir")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(
            f'https://{self.domain}/?module=Uploadzone&file=tree&ssID={self.platform_id}&courseID={course_id}',
            headers=headers,
            data="id=" + dir_id,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Upload zone dir received")
            upload_zone_dir_json = response.json()
            return upload_zone_dir_json
        self.api_logger.error("Could not get upload zone dir")
        return None

    def get_helpdesk_tickets_filters(self):
        """
        Get helpdesk tickets filter
        """
        self.api_logger.info("Requesting tickets filter from API")
        self.api_logger.debug("Sending request to get tickets filter")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Accept': 'application/json'
        }
        response = requests.get(
            f'https://{self.domain}/helpdesk/api/v1/filters/',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Tickets filter received")
            tickets_filter_json = response.json()
            return tickets_filter_json
        self.api_logger.error("Could not get tickets filter")
        return None

    def get_helpdesk_tickets_by_filter_id(self, filter_id):
        """
        Get helpdesk tickets by filter id
        """
        self.api_logger.info("Requesting tickets from API")
        self.api_logger.debug("Sending request to get tickets")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Accept': 'application/json'
        }
        response = requests.get(
            f'https://{self.domain}/helpdesk/api/v1/tickets/filter/{filter_id}',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            self.api_logger.info("Tickets received")
            tickets_json = response.json()
            return tickets_json
        self.api_logger.error("Could not get tickets")
        return None

    def intradesk_get_directory(self, directory: str = ""):
        """
        Get intradesk files
        """
        self.api_logger.info("Requesting intradesk files from API")
        self.api_logger.debug("Sending request to get intradesk files")
        headers = {
            'Cookie': f'pid={self.pid}; PHPSESSID={self.phpsessid}',
            'Accept': 'application/json'
        }
        response = requests.get(
            f'https://{self.domain}/intradesk/api/v1/4005/directory-listing'
            f'/forTreeOnlyFolders{'/{directory}' if directory else ""}',
            headers=headers,
            timeout=10
        )
        self.api_logger.debug("Response: %s", response.text)
        if response.status_code == 200:
            self.api_logger.info("Intradesk folders received")
            intradesk_files_json = response.json()
            return intradesk_files_json
        self.api_logger.error("Could not get intradesk folders")
        return None

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

        if self.received_message_callback is not None:
            self.received_message_callback(message_data)
        else:
            self.websocket_logger.info("Received message: %s", message_text)

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
