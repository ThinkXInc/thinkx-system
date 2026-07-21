#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# mails/render_html.py
#

from flask import render_template
from models.user import User
from models.organization_member import OrganizationMember
from general.config import Config


# generate path
# for html rendering files present in 
# www/server/application/views/templates/mails
def html_path(key: str, lang='en'):
    return f'mails/{lang}/{key}.html'


def plain_path(key: str, lang='en'):
    return f'mails/plain/{lang}/{key}.txt'


# format plain text
def plain_text(key: str, lang='en', **kwargs):
    f = open(key, 'r')
    template = f.read()
    f.close()
    return template.format(kwargs)


# render html/plain method
def render_signup(
        user: User, validation_url: str, 
        lang='en', html=True, hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('signup', lang),
            user=user,
            validation_url=validation_url,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('signup', lang),
            user=user,
            validation_url=validation_url,
            hosturl=hosturl)
        

def render_signup_organization(
        organization_member: OrganizationMember,
        validation_url: str, lang='en',
        html=True, hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('signup_organization', lang),
            organization_member=organization_member,
            validation_url=validation_url,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('signup_organization', lang),
            organization_member=organization_member,
            validation_url=validation_url,
            hosturl=hosturl)
 

def render_email_change_verification(
        user: User, mail_confirmation_code: str,
        lang='en', html=True, hosturl=Config.HOST_URL):
    if html:
        return render_template(html_path(
            'email_change_verification', lang),
            user=user,
            mail_confirmation_code=mail_confirmation_code,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('email_change_verification', lang),
            user=user,
            mail_confirmation_code=mail_confirmation_code,
            hosturl=hosturl)


def render_email_change_verification_organization_member(
        organization_member: OrganizationMember, mail_confirmation_code: str,
        lang='en', html=True, hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('email_change_verification_organization_member', lang),
            organization_member=organization_member,
            mail_confirmation_code=mail_confirmation_code,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('email_change_verification_organization_member', lang),
            organization_member=organization_member,
            mail_confirmation_code=mail_confirmation_code,
            hosturl=hosturl)


def render_email_change_success(
        user: User, lang='en', html=True, hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('email_change_success', lang),
            user=user,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('email_change_success', lang),
            user=user,
            hosturl=hosturl)


def render_email_change_success_organization_member(
        organization_member: OrganizationMember, lang='en',
        html=True, hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('email_change_success_organization', lang),
            organization_member=organization_member,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('email_change_success_organization_member', lang),
            organization_member=organization_member,
            hosturl=hosturl)


def render_password_reset(
        user: User, password_reset_code: str, lang='en', html=True,
        hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('password_reset', lang),
            user=user,
            password_reset_code=password_reset_code,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('password_reset', lang),
            user=user,
            password_reset_code=password_reset_code,
            hosturl=hosturl)


def render_password_reset_organization_member(
        organization_member: OrganizationMember,
        password_reset_code: str, lang='en', html=True,
        hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('password_reset_organization_member', lang),
            organization_member=organization_member,
            password_reset_code=password_reset_code,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('password_reset_organization_member', lang),
            organization_member=organization_member,
            password_reset_code=password_reset_code,
            hosturl=hosturl)


def render_password_change_success(
        user: User, lang='en', html=True,
        hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('password_change_success', lang),
            user=user,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('password_change_success', lang),
            user=user,
            hosturl=hosturl)


def render_password_change_success_organization_member(
        organization_member: OrganizationMember, lang='en', html=True,
        hosturl=Config.HOST_URL):
    if html:
        return render_template(
            html_path('password_change_success_organization_member', lang),
            organization_member=organization_member,
            hosturl=hosturl)
    else:
        return plain_text(
            plain_path('password_change_success_organization_member', lang),
            organization_member=organization_member,
            hosturl=hosturl)