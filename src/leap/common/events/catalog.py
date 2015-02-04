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
    "IMAP_CLIENT_LOGIN",
    "IMAP_SERVICE_FAILED_TO_START",
    "IMAP_SERVICE_STARTED",
    "IMAP_UNHANDLED_ERROR",
    "KEYMANAGER_DONE_UPLOADING_KEYS",
    "KEYMANAGER_FINISHED_KEY_GENERATION",
    "KEYMANAGER_KEY_FOUND",
    "KEYMANAGER_KEY_NOT_FOUND",
    "KEYMANAGER_LOOKING_FOR_KEY",
    "KEYMANAGER_STARTED_KEY_GENERATION",
    "MAIL_FETCHED_INCOMING",
    "MAIL_MSG_DECRYPTED",
    "MAIL_MSG_DELETED_INCOMING",
    "MAIL_MSG_PROCESSING",
    "MAIL_MSG_SAVED_LOCALLY",
    "MAIL_UNREAD_MESSAGES",
    "RAISE_WINDOW",
    "SMTP_CONNECTION_LOST",
    "SMTP_END_ENCRYPT_AND_SIGN",
    "SMTP_END_SIGN",
    "SMTP_RECIPIENT_ACCEPTED_ENCRYPTED",
    "SMTP_RECIPIENT_ACCEPTED_UNENCRYPTED",
    "SMTP_RECIPIENT_REJECTED",
    "SMTP_SEND_MESSAGE_ERROR",
    "SMTP_SEND_MESSAGE_START",
    "SMTP_SEND_MESSAGE_SUCCESS",
    "SMTP_SERVICE_FAILED_TO_START",
    "SMTP_SERVICE_STARTED",
    "SMTP_START_ENCRYPT_AND_SIGN",
    "SMTP_START_SIGN",
    "SOLEDAD_CREATING_KEYS",
    "SOLEDAD_DONE_CREATING_KEYS",
    "SOLEDAD_DONE_DATA_SYNC",
    "SOLEDAD_DONE_DOWNLOADING_KEYS",
    "SOLEDAD_DONE_UPLOADING_KEYS",
    "SOLEDAD_DOWNLOADING_KEYS",
    "SOLEDAD_INVALID_AUTH_TOKEN",
    "SOLEDAD_NEW_DATA_TO_SYNC",
    "SOLEDAD_SYNC_RECEIVE_STATUS",
    "SOLEDAD_SYNC_SEND_STATUS",
    "SOLEDAD_UPLOADING_KEYS",
    "UPDATER_DONE_UPDATING",
    "UPDATER_NEW_UPDATES",
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
