from wepay.calls.base import Call
from wepay.utils import cached_property

class User(Call):
    """ The /user API calls """

    call_name = 'user'

    @cached_property
    def mfa(self):
        """:class:`Membership<wepay.calls.user.MFA>` call instance"""
        return MFA(self._api)

    def __call__(self, **kwargs):
        """Call documentation: `/user
        <https://www.wepay.com/developer/reference/user#lookup>`_, plus extra
        keyword parameters:
        
        :keyword str access_token: will be used instead of instance's
           ``access_token``, with ``batch_mode=True`` will set `authorization`
           param to it's value.

        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        return self.make_call(self, {}, kwargs)
    allowed_params = []

    def __modify(self, **kwargs):
        """Call documentation: `/user/modify
        <https://www.wepay.com/developer/reference/user#modify>`_, plus extra
        keyword parameters:
        
        :keyword str access_token: will be used instead of instance's
           ``access_token``, with ``batch_mode=True`` will set `authorization`
           param to it's value.

        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        return self.make_call(self.__modify, {}, kwargs)
    __modify.allowed_params = ['callback_uri']
    modify = __modify

    def __register(self, client_id, client_secret, email, scope, first_name,
                   last_name, original_ip, original_device, **kwargs):
        """Call documentation: `/user/register
        <https://www.wepay.com/developer/reference/user#register>`_, plus
        extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        .. note ::

            This call is NOT supported by API versions older then '2014-01-08'.

        """
        params = {
            'client_id': client_id, 
            'client_secret': client_secret, 
            'email': email, 
            'scope': scope, 
            'first_name': first_name,
            'last_name': last_name, 
            'original_ip': original_ip, 
            'original_device': original_device
        }
        return self.make_call(self.__register, params, kwargs)
    __register.allowed_params = [
        'client_id', 'client_secret', 'email', 'scope', 'first_name', 'last_name', 
        'original_ip', 'original_device', 'redirect_uri', 'callback_uri', 
        'tos_acceptance_time'
    ]
    __register.control_keywords = ['batch_mode']
    register = __register

    def __send_confirmation(self, **kwargs):
        """Call documentation: `/user/resend_confirmation
        <https://www.wepay.com/developer/reference/user#resend_confirmation>`_, plus
        extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        .. note ::

            This call is NOT supported by API versions older then '2014-01-08'.

        """
        return self.make_call(self.__send_confirmation, {}, kwargs)
    __send_confirmation.allowed_params = ['email_message']
    __send_confirmation.control_keywords = ['batch_mode']
    send_confirmation = __send_confirmation


class MFA(Call):
    """ The /user/mfa API calls"""

    call_name = 'user/mfa'

    def __create(self, type, **kwargs):
        """Call documentation: `/user/mfa/create
        <https://www.wepay.com/developer/reference/user-mfa#create>`_, plus
        extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {
            'type': type
        }
        return self.make_call(self.__create, params, kwargs)
    __create.allowed_params = [
        'type', 'nickname', 'setup_data', 'cookie'
    ]
    create = __create

    def __validate_cookie(self, mfa_id, cookie, **kwargs):
        """Call documentation: `/user/mfa/validate_cookie
        <https://www.wepay.com/developer/reference/user-mfa#validate_cookie>`_,
        plus extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {
            'mfa_id': mfa_id,
            'cookie': cookie
        }
        return self.make_call(self.__validate_cookie, params, kwargs)
    __validate_cookie.allowed_params = [
        'mfa_id', 'cookie'
    ]
    validate_cookie = __validate_cookie
    
    def __send_challenge(self, mfa_id, **kwargs):
        """Call documentation: `/user/mfa/send_challenge
        <https://www.wepay.com/developer/reference/user-mfa#send_challenge>`_,
        plus extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {
            'mfa_id': mfa_id
        }
        return self.make_call(self.__send_challenge, params, kwargs)
    __send_challenge.allowed_params = [
        'mfa_id', 'force_voice'
    ]
    send_challenge = __send_challenge
    
    def __send_default_challenge(self, **kwargs):
        """Call documentation: `/user/mfa/send_default_challenge
        <https://www.wepay.com/developer/reference/user-mfa#send_default_challenge>`_,
        plus extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {}
        return self.make_call(self.__send_default_challenge, params, kwargs)
    __send_default_challenge.allowed_params = []
    send_default_challenge = __send_default_challenge
    
    def __confirm(self, mfa_id, challenge, **kwargs):
        """Call documentation: `/user/mfa/confirm
        <https://www.wepay.com/developer/reference/user-mfa#confirm>`_,
        plus extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {
            'mfa_id': mfa_id,
            'challenge': challenge
        }
        return self.make_call(self.__confirm, params, kwargs)
    __confirm.allowed_params = [
        'mfa_id', 'challenge'
    ]
    confirm = __confirm

    def __find(self, **kwargs):
        """Call documentation: `/user/mfa/find
        <https://www.wepay.com/developer/reference/user-mfa#find>`_,
        plus extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {}
        return self.make_call(self.__find, params, kwargs)
    __find.allowed_params = [
        'challenge'
    ]
    find = __find
    
    def __modify(self, mfa_id, **kwargs):
        """Call documentation: `/user/mfa/modify
        <https://www.wepay.com/developer/reference/user-mfa#modify>`_,
        plus extra keyword parameter:
        
        :keyword bool batch_mode: turn on/off the batch_mode, see 
           :class:`wepay.api.WePay`

        :keyword str batch_reference_id: `reference_id` param for batch call,
           see :class:`wepay.api.WePay`

        :keyword str api_version: WePay API version, see
           :class:`wepay.api.WePay`

        """
        params = {
            'mfa_id': mfa_id
        }
        return self.make_call(self.__modify, params, kwargs)
    __modify.allowed_params = [
        'mfa_id'
    ]
    modify = __modify
