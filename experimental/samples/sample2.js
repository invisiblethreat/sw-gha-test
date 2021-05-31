var registrationEpoch = registrationEpoch || (function () {
    var $tabs = $('#createNotTab li');

    const EMAIL_REGEX = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

    const USERNAME_REGEX = /^[\.a-z0-9_-]+$/i;

    const DEFERRED_NOOP = function() {
        return $.Deferred().resolve(true);
    }

    function init() {
        $tabs = $('#createNotTab li');

        $('#licenseCheckbox').change(function() {
            if (this.checked) {
                $('#licenseButton')
                    .removeClass('disabled')
                    .prop('disabled', false);
            } else {
                $('#licenseButton')
                    .addClass('disabled')
                    .prop('disabled', true);
            }
        });

        $('#setup_newUser').click(function(event) {
            if ($(this).hasClass('disabled')) {
                return false;
            }
        });

        $('#setup_newConfig').click(function(event) {
            if ($(this).hasClass('disabled')) {
                return false;
            }
        });

        $('input[type=radio][name=licenseType]').change(handleLicenseTypeChange);
        $('input[type=radio][name=setupType]').change(handleSetupTypeChange);

        initValidation();
    }

    function initValidation() {
        $('[required],[data-validate]').each(function() {
            const elem = $(this);
            const isRequired = elem.attr('required') === 'required';
            const validate = (elem.data('validate') || '').split(':');
            const type = validate[0] || 'text';
            const args = validate[1] ? validate[1].split(',').map(function(val) {
                return val.trim();
            }) : [];
            const validator = validators[type] || validators.text;

            // all required items are invalid until proven innocent...
            if (isRequired) {
                elem.addClass('has-error');
            }

            elem.on('keyup', validateWith(validator, args, isRequired));
            elem.on('blur', validateWith(validator, args, isRequired));

            if (type === 'confirm') {
                // sync confirm element with password element
                const synced_id = elem.attr('id').replace('-confirm', '');

                elem.on('keyup', function() {
                    $(`#${synced_id}`).blur();
                });
            }

            // find ancestor form element and notify changes
            const form = elem.parents('form');

            elem.on('keyup', function() {
                validateForm(form);
            });
        });

        // do something when forms are (in)valid
        $('#newLicenseForm').on('validate', function (event, isValid) {
            toggleButton('#requestLicenseButton', isValid);
        });

        $('#existingLicenseForm').on('validate', function (event, isValid) {
            toggleButton('#enterLicenseButton', isValid);
        });

        $('#setup_newUser').on('validate', function (event, isValid) {
            toggleButton('#newUserButton', isValid);
        });

        $('#deepStoreConfig').on('validate', function (event, isValid) {
            const isEnabled = isValid || getStorageType() === 'local';
            toggleButton('#customizePersistenceButton', isEnabled);
        });

        $('#persistenceConfig').on('validate', function (event, isValid) {
            const isEnabled = isValid || getPersistenceType() === 'local';
            toggleButton('#configurePersistenceButton', isEnabled);
        });
    }

    const lengthConditionRegex = /([<>]?=?)?\s*(\d+)/;

    function lengthSatisfies(value, condition) {
        if (!condition) {
            return true;
        }

        const matches = lengthConditionRegex.exec(condition);
        if (!matches) {
            return false;
        }

        const operator = matches[1] || '=';
        const expected = parseInt(matches[2], null);
        const actual = value.length;

        switch (operator) {
        case '>':
            return actual > expected;
        case '>=':
            return actual >= expected;
        case '<':
            return actual < expected;
        case '<=':
            return actual <= expected;
        case '=':
        default:
            return actual === expected;
        }
    }

    const validators = {
        // this is bound to jquery element in validator functions
        text: function(lengthCondition, invalidLengthMessage) {
            const value = $(this).val().trim();
            const isEmpty = (value === '');

            return {
                isValid: !isEmpty && lengthSatisfies(value, lengthCondition),
                message: isEmpty ? 'This field is required.' : invalidLengthMessage
            };
        },

        email: function() {
            const val = $(this).val().trim();

            return {
                isValid: val && EMAIL_REGEX.test(val),
                message: 'Invalid email address.'
            }
        },

        password: function() {
            const pass = $(this);
            const val = pass.val().trim();
            const id = pass.attr('id');
            const confirm = $(`#${id}-confirm`).val().trim();

            if (!val || !confirm) {
                return {
                    isValid: false,
                    message: 'This field is required.'
                }
            }

            return {
                isValid: val === confirm,
                message: 'Passwords do not match.'
            }
        },

        username: function() {
            const value = $(this).val();
            const isEmpty = (value.trim() === '');

            return {
                isValid: !isEmpty && USERNAME_REGEX.test(value),
                message: isEmpty ? 'This field is required.' : 'Invalid username.'
            };
        }
    }

    function validateWith(validator, args, isRequired) {
        return function(event) {
            // this is bound to jquery element
            const id = $(this).attr('id');
            const value = $(this).val().trim();

            var isValid, message;

            if (!isRequired && value === '') {
                isValid = true;
            } else {
                ({isValid, message} = validator.apply(this, args));
            }

            $(this).toggleClass('has-error', !isValid);
            $(this).parent().parent().toggleClass('has-error', !isValid);
            $(`#${id}Field`).text(isValid ? '' : message);
        };
    }

    function validateForm(form) {
        const invalidElems = $(form).find('.has-error');
        const isValid = invalidElems.length == 0;

        $(form).trigger('validate', [isValid, invalidElems]);
    }

    function showPrev() {
        $tabs.filter('.active').prev('li').removeClass('disabled');
        $tabs.filter('.active').prev('li').find('a[data-toggle]').each(function () {
            $(this).attr('data-toggle', 'tab');
        });

        $tabs.filter('.active').prev('li').find('a[data-toggle="tab"]').tab('show');

        $tabs.filter('.active').next('li').find('a[data-toggle="tab"]').each(function () {
            $(this).attr('data-toggle', '').parent('li').addClass('disabled');
        });
        resetProgress();
    }

    function updateProgressPercent(progressBar, percent) {
        $(progressBar).css('width', `${percent}%`);
    }

    function resetProgress() {
        $('#registrationProgress').hide();
        $('#newUserProgressBar').removeClass('progress-bar-success progress-bar-danger');
        updateProgressPercent($('#newUserProgressBar'), 60);
        $('#newUserMessage')
            .removeClass('text-success text-danger')
            .text('');

        $('#newConfigProgressBar').removeClass('progress-bar-success progress-bar-danger');
        updateProgressPercent($('#newConfigProgressBar'), 60);
        $('#newConfigMessage')
            .removeClass('text-success text-danger')
            .text('');
    }

    function showNext(e) {
        if (e) {
            e.preventDefault();
        }
        $tabs.filter('.active').next('li').removeClass('disabled');
        $tabs.filter('.active').next('li').find('a[data-toggle]').each(function () {
            $(this).attr('data-toggle', 'tab');
        });

        $tabs.filter('.active').next('li').find('a[data-toggle="tab"]').tab('show');

        $tabs.filter('.active').prev('li').find('a[data-toggle="tab"]').each(function () {
            $(this).attr('data-toggle', '').parent('li').addClass('disabled');
        });
    }

    function handleLicenseTypeChange() {
        // this is bound to the radio button group, see init()
        const type = this.value;

        $('#newLicenseForm').toggleClass('hidden', type !== 'new');
        $('#existingLicenseForm').toggleClass('hidden', type !== 'existing');
    }

    function handleSetupTypeChange() {
        // this is bound to the radio button group, see init()
        const type = this.value;

        if (type === 'default') {
            // reset values
            ['mysqlType', 'storageType'].forEach(function(id) {
                $(`#${id}`).val('local').trigger('change');
                $(`#${id}Label`).text('local');
            });
        }
    }

    function verifyInstance() {
        var instanceId = $('#awsInstanceId').val();
        var data = {
            instanceId: instanceId
        };
        $.post('verify-instance', data)
            .done(function () {
                $('#awsInstanceIdField').text('');
                showNext();
            })
            .fail(function (data) {
                $('#awsInstanceIdField').text('Error: ' + data.responseText);
            });
    }

    // Add storage settings
    function customizePersistence() {
        $('#configStart').hide();
        $('#persistenceSettings').show();
    }

    // Start over with storage settings
    function resetPersistence() {
        $('#configStart').show();
        $('#persistenceSettings').hide();
        resetProgress();
    }

    // Add storage settings
    function customizeStorage() {
        $('#persistenceSettings').hide();
        $('#storageSettings').show();
    }

    // Start over with storage settings
    function resetStorage() {
        $('#persistenceSettings').show();
        $('#storageSettings').hide();
        resetProgress();
    }

    function resetConfig() {
        $('#configStart').show();
        $('#confirmSettings').hide();
    }

    // Select storage type
    function selectStorage(event) {
        var type = event.target.value;

        $('#s3Storage').toggleClass('hidden', type !== 's3');
        $('#storageTypeLabel').text(type);
        validateForm('#deepStoreConfig');
    }

    // Select mysql type
    function selectPersistence(event) {
        var type = event.target.value;

        $('#mysqlSettings').toggleClass('hidden', type !== 'external');
        $('#mysqlTypeLabel').text(type);
        validateForm('#persistenceConfig');
    }

    function toggleButton(selector, enabled) {
        if (enabled) {
            $(selector).removeClass('disabled').removeAttr('disabled');
        } else {
            $(selector).addClass('disabled').attr('disabled', true);
        }
    }

    function getS3Values() {
        return {
            s3Endpoint: $('#s3Endpoint').val().trim(),
            storageBaseKey: 'druid-segments',
            storageBucket: $('#s3Bucket').val().trim(),
            secretKey: $('#s3SecretKey').val().trim(),
            accessKey: $('#s3AccessKey').val().trim()
        };
    }

    function getMySQLValues() {
        return {
            database: $('#mysqlDb').val().trim(),
            user: $('#mysqlUser').val().trim(),
            password: $('#mysqlPwd').val().trim(),
            host: $('#mysqlHost').val().trim(),
            port: $('#mysqlPort').val().trim()
        };
    }

    function getPersistenceType() {
        return $('#mysqlType').val();
    }

    function getStorageType() {
        return $('#storageType').val();
    }

    function getFlavor() {
        return $('#flavor').val();
    }

    function getLicenseKey() {
        return $('#licenseKey').val().trim();
    }

    function updateProgress(type, progressBar, msgElem, message, isHtml) {
        const removeCls = type === 'success' ? 'danger' : 'success';
        $(progressBar)
            .addClass(`progress-bar-${type}`)
            .removeClass(`progress-bar-${removeCls}`);
        updateProgressPercent(progressBar, 100);

        $(msgElem)
            .addClass(`text-${type}`)
            .removeClass(`text-${removeCls}`);

        if (isHtml) {
            $(msgElem).html(message);
        } else {
            $(msgElem).text(message);
        }
    }

    function success(progressBar, msgElem) {
        updateProgress('success', progressBar, msgElem, 'Success!');
    }

    function failure(progressBar, msgElem, msg, isHtml) {
        updateProgress('danger', progressBar, msgElem, msg, isHtml);
    }

    function addLicense(orgId) {
        const licenseData = {
            key: getLicenseKey(),
            orgId
        };

        return $.post('license/activate', licenseData)
            .then(function(licenses) {
                success('#licenseRegistrationProgressBar', '#licenseRegistrationMessage');
                return true;
            })
            .fail(function (err) {
                failure('#licenseRegistrationProgressBar', '#licenseRegistrationMessage',
                    err.responseText);
            });
    }

    function startConfiguration() {
        const type = $("input[name='setupType']:checked").val();

        if (type === 'custom') {
            customizePersistence();
        } else {
            confirmConfiguration('#configStart');
        }
    }

    function finishConfiguration() {
        confirmConfiguration('#storageSettings');
    }

    function confirmConfiguration(previousId) {
        $(previousId).hide();
        $('#confirmSettings').show();
    }

    function testPersistenceConfig() {
        const mysqlType = getPersistenceType();
        const errField = $('#mysqlError');

        errField.empty();
        errField.toggleClass('hidden', true);

        if (mysqlType === 'local') {
            return customizeStorage();
        }

        const mysqlConfig = getMySQLValues();

        function handleError(err) {
            errField.text(`Failed to connect to MySQL database: ${err.message || err}`);
            errField.toggleClass('hidden', false);
        }

        $.post('user-persistence/test', mysqlConfig)
            .then(function(result) {
                if (result.ok) {
                    return customizeStorage();
                }
                handleError(result.error || result.code);
            })
            .fail(handleError);
    }

    function configureSystem() {
        $('#confirmSettings').hide();
        $('#registrationProgress').show();

        const username = $('#newUsername').val();
        const password = $('#newPassword').val();

        var userData = {
            email: $('#email').val().trim(),
            password: password,
            firstName: $('#firstName').val().trim(),
            lastName: $('#lastName').val().trim(),
            licenseKey: getLicenseKey()
        };

        if (username) {
            userData.username = username;
        }

        const login = function() {
            return $.post('login', {username, password});
        };

        const createUser = function() {
            return $.post('registration', userData)
                .then(function (user) {
                    success('#newUserProgressBar', '#newUserMessage');
                    updateProgressPercent('#newConfigProgressBar', 20);

                    $('#hiddenUserField').val(username);
                    $('#hiddenPasswordField').val(password);

                    return user;
                })
                .fail(function (xhrResponse, textStatus, errorThrown) {
                    var errorMessage = errorThrown.message || xhrResponse.responseText;

                    console.error(errorThrown.stack); // eslint-disable-line no-console

                    failure('#newUserProgressBar', '#newUserMessage', errorMessage);
                });
        };

        const persistenceType = getPersistenceType();
        const storageType = getStorageType();
        const flavor = getFlavor();

        var configurePersistence = DEFERRED_NOOP;

        if (persistenceType !== 'local') {
            const persistenceData = {
                type: persistenceType,
                properties: getMySQLValues()
            };

            configurePersistence = function() {
                return $.post('user-persistence/configure', persistenceData);
            };
        }

        var configureStore = DEFERRED_NOOP;
        var configureStorageBackup = DEFERRED_NOOP;

        if (storageType !== 'local') {
            var storeData = {
                type: storageType,
                properties: getS3Values()
            };

            if (flavor == 'Pro') {
                configureStore = function() {
                    return $.post('druid-deep-store', storeData);
                }
            }

            // Update mysql with settings
            storeData.retentionPeriod = {value: 180, unit: 'days'};
            storeData.isDeepStoreEnabled = flavor == 'Pro';

            // must be logged in first
            configureStorageBackup = function() {
                return $.ajax({
                        type: 'post',
                        url: 'auth-api/settings/storage',
                        headers: {
                          'content-type': 'application/json'
                        },
                        data: JSON.stringify(storeData)
                    })
                    .then(function() {
                        // Send message to backups service to reconfigure
                        return $.post('backups/config', {message: 'reconfigure'});
                    });
            };
        }

        const isFeedbackEnabled = $('#feedbackTrack').is(':checked');

        // must be logged in first
        const configureSettings = function() {
            return $.ajax({
                    type: 'post',
                    url: 'auth-api/settings/feedback',
                    headers: {
                        'content-type': 'application/json'
                    },
                    data: JSON.stringify({
                        track: isFeedbackEnabled
                    })
                })
                .then(function() {
                    return $.post('error-reporting', {enabled: isFeedbackEnabled})
                });
        };

         // now run everything
        $.when(configurePersistence())
            .then(createUser)
            .then(function(user) {
                const orgId = user.ActiveOrganizationMembership.organizationId;

                return addLicense(orgId);
            })
            .then(login)
            .then(function () {

                return configureStore();
            })
            .then(function () {

                return $.when(configureSettings(), configureStorageBackup());
            })
            .then(function() {
                const results = Array.prototype.slice.call(arguments);
                const allOk = results.every(Boolean);

                if (allOk) {
                    success('#newConfigProgressBar', '#newConfigMessage');
                    setTimeout(showNext, 1000);
                }
            })
            .fail(function(err) {
                failure('#newConfigProgressBar', '#newConfigMessage',
                    err.responseJSON && err.responseJSON.message || err.responseText);
            });
    }

    function requestLicense(event) {
        event.preventDefault();

        const progressMessage = $('#requestLicenseMessage');
        progressMessage.removeClass('text-success text-danger').text('Requesting evaluation license...');

        const progressBar = $('#requestLicenseProgressBar');
        progressBar.removeClass('progress-bar-success progress-bar-danger');
        updateProgressPercent(progressBar, 60);

        $('#requestLicenseProgress').show();

        const userData = {
            'email': $('#licenseEmail').val().trim(),
            'firstName': $('#licenseFirstName').val().trim(),
            'lastName': $('#licenseLastName').val().trim(),
            'password': $('#licensePassword').val().trim(),
            'company': $('#licenseCompany').val().trim()
        };

        $.ajax({
            method: 'POST',
            url: 'license/register',
            data: userData,
            dataType: 'json',
            timeout: 30000
        })
        .done(function(license) {
            success(progressBar, progressMessage);

            $('#requestLicenseProgress').delay(1000).fadeOut(500);

            setTimeout(function() {
                $('#licenseKey').val(license.licenseKey);
                $('#licenseKey').keyup();
                $('input[name="licenseType"][value="new"]').prop('disabled', true);
                $('input[name="licenseType"][value="existing"]').click();
            }, 1000);
        })
        .fail(function(err, statusText) {
            var msg = err.responseText;
            var isHtml = false;

            if (statusText === 'timeout') {
                msg = 'Request timed out.';
            }

            if (err.status === 401) {
                msg = 'You have an existing Epoch account.<br>Please <a href="https://lm.epoch.nutanix.com" target="_blank">login</a> to generate your license key.';
                isHtml = true;
            }

            failure(progressBar, progressMessage, msg, isHtml);
            // TODO: show skip button on failure
        });
    }

    function verifyLicense(event, registerImmediately) {
        event.preventDefault();

        const licenseData = {
            key: getLicenseKey()
        };

        $.post('license/verify', licenseData)
        .then(function() {
            return registerImmediately ? addLicense() : $.Deferred().resolve(true);
        })
        .then(function() {
            showNext();
        })
        .fail(function (error) {
            if (registerImmediately) {
                addLicense().then(function() {
                    showNext();
                });
            } else {
                showNext();
            }
        });
    }

    return {
        init,
        showPrev,
        showNext,
        verifyInstance,
        startConfiguration,
        finishConfiguration,
        customizeStorage,
        customizePersistence,
        testPersistenceConfig,
        resetConfig,
        resetStorage,
        resetPersistence,
        configureSystem,
        selectStorage,
        selectPersistence,
        requestLicense,
        verifyLicense
    };
})();