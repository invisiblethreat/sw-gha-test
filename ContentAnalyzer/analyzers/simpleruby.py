"""SimpleRubyAnalyzer."""

from ContentAnalyzer.lexers import Document, KeyValuePair


class SimpleRubyAnalyzer(Document):
    """SimpleRubyAnalyzer"""

    # pylint: disable=unused-argument
    def analyze(self, content):
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        self.set_lexer("SimpleRubyLexer")

        self.parse(content)

        left_side = None
        right_side = None
        for token in self.all_tokens:
            if token.kind == "analyzer.Key":
                if token.value is None:
                    continue
                left_side = token
            elif token.kind == "analyzer.Value":
                right_side = token
                kv_pair = KeyValuePair.from_tokens(left_side, right_side)
                self.kvps.append(kv_pair)
                left_side = None
                right_side = None
            else:
                raise ValueError("Unknown token kind '%s'" % token.kind)

    # pylint: enable=unused-argument


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


# def main():
#     """Main."""

#     doc = SimpleRubyAnalyzer()
#     doc.analyze(content=TEXT)

#     for n in doc.get_kvps():
#         print(n.key, n.value)

#     print("breakpoint")

# if __name__ == "__main__":
#     main()
