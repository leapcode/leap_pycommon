# -*- coding: utf-8 -*-
# catalog.py
# Copyright (C) 2015 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful",
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""
Events catalog.
"""


EVENTS = [
    "CLIENT_SESSION_ID",
    "CLIENT_UID",
    "RAISE_WINDOW",
    "UPDATER_DONE_UPDATING",
    "UPDATER_NEW_UPDATES",

    "KEYMANAGER_DONE_UPLOADING_KEYS",  # (address)
    "KEYMANAGER_FINISHED_KEY_GENERATION",  # (address)
    "KEYMANAGER_KEY_FOUND",  # (address)
    "KEYMANAGER_KEY_NOT_FOUND",  # (address)
    "KEYMANAGER_LOOKING_FOR_KEY",  # (address)
    "KEYMANAGER_STARTED_KEY_GENERATION",  # (address)

    "SOLEDAD_CREATING_KEYS",  # {uuid, userid}
    "SOLEDAD_DONE_CREATING_KEYS",  # {uuid, userid}
    "SOLEDAD_DONE_DATA_SYNC",  # {uuid, userid}
    "SOLEDAD_DONE_DOWNLOADING_KEYS",  # {uuid, userid}
    "SOLEDAD_DONE_UPLOADING_KEYS",  # {uuid, userid}
    "SOLEDAD_DOWNLOADING_KEYS",  # {uuid, userid}
    "SOLEDAD_INVALID_AUTH_TOKEN",  # {uuid, userid}
    "SOLEDAD_SYNC_RECEIVE_STATUS",  # {uuid, userid}
    "SOLEDAD_SYNC_SEND_STATUS",  # {uuid, userid}
    "SOLEDAD_UPLOADING_KEYS",  # {uuid, userid}
    "SOLEDAD_NEW_DATA_TO_SYNC",

    "MAIL_FETCHED_INCOMING",  # (userid)
    "MAIL_MSG_DECRYPTED",  # (userid)
    "MAIL_MSG_DELETED_INCOMING",  # (userid)
    "MAIL_MSG_PROCESSING",  # (userid)
    "MAIL_MSG_SAVED_LOCALLY",  # (userid)
    "MAIL_UNREAD_MESSAGES",  # (userid, number)

    "IMAP_SERVICE_STARTED",
    "IMAP_SERVICE_FAILED_TO_START",
    "IMAP_UNHANDLED_ERROR",
    "IMAP_CLIENT_LOGIN",  # (username)

    "SMTP_SERVICE_STARTED",
    "SMTP_SERVICE_FAILED_TO_START",
    "SMTP_START_ENCRYPT_AND_SIGN",  # (from_addr)
    "SMTP_END_ENCRYPT_AND_SIGN",  # (from_addr)
    "SMTP_START_SIGN",  # (from_addr)
    "SMTP_END_SIGN",  # (from_addr)
    "SMTP_SEND_MESSAGE_START",  # (from_addr)
    "SMTP_SEND_MESSAGE_SUCCESS",  # (from_addr)
    "SMTP_RECIPIENT_ACCEPTED_ENCRYPTED",  # (userid, dest)
    "SMTP_RECIPIENT_ACCEPTED_UNENCRYPTED",  # (userid, dest)
    "SMTP_CONNECTION_LOST",  # (userid, dest)
    "SMTP_RECIPIENT_REJECTED",  # (userid, dest)
    "SMTP_SEND_MESSAGE_ERROR",  # (userid, dest)
]


class Event(object):

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return '<Event: %s>' % self.label

    def __str__(self):
        return self.label


# create local variables based on the event list above
lcl = locals()
for event in EVENTS:
    lcl[event] = Event(event)
