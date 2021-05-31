// Config overrides for NODE_ENV=saucelabs
import toTime from 'to-time';
import capabilities, {formatName} from '../support/capabilities';
import {tag as productBuildTag} from '../support/product-build';
import cliOpts from '../support/protractor/cli-opts';
import {waitTime} from '../support/protractor/time';

const config = {
    baseUrl: 'https://qa.product.io',

    sauceUser: 'productdev',
    sauceKey: '0017e418-d36e-4b3b-bac7-b9527dfb42ff',
    sauceBuild: productBuildTag ? productBuildTag : null,

    // 30 secs
    getPageTimeout: toTime(waitTime.pageLoad).ms()
};

const {browser: browserName, platform, 'platform-version': version} = cliOpts;

if (browserName || platform || version) {
    config.capabilities = {
        name: formatName(browserName, version, platform)
    };
} else {
    config.multiCapabilities = capabilities({
        browserName: 'chrome',
        version: 'latest',
        platform: ['OS X 10.11', 'Windows 7']
    }, {
        browserName: 'firefox',
        version: '52',
        platform: ['OS X 10.11', 'Windows 7'],
        // See: https://www.hskupin.info/2017/01/23/using-selenium-and-webdriver-to-interact-with-insecure-ssl-pages-in-firefox/
        acceptInsecureCerts: true
    });
}

export {config};