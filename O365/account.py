from .connection import Connection, Protocol, MSGraphProtocol
from .connection import oauth_authentication_flow


class Account(object):

    def __init__(self, credentials, *, protocol=None, main_resource=None, **kwargs):
        """ Creates an object which is used to access resources related to the
        specified credentials

        :param tuple credentials: a tuple containing the client_id
         and client_secret
        :param Protocol protocol: the protocol to be used in this account
        :param str main_resource: the resource to be used by this account
         ('me' or 'users', etc.)
        :param kwargs: any extra args to be passed to the Connection instance
        :raises ValueError: if an invalid protocol is passed
        """

        protocol = protocol or MSGraphProtocol  # Defaults to Graph protocol
        self.protocol = protocol(default_resource=main_resource,
                                 **kwargs) if isinstance(protocol,
                                                         type) else protocol

        if not isinstance(self.protocol, Protocol):
            raise ValueError("'protocol' must be a subclass of Protocol")

        # for client credential grant flow solely:
        if kwargs.get('auth_flow_type', 'web') == 'backend':
            # append the default scope if it's not provided
            scopes = kwargs.get('scopes', [])
            if not scopes:
                scopes.append(self.protocol.prefix_scope('.default'))
                kwargs['scopes'] = scopes
            # set main_resource to blank
            self.protocol.default_resource = ''
            main_resource = ''

        self.con = Connection(credentials, **kwargs)
        self.main_resource = main_resource or self.protocol.default_resource

    def __repr__(self):
        if self.con.auth:
            return 'Account Client Id: {}'.format(self.con.auth[0])
        else:
            return 'Unidentified Account'

    @property
    def is_authenticated(self):
        """
        Checks whether the library has the authentication and that is not expired
        :return: True if authenticated, False otherwise
        """
        token = self.con.token_backend.token
        if not token:
            token = self.con.token_backend.get_token()

        return token is not None and not token.is_expired

    def authenticate(self, *, scopes=None, **kwargs):
        """ Performs the oauth authentication flow using the console resulting in a stored token.
        It uses the credentials passed on instantiation

        :param list[str] or None scopes: list of protocol user scopes to be converted
         by the protocol or scope helpers
        :param kwargs: other configurations to be passed to the
         Connection instance
        :return: Success / Failure
        :rtype: bool
        """

        if self.con.auth_flow_type == 'web':
            scopes = scopes or self.con.scopes
            # TODO: set connection defaults.
            kwargs.setdefault('token_backend', self.con.token_backend)
            return oauth_authentication_flow(*self.con.auth, scopes=scopes,
                                             protocol=self.protocol, **kwargs)
        elif self.con.auth_flow_type == 'backend':
            return self.con.request_token(None, requested_scopes=scopes)
        else:
            raise ValueError('Connection "auth_flow_type" must be either web or backend')

    @property
    def connection(self):
        """ Alias for self.con

        :rtype: Connection
        """
        return self.con

    def new_message(self, resource=None):
        """ Creates a new message to be sent or stored

        :param str resource: Custom resource to be used in this message
         (Defaults to parent main_resource)
        :return: New empty message
        :rtype: Message
        """
        from .message import Message
        return Message(parent=self, main_resource=resource, is_draft=True)

    def mailbox(self, resource=None):
        """ Get an instance to the mailbox for the specified account resource

        :param str resource: Custom resource to be used in this mailbox
         (Defaults to parent main_resource)
        :return: a representation of account mailbox
        :rtype: MailBox
        """
        from .mailbox import MailBox
        return MailBox(parent=self, main_resource=resource, name='MailBox')

    def address_book(self, *, resource=None, address_book='personal'):
        """ Get an instance to the specified address book for the
        specified account resource

        :param str resource: Custom resource to be used in this address book
         (Defaults to parent main_resource)
        :param str address_book: Choose from 'Personal' or
         'GAL' (Global Address List)
        :return: a representation of the specified address book
        :rtype: AddressBook or GlobalAddressList
        :raises RuntimeError: if invalid address_book is specified
        """
        if address_book.lower() == 'personal':
            from .address_book import AddressBook

            return AddressBook(parent=self, main_resource=resource,
                               name='Personal Address Book')
        elif address_book.lower() == 'gal':
            from .address_book import GlobalAddressList

            return GlobalAddressList(parent=self)
        else:
            raise RuntimeError(
                'address_book must be either "personal" '
                '(resource address book) or "gal" (Global Address List)')

    def schedule(self, *, resource=None):
        """ Get an instance to work with calendar events for the
        specified account resource

        :param str resource: Custom resource to be used in this schedule object
         (Defaults to parent main_resource)
        :return: a representation of calendar events
        :rtype: Schedule
        """
        from .calendar import Schedule
        return Schedule(parent=self, main_resource=resource)

    def storage(self, *, resource=None):
        """ Get an instance to handle file storage (OneDrive / Sharepoint)
        for the specified account resource

        :param str resource: Custom resource to be used in this drive object
         (Defaults to parent main_resource)
        :return: a representation of OneDrive File Storage
        :rtype: Storage
        :raises RuntimeError: if protocol doesn't support the feature
        """
        if not isinstance(self.protocol, MSGraphProtocol):
            # TODO: Custom protocol accessing OneDrive/Sharepoint Api fails here
            raise RuntimeError(
                'Drive options only works on Microsoft Graph API')
        from .drive import Storage
        return Storage(parent=self, main_resource=resource)

    def sharepoint(self, *, resource=''):
        """ Get an instance to read information from Sharepoint sites for the
        specified account resource

        :param str resource: Custom resource to be used in this sharepoint
         object (Defaults to parent main_resource)
        :return: a representation of Sharepoint Sites
        :rtype: Sharepoint
        :raises RuntimeError: if protocol doesn't support the feature
        """

        if not isinstance(self.protocol, MSGraphProtocol):
            # TODO: Custom protocol accessing OneDrive/Sharepoint Api fails here
            raise RuntimeError(
                'Sharepoint api only works on Microsoft Graph API')

        from .sharepoint import Sharepoint
        return Sharepoint(parent=self, main_resource=resource)

    def planner(self, *, resource=''):
        """ Get an instance to read information from Microsoft planner """

        if not isinstance(self.protocol, MSGraphProtocol):
            # TODO: Custom protocol accessing OneDrive/Sharepoint Api fails here
            raise RuntimeError(
                'planner api only works on Microsoft Graph API')

        from .planner import Planner
        return Planner(parent=self, main_resource=resource)
