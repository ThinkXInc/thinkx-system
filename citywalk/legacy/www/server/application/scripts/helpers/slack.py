#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# slack.py
#
# slack function
#
import os
import traceback
from enum import Enum

import slackweb

from general.config import Config
from helpers.date_utils import DateUtils
from helpers.mdc import MDC


class Slack:
    class Color(Enum):
        RED = "#e00202"
        BLUE = "#314ce2"
        GREEN = "#1eed30"
        PURPLE = "#C299FF"
        ORANGE = "#FF9872"
        BROWN = "#CD853F"

    @classmethod
    def notify_rich_text(cls, hook_url: str, pretext: str, title: str, text: str, footer: str, color=Color.RED):
        """Send notification to channel.

        args:
            - hook_url: str # ex) "https://hooks.slack.com/services/xxxx/xxx/xxxx"
            - pretext: str
            - title: str
            - text: str
            - footer: str
            - color: Slack.Color
        """
        if not hook_url:
            return
        slack = slackweb.Slack(url=hook_url)
        attachment = {
            "pretext": pretext,
            "title": title,
            "text": text,
            "footer": footer,
            "color": color.value,
        }
        attachments = []
        attachments.append(attachment)
        slack.notify(attachments=attachments)

    @classmethod
    def notify_simple_text(cls, hook_url: str, text: str):
        """Send notification with simple format.

        args:
            - hook_url: str # ex) "https://hooks.slack.com/services/xxxx/xxx/xxxx"
            - text: str
        """
        if not hook_url:
            return
        slack = slackweb.Slack(url=hook_url)
        slack.notify(text=text)

    @classmethod
    def notify_error_alert(cls, text):
        """Send error message to channel.

        args:
            text: str
        """
        try:
            for hook_url in Config.ALERT_SLACK_HOOK_URLS:
                Slack.notify_rich_text(hook_url=hook_url, pretext="Unexpected error occurred",
                                       title=os.environ.get("ENV").upper(),
                                       text=str(text),
                                       footer=MDC.get_message_id(),
                                       color=Slack.Color.RED)
        except:
            print(traceback.format_exc())

    @classmethod
    def notify_batch_progress(cls, text: str, color, process_name="Unknown", is_start=False):
        """Send batch report to channel.

        args:
            - text: str
            - color: Slack.Color
            - process_name: str
            - is_start: bool default False # If True output startup process.
        """
        pretext = ""
        if is_start:
            pretext = "{}\n{}({})".format(DateUtils.get_date_str(format='%m/%d %H:%M'),
                                          process_name.lower(), os.environ.get("ENV"))
        for hook_url in Config.BATCH_SLACK_HOOK_URLS:
            Slack.notify_rich_text(hook_url=hook_url,
                                   pretext=pretext,
                                   title="",
                                   text=str(text),
                                   footer=MDC.get_message_id(),
                                   color=color)
