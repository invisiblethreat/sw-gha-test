"""SimpleRuby Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase


@attr.s(kw_only=True, slots=True)
class SimpleRubyKeyValue(LexerMatchBase):
    """SimpleRubyKeyValue."""

    key = attr.ib(default=None, type=str)
    value = attr.ib(default=None, type=str)

    _field_match_mappings = attr.ib(default={
        1: 'key',
        5: 'value',
        6: 'value',
    })

    _token_index_mappings = attr.ib(default={
        'key': 1,
        'value': 2,
    })

    _token_kind_mapping = attr.ib(default={
        'key': ['analyzer', 'Key'],
        'value': ['analyzer', 'Value'],
    })

    _token_kinds = attr.ib(default=[
        'analyzer.Key',
        'analyzer.Value',
    ])

    def consume_match(self, match):
        """Consume a regex match and populate self with it."""

        key_group = self._token_index_mappings['key']
        # TODO: Shouldn't need to implement this but have to for some reason
        if match.group(key_group) is None:
            # Key value is None so return
            return

        if match.group(key_group) is not None:
            # key = match.group(4)
            field_name = "key"
            start_pos = match.start(key_group)
            kind = self._get_field_to_kind(field_name)
            value = match.group(key_group)

            match_tuple = self._make_token_tuple(start_pos, kind, value)

            setattr(self, field_name, match_tuple)
        else:
            raise RuntimeError("Couldn't find key!")

        field_name = "value"
        value_group = None
        if match.group(5) is not None:
            value_group = 5
        elif match.group(6) is not None:
            value_group = 6

        start_pos = match.start(value_group)
        kind = self._get_field_to_kind(field_name)
        value = match.group(value_group)

        match_tuple = self._make_token_tuple(start_pos, kind, value)

        setattr(self, field_name, match_tuple)

    # pylint: disable=no-member
    @property
    def tokens(self):
        """Spits out tokens from attributes."""

        props = [n for n in self.__slots__ if not n.startswith('_') and n != "__weakref__"]

        for n in props:
            token = getattr(self, n)
            yield token
    # pylint: enable=no-member

    @classmethod
    def from_dict(cls, data):
        """Instantiate class from a dict."""

        instance = cls()
        for k, v in data.items():
            try:
                setattr(instance, k, v)
            except AttributeError:
                # We don't have this attribute so ignore
                pass

        return instance

    @classmethod
    def from_regex_match(cls, match):
        """Instantiate class from a regex match."""

        instance = cls()
        instance.consume_match(match)

        return instance


@attr.s(kw_only=True, slots=True)
class SimpleRubyLexer():
    """SimpleRubyLexer."""

    # pylint: disable=line-too-long
    # 2 is key. 7 is value if in '' or 5 if in "".
    regex = attr.ib(default=r"(?:(?:[@$]{0,2}([\w]+)(?:(?:\['(.+)'\])|(?:\[\"(.+)\"]))?)|(?:'([\w@]+)'))(?:(?: ?= ?)|(?: => ))(?:(?:(?:'(.[^,\n]*)'|\"(.[^,\n]*)\")))", type=str)
    compiled_regex = attr.ib(default=None)
    # pylint: enable=line-too-long

    def __attrs_post_init__(self):

        self.compiled_regex = re.compile(self.regex, re.MULTILINE)


    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.compiled_regex, text)

        entries = [SimpleRubyKeyValue.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop


TEXT = """DemoApp::Application.configure do
    # Settings specified here will take precedence over those in config/application.rb

    ENV['full_host'] = "https://partnerprogram.heroku.com"
    ENV['sfdc_login'] = "https://login.salesforce.com"

    #You setup these in Setup > Development > Remote Access
    #Set your callback url to https://yourtemplateapp.heroku.com/auth/forcedotcom/callback
    ENV['sfdc_consumer_key'] = "3MVG9Oe7T3Ol0ea5IyD_vRQiffzilFchfSDuwzR9S.O7.XUr49a5s9C_tlTUqfBi4St9aVP8F2SC9xESbczRn"
    ENV['sfdc_consumer_secret'] = "8303684421513603327"

    ENV['sfdc_api_version'] = '21.0'

    ENV['DATABASEDOTCOM_CLIENT_ID'] = ENV['sfdc_consumer_key']
    ENV['DATABASEDOTCOM_CLIENT_SECRET'] = ENV['sfdc_consumer_secret']
    # The production environment is meant for finished, "live" apps.
    # Code is not reloaded between requests
    config.cache_classes = true

    # Full error reports are disabled and caching is turned on
    config.consider_all_requests_local       = false
    config.action_controller.perform_caching = true

    # Specifies the header that your server uses for sending files
    config.action_dispatch.x_sendfile_header = "X-Sendfile"

    # For nginx:
    # config.action_dispatch.x_sendfile_header = 'X-Accel-Redirect'

    # If you have no front-end server that supports something like X-Sendfile,
    # just comment this out and Rails will serve the files

    # See everything in the log (default is :info)
    # config.log_level = :debug

    # Use a different logger for distributed setups
    # config.logger = SyslogLogger.new

    # Use a different cache store in production
    # config.cache_store = :mem_cache_store

    # Disable Rails's static asset server
    # In production, Apache or nginx will already do this
    config.serve_static_assets = false

    # Enable serving of images, stylesheets, and javascripts from an asset server
    # config.action_controller.asset_host = "http://assets.example.com"

    # Disable delivery errors, bad email addresses will be ignored
    # config.action_mailer.raise_delivery_errors = false

    # Enable threaded mode
    # config.threadsafe!

    # Enable locale fallbacks for I18n (makes lookups for any locale fall back to
    # the I18n.default_locale when a translation can not be found)
    config.i18n.fallbacks = true

    # Send deprecation notices to registered listeners
    config.active_support.deprecation = :notify
  end"""


# # pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = SimpleRubyLexer()
#     entries = list(lexer.get_tokens_unprocessed(TEXT))


#     print("breakpoint")

# if __name__ == "__main__":
#     main()
