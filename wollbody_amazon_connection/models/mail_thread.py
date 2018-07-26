# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import dateutil
import email
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
import xmlrpclib

from collections import namedtuple
from email.message import Message
from email.utils import formataddr
from lxml import etree
from werkzeug import url_encode

from odoo import _, api, exceptions, fields, models, tools
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    @api.multi
    def _message_auto_subscribe_notify(self, partner_ids):
        """ Notify newly subscribed followers of the last posted message.
            :param partner_ids : the list of partner to add as needaction partner of the last message
                                 (This excludes the current partner)
        """
        if not partner_ids:
            return

        if self.env.context.get('mail_auto_subscribe_no_notify'):
            return

        # send the email only to the current record and not all the ids matching active_domain !
        # by default, send_mail for mass_mail use the active_domain instead of active_ids.
        if 'active_domain' in self.env.context:
            ctx = dict(self.env.context)
            ctx.pop('active_domain')
            self = self.with_context(ctx)

        for record in self:
            pass
        
#             record.message_post_with_view(
#                 'mail.message_user_assigned',
#                 composition_mode='mass_mail',
#                 partner_ids=[(4, pid) for pid in partner_ids],
#                 auto_delete=True,
#                 auto_delete_message=True,
#                 parent_id=False, # override accidental context defaults
#                 subtype_id=self.env.ref('mail.mt_note').id)
    
    @api.model
    def message_route_process(self, message, message_dict, routes):
        self = self.with_context(attachments_mime_plainxml=True) # import XML attachments as text
        # postpone setting message_dict.partner_ids after message_post, to avoid double notifications
        partner_ids = message_dict.pop('partner_ids', [])
        thread_id = False
        for model, thread_id, custom_values, user_id, alias in routes or ():
            if model:
                Model = self.env[model]
                if not (thread_id and hasattr(Model, 'message_update') or hasattr(Model, 'message_new')):
                    raise ValueError(
                        "Undeliverable mail with Message-Id %s, model %s does not accept incoming emails" %
                        (message_dict['message_id'], model)
                    )

                # disabled subscriptions during message_new/update to avoid having the system user running the
                # email gateway become a follower of all inbound messages
                MessageModel = Model.sudo(user_id).with_context(mail_create_nosubscribe=True, mail_create_nolog=True)
                if thread_id and hasattr(MessageModel, 'message_update'):
                    MessageModel.browse(thread_id).message_update(message_dict)
                    
                    ###############################
                    
                    _logger.info('message model>>>>>>>>>>>>>        ' + str(MessageModel))
                    _logger.info('normal  model>>>>>>>>>>>>>        ' + str(model))
                    if model == 'account.invoice' or model == 'sale.order' or model == 'res.partner':
                        message_dict.pop('parent_id', None)
                        NewMessageModel = self.env['project.issue']
                        thread_id = NewMessageModel.message_new(message_dict, custom_values)
                        mail_vals ={
                                    'subject'       : message_dict.get('subject'),
                                    'email_from'    : message_dict.get('email_from'),
                                    'model'         : 'project.issue',
                                    'message_type'  : 'email',
                                    'subtype_id'    : 1,
                                    'body'          : message_dict.get('body'),
                                    'res_id'        : thread_id,
                                    }
                        self.env['mail.message'].create(mail_vals)
                        
                else:
                    # if a new thread is created, parent is irrelevant
                    _logger.info('create new message  message model>>>>>>>>>>>>>        ' + str(MessageModel))
                    message_dict.pop('parent_id', None)
                    thread_id = MessageModel.message_new(message_dict, custom_values)
            else:
                if thread_id:
                    raise ValueError("Posting a message without model should be with a null res_id, to create a private message.")
                Model = self.env['mail.thread']
            if not hasattr(Model, 'message_post'):
                Model = self.env['mail.thread'].with_context(thread_model=model)
            internal = message_dict.pop('internal', False)
            new_msg = Model.browse(thread_id).message_post(subtype=internal and 'mail.mt_note' or 'mail.mt_comment', **message_dict)

            if partner_ids:
                # postponed after message_post, because this is an external message and we don't want to create
                # duplicate emails due to notifications
                new_msg.write({'partner_ids': partner_ids})
        return thread_id
    
    
    
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Called by ``message_process`` when a new message is received
           for a given thread model, if the message did not belong to
           an existing thread.
           The default behavior is to create a new record of the corresponding
           model (based on some very basic info extracted from the message).
           Additional behavior may be implemented by overriding this method.

           :param dict msg_dict: a map containing the email details and
                                 attachments. See ``message_process`` and
                                ``mail.message.parse`` for details.
           :param dict custom_values: optional dictionary of additional
                                      field values to pass to create()
                                      when creating the new thread record.
                                      Be careful, these values may override
                                      any other values coming from the message.
           :param dict context: if a ``thread_model`` value is present
                                in the context, its value will be used
                                to determine the model of the record
                                to create (instead of the current model).
           :rtype: int
           :return: the id of the newly created thread object
        """
        
        data = {}
        if isinstance(custom_values, dict):
            data = custom_values.copy()
        model = self._context.get('thread_model') or self._name
        RecordModel = self.env[model]
        fields = RecordModel.fields_get()
        name_field = RecordModel._rec_name or 'name'
        
        _logger.info('message new normal model         ',str(model))
        _logger.info('message new record model creation model         ',str(RecordModel))
        
        if name_field in fields and not data.get('name'):
            data[name_field] = msg_dict.get('subject', '')
        res = RecordModel.create(data)
        return res.id
    
    