from flask_mail import Message
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS import mail
from eNMS.automation.models import Service
from eNMS.base.helpers import get_one
from eNMS.base.models import service_classes


class MailNotificationService(Service):

    __tablename__ = 'MailNotificationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    title = Column(String)
    sender = Column(String)
    recipients = Column(String)
    body = Column(String)
    body_textarea = True
    multiprocessing = False

    __mapper_args__ = {
        'polymorphic_identity': 'mail_notification_service',
    }

    def job(self, _):
        parameters = get_one('Parameters')
        if self.recipients:
            recipients = self.recipients.split(',')
        else:
            recipients = parameters.mail_sender.split(',')
        message = Message(
            self.title,
            sender=self.sender or parameters.mail_sender,
            recipients=recipients,
            body=self.body
        )
        mail.send(message)
        return {'success': True, 'result': str(message)}


service_classes['mail_notification_service'] = MailNotificationService
