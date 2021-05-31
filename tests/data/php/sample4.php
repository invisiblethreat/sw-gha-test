<?php
/**
 * EKR Blank Starter Theme
 *
 * @link https://developer.wordpress.org/themes/basics/theme-functions/
 */
// require_once(get_template_directory().'/lib/iContact/iContactApi.php');
require_once(get_template_directory().'/lib/mailchimp-api-master/src/MailChimp.php');
use \DrewM\MailChimp\MailChimp;


/** ---------------------------------------------------------------------------
 * Sets up theme defaults and registers support for various WordPress features.
 */
function ekrblank_setup() {
        /*
         * Let WordPress manage the document title.
         * By adding theme support, we declare that this theme does not use a
         * hard-coded <title> tag in the document head, and expect WordPress to
         * provide it for us.
         */
        add_theme_support('title-tag');

        /*
         * Remove WP Emoji and other unnessesary code
         */
        remove_action('wp_head', 'print_emoji_detection_script', 7);
        remove_action('wp_print_styles', 'print_emoji_styles');
        remove_action('admin_print_scripts', 'print_emoji_detection_script');
        remove_action('admin_print_styles', 'print_emoji_styles');
        remove_action('wp_head', 'rsd_link');
        remove_action('wp_head', 'wlwmanifest_link');
        remove_action('wp_head', 'wp_generator');
        remove_action('wp_head', 'wp_shortlink_wp_head', 10, 0);
        remove_action('wp_head', 'rest_output_link_wp_head');
        remove_action('wp_head', 'wp_oembed_add_discovery_links');
        remove_action('template_redirect', 'rest_output_link_header', 11, 0);
        add_filter('emoji_svg_url', '__return_false');

        // Register menus
        register_nav_menus(array(
                'header' => __('Header Menu', 'ekr'),
                'footer-primary' => __('Footer Menu Primary', 'ekr'),
                'footer-secondary' => __('Footer Menu Secondary', 'ekr'),
                'footer-tertiary' => __('Footer Menu Tertiary', 'ekr')
        ));

        // Register a sidebar
        register_sidebar(array(
                'name' => 'Main Sidebar',
                'id' => 'main-sidebar',
                'before_widget' => '<div class="widget">',
                'after_widget' => '</div>',
                'before_title' => '<h3 class="widgettitle">',
                'after_title' => '</h3>'
        ));

        /*
         * Switch default core markup for search form and comment form to use HTML5 tags
         */
        add_theme_support('html5', array(
                'comment-form',
                'search-form'
        ));

        add_theme_support('responsive-embeds');
}
add_action('after_setup_theme', 'ekrblank_setup');


/** ---------------------------------------------------------------------------
 * Load styles and javascript needed for theme
 */
function theme_enqueue_styles() {
        // Get the theme data
        $the_theme = wp_get_theme();

        // load custom styles and js for theme
        wp_enqueue_style(
                'slick',
                get_template_directory_uri().'/js/lib/slick/slick.css',
                array(),
                $the_theme->get('Version')
        );
        wp_enqueue_style(
                'slick-theme',
                get_template_directory_uri().'/js/lib/slick/slick-theme.css',
                array('slick'),
                $the_theme->get('Version')
        );
        wp_enqueue_style(
                'ekr-styles',
                get_template_directory_uri().'/style.css',
                array('slick-theme'),
                $the_theme->get('Version')
        );
        wp_enqueue_style(
                'map-styles',
                'https://js.arcgis.com/4.12/esri/css/main.css',
                array('ekr-styles'),
                $the_theme->get('Version')
        );

        wp_enqueue_script(
                'ekr-scripts',
                get_template_directory_uri().'/js/scripts.js',
                array('jquery'),
                $the_theme->get('Version'),
                true
        );
        wp_enqueue_script(
                'slick',
                get_template_directory_uri().'/js/lib/slick/slick.min.js',
                array('ekr-scripts'),
                $the_theme->get('Version'),
                true
        );
        wp_enqueue_script(
                'map-script',
                'https://js.arcgis.com/4.12/',
                array('slick'),
                wp_get_theme()->get('Version'),
                true
        );

        $custom_js_vars = array(
                'template_uri' => get_template_directory_uri()
        );
        wp_localize_script('ekr-scripts', 'GOED', $custom_js_vars);
}
add_action('wp_enqueue_scripts', 'theme_enqueue_styles');

function add_defer_attribute($tag, $handle) {
        if ( 'googleapis' !== $handle )
        return $tag;
        return str_replace( ' src', ' defer src', $tag );
}
add_filter('script_loader_tag', 'add_defer_attribute', 10, 2);

function add_async_attribute($tag, $handle) {
        if ( 'googleapis' !== $handle )
        return $tag;
        return str_replace( ' src', ' async src', $tag );
}
add_filter('script_loader_tag', 'add_async_attribute', 10, 2);

/** ---------------------------------------------------------------------------
 * Add theme options page
 *
 * add_theme_page(
 *         'Theme Options',                // The title to be displayed in the browser window for this page.
 *         'Theme Options',                // The text to be displayed for this menu item
 *         'administrator',                // Which type of users can see this menu item
 *         'theme_option_id',      // The unique ID - that is, the slug - for this menu item
 *         'theme_option_callback' // The name of the function to call when rendering this menu's page
 * );
 */

function ekr_theme_menu() {
        add_theme_page(
                'Theme Options',
                'Theme Options',
                'administrator',
                'ekr_options',
                'ekr_display'
        );
}
add_action('admin_menu', 'ekr_theme_menu');

// Renders a simple page to display for the theme menu defined above.
function ekr_display() {
        ?>
                <div class="wrap">
                        <div id="icon-themes" class="icon32"></div>
                        <h2>Theme Options</h2>
                        <?php settings_errors(); ?>

                        <form method="post" action="options.php">
                                <?php settings_fields('ekr_display_options'); ?>
                                <?php do_settings_sections('ekr_display_options'); ?>
                                <?php submit_button(); ?>
                        </form>
                </div>
        <?php
}

// Add settings
function ekr_initialize_theme_options() {
        // If the theme options don't exist, create them.
        if(false == get_option('ekr_display_options')) {
                add_option('ekr_display_options');
        }

        /** --------------------------------------------------------
         *      Adding a section for the settings
         *
         * add_settings_section(
         *         'setting_section_id',                   // ID used to identify this section and with which to register options
         *         'Setting Section Name',                 // Title to be displayed on the administration page
         *         'setting_section_callback',     // Callback used to render the description of the section
         *         'setting_page'                                  // Page on which to add this section of options
         * );
         */

        // Register General Settings Section
        add_settings_section(
                'general_settings_section',
                'General Settings',
                'ekr_general_options_callback',
                'ekr_display_options'
        );

        // Contact Information
        add_settings_section(
                'contact_info_section',
                'General Contact Information',
                'ekr_contactinfo_callback',
                'ekr_display_options'
        );

        // Social Sharing
        add_settings_section(
                'social_section',
                'Social Media Links',
                'ekr_social_callback',
                'ekr_display_options'
        );

        /** -----------------------------------------------------
         *      Adding fields to the section
         *
         * add_settings_field(
         *         'setting_field_id',                  // ID used to identify the field throughout the theme
         *         'Setting Filed Name',                // The label to the left of the option interface element
         *         'setting_field_callback',    // The name of the function responsible for rendering the option interface
         *         'setting_page',                              // The page on which this option will be displayed
         *         'setting_section',                   // The name of the section to which this field belongs
         *         array(                                               // The array of arguments to pass to the callback
         *                 'setting', // field name
         *                 '500px'        // field width
         *         )
         * );
         */

        // Add Fields
        add_settings_field(
                'copyright',
                'Copyright Text',
                'ekr_textfield_callback',
                'ekr_display_options',
                'general_settings_section',
                array(
                        'copyright',
                        '500px'
                )
        );

        add_settings_field(
                'phone',
                'Phone Number',
                'ekr_textfield_callback',
                'ekr_display_options',
                'contact_info_section',
                array(
                        'phone',
                        '200px'
                )
        );

        add_settings_field(
                'address',
                'Address',
                'ekr_textfield_callback',
                'ekr_display_options',
                'contact_info_section',
                array(
                        'address',
                        '300px'
                )
        );

        add_settings_field(
                'city',
                'City',
                'ekr_textfield_callback',
                'ekr_display_options',
                'contact_info_section',
                array(
                        'city',
                        '300px'
                )
        );

        add_settings_field(
                'state',
                'State',
                'ekr_textfield_callback',
                'ekr_display_options',
                'contact_info_section',
                array(
                        'state',
                        '300px'
                )
        );

        add_settings_field(
                'zip',
                'Zip',
                'ekr_textfield_callback',
                'ekr_display_options',
                'contact_info_section',
                array(
                        'zip',
                        '100px'
                )
        );

        add_settings_field(
                'facebook',
                'Facebook',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'facebook',
                        '500px'
                )
        );

        add_settings_field(
                'twitter',
                'Twitter',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'twitter',
                        '500px'
                )
        );

        add_settings_field(
                'linkedin',
                'LinkedIn',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'linkedin',
                        '500px'
                )
        );

        add_settings_field(
                'youtube',
                'YouTube',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'youtube',
                        '500px'
                )
        );

        add_settings_field(
                'pintrest',
                'Pintrest',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'pintrest',
                        '500px'
                )
        );

        add_settings_field(
                'instagram',
                'Instagram',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'instagram',
                        '500px'
                )
        );

        add_settings_field(
                'google',
                'Google Plus',
                'ekr_textfield_callback',
                'ekr_display_options',
                'social_section',
                array(
                        'google',
                        '500px'
                )
        );

        // Finally, we register the fields with WordPress
        register_setting(
                'ekr_display_options',
                'ekr_display_options'
        );

} // end ekr_initialize_theme_options
add_action('admin_init', 'ekr_initialize_theme_options');

// Add section callback functions
function ekr_general_options_callback() {
        echo '<p>These settings are global and will be used throughout the site.</p>';
}
function ekr_contactinfo_callback() {
        // do nothing
}
function ekr_social_callback() {
        // do nothing
}

// Add field callback functions
function ekr_textfield_callback($args) {
        // First, we read the options collection
        $options = get_option('ekr_display_options');

        // Next, we update the name attribute to access this element's ID in the context of the display options array
        $html = '<input type="input" id="'      . $args[0] . '" name="ekr_display_options['  . $args[0] . ']" value="'.$options[$args[0]].'" style="width:100%; max-width:'.$args[1].'" />';

        echo $html;
}

function ekr_toggle_callback($args) {
        $options = get_option('ekr_display_options');

        $html = '<input type="checkbox" id="'.$args[0].'" name="ekr_display_options['.$args[0].']" value="1" ' . checked(1, $options[$args[0]], false) . '/>';
        $html .= '<label for="show_content"> '  . $args[1] . '</label>';

        echo $html;
}

function create_custom_post_types() {
        register_post_type('office', array(
                'labels' => array(
                        'name' => 'offices',
                        'singular_name' => 'office',
                        'plural_name' => __('offices'),
                        'edit_item' => __('Edit Office'),
                        'add_new_item' => __('Add New Office'),
                        'update_item' => __('Update Office'),
                        'new_item_name' => __('Add New Office'),
                        'add_or_remove_items' => __('Add or Remove Office'),
                        'view_item' => __('View Office'),
                        'menu_name' => __('Offices')
                ),
                'public' => true,
                'hierarchical' => false,
                'has_archive' => false,
                'publicly_queryable' => true,
                'exclude_from_search' => true,
                'supports' => array(),
                'can_export' => true
        ));
        register_post_type('incented-companies', array(
                'labels' => array(
                        'name' => 'Incented Companies',
                        'singular_name' => 'Incented Company',
                        'edit_item' => __('Edit Company'),
                        'add_new_item' => __('Add New Company'),
                        'update_item' => __('Update Company'),
                        'new_item_name' => __('Add New Company'),
                        'add_or_remove_items' => __('Add or Remove Company'),
                        'view_item' => __('View Company'),
                        'menu_name' => __('Incented Companies')
                ),
                'public' => true,
                'hierarchical' => false,
                'has_archive' => false,
                'publicly_queryable' => true,
                'exclude_from_search' => true,
                'supports' => array(),
                'can_export' => true
        ));
}
add_action('init', 'create_custom_post_types');

// add_filter('show_admin_bar', '__return_false');

function custom_excerpt_length( $length ) {
        return 10;
}
add_filter('excerpt_length', 'custom_excerpt_length', 999);

function ekr_truncate($string, $character_limit) {
        if(strlen($string) > $character_limit) {
                $string = substr($string, 0, strrpos(substr($string, 0, $character_limit), ' '));
                $string .= "&hellip;";
        }
        return $string;
}

function ekr_fetch_icon($icon) {
        if(file_exists(get_template_directory().'/images/icon-'.$icon.'.svg')) {
                include(get_template_directory().'/images/icon-'.$icon.'.svg');
        }
}

function ekr_cf7_button_tag_handler($tag) {
        $class = wpcf7_form_controls_class( $tag->type );

        $atts = array();

        $atts['class'] = $tag->get_class_option($class);
        $atts['id'] = $tag->get_id_option();
        $atts['tabindex'] = $tag->get_option( 'tabindex', 'signed_int', true );

        $value = isset( $tag->values[0] ) ? $tag->values[0] : '';

        if(empty( $value)) {
                $value = __('Send', 'contact-form-7');
        }

        $atts['type'] = 'submit';
        $atts['value'] = $value;

        $atts = wpcf7_format_atts($atts);

        $html = sprintf( '<button %1$s>%2$s</button>', $atts, $value);

        return $html;
}
function ekr_wpcf7_add_tags() {
        wpcf7_add_form_tag('button', 'ekr_cf7_button_tag_handler', true);
}
add_action('wpcf7_init', 'ekr_wpcf7_add_tags');

function ekr_get_wpcf7_id_by_name($name) {
        global $wpdb;
        $id = $wpdb->get_var($wpdb->prepare("".
                "SELECT ID FROM wp_posts
                        WHERE
                                post_status = 'publish' AND
                                post_title LIKE %s AND
                                post_type = 'wpcf7_contact_form'",
                $name
        ));
        return $id;
}

/**
 *
 * Change Posts label to News
 *
**/
function change_post_label() {
        global $menu;
        global $submenu;
        $user = wp_get_current_user();
        if(in_array('edit_posts', (array)$user->roles)) {
                $menu[5][0] = 'News';
                $submenu['edit.php'][5][0] = 'News';
                $submenu['edit.php'][10][0] = 'Add News';
                $submenu['edit.php'][16][0] = 'News Tags';
        }
}
function change_post_object() {
        global $wp_post_types;
        $labels = &$wp_post_types['post']->labels;
        $labels->name = 'News';
        $labels->singular_name = 'News';
        $labels->add_new = 'Add News';
        $labels->add_new_item = 'Add News';
        $labels->edit_item = 'Edit News';
        $labels->new_item = 'News';
        $labels->view_item = 'View News';
        $labels->search_items = 'Search News';
        $labels->not_found = 'No News found';
        $labels->not_found_in_trash = 'No News found in Trash';
        $labels->all_items = 'All News';
        $labels->menu_name = 'News';
        $labels->name_admin_bar = 'News';
}

add_action( 'admin_menu', 'change_post_label' );
add_action( 'init', 'change_post_object' );

function add_user_fields() {
        acf_add_local_field_group(array(
                'key' => 'user_fields',
                'title' => 'Additional User Fields',
                'fields' => array(
                        array(
                                'key' => 'user_title',
                                'name' => 'user_title',
                                'label' => 'User Title',
                                'type' => 'text'
                        ),
                        array(
                                'key' => 'user_phone',
                                'name' => 'user_phone',
                                'label' => 'User Phone',
                                'type' => 'text'
                        ),
                        array(
                                'key' => 'user_twitter',
                                'name' => 'user_twitter',
                                'label' => 'User Twitter Handle',
                                'type' => 'text'
                        ),
                        array(
                                'key' => 'user_image',
                                'name' => 'user_image',
                                'label' => 'User Image',
                                'type' => 'image'
                        )
                ),
                'location' => array(
                        array(
                                array(
                                        'param' => 'user_role',
                                        'operator' => '==',
                                        'value' => 'all'
                                )
                        )
                )
        ));
}
add_action('acf/init', 'add_user_fields');

function add_post_fields() {
        acf_add_local_field_group(array(
                'key' => 'post_fields',
                'title' => 'Additional Post Settings',
                'fields' => array(
                        array(
                                'key' => 'post_hide_author',
                                'name' => 'post_hide_author',
                                'label' => 'Hide Post Author',
                                'type' => 'true_false',
                                'default_value' => 1
                        ),
                ),
                'position' => 'side',
                'location' => array(
                        array(
                                array(
                                        'param' => 'post_type',
                                        'operator' => '==',
                                        'value' => 'post'
                                )
                        ),
                        array(
                                array(
                                        'param' => 'post_type',
                                        'operator' => '==',
                                        'value' => 'project'
                                )
                        )
                )
        ));
}
add_action('acf/init', 'add_post_fields');

function add_social_fields() {
        acf_add_local_field_group(array(
                'key' => 'social_fields',
                'title' => 'Social Page Fields',
                'fields' => array(
                        array(
                                'key' => 'youtube_embed',
                                'name' => 'youtube_embed',
                                'label' => 'YouTube Video Embed Code',
                                'instructions' => 'Copy and paste the YouTube embed code. On the YouTube video page click "Share" then "Embed" and copy the code that shows up on the right of the video',
                                'type' => 'textarea'
                        ),
                ),
                'location' => array(
                        array(
                                array(
                                        'param' => 'post_template',
                                        'operator' => '==',
                                        'value' => 'templates/template-social.php'
                                )
                        )
                )
        ));
}
add_action('acf/init', 'add_social_fields');


function ekr_submit_email_to_list_manager($cf7) {
        $sub = WPCF7_Submission::get_instance();
        $MailChimp = new MailChimp('a7bc3013c9919fd6677e1faa0fe05e2d-us19');

        if($cf7->title() == 'Newsletter Form') {
                $user_email = $sub->get_posted_data('user-email');
                $utah_talks_business = $sub->get_posted_data('utah-talks-business')[0];
                $utah_talks_outdoors = $sub->get_posted_data('utah-talks-outdoors')[0];
                $ptac_newsletter = $sub->get_posted_data('ptac-newsletter')[0];
                $stem_ac_newsletter = $sub->get_posted_data('stem-ac-newsletter')[0];
                $broadband_newsletter = $sub->get_posted_data('broadband-newsletter')[0];

                $list_id = false;
                /*
                $result = $MailChimp->get("lists");
                var_dump($result);
                */
                if($utah_talks_business) {
                        // GOED Public
                        $list_id = '3084840a9f';
                        $result = $MailChimp->post("lists/$list_id/members", array(
                                'email_address' => $user_email,
                                'status' => 'subscribed'
                        ));
                }
                if($utah_talks_outdoors) {
                        // Utah GOED Office of Outdoor Recreation
                        $list_id = '4b49378fec';
                        $result = $MailChimp->post("lists/$list_id/members", array(
                                'email_address' => $user_email,
                                'status' => 'subscribed'
                        ));
                }
                if($ptac_newsletter) {
                        // Utah GOED PTAC
                        $list_id = '9e01bc1db2';
                        $result = $MailChimp->post("lists/$list_id/members", array(
                                'email_address' => $user_email,
                                'status' => 'subscribed'
                        ));
                }
                if($stem_ac_newsletter) {
                        // Utah GOED STEM AC newsletter
                        $list_id = 'e95642eda6';
                        $result = $MailChimp->post("lists/$list_id/members", array(
                                'email_address' => $user_email,
                                'status' => 'subscribed'
                        ));
                }
                if($broadband_newsletter) {
                }

                /*
                iContactApi::getInstance()->setConfig(array(
                        'appId'       => 'IrZH2zHCB4QRbiuYzlmpSF6RMMQTuO03',
                        'apiPassword' => 'bea3MiiUp',
                        'apiUsername' => 'goed2010'
                ));
                $oiContact = iContactApi::getInstance();
                try {
                        $contact = $oiContact->addContact($user_email);

                        if($utah_talks_business) {
                                $oiContact->subscribeContactToList($contact->contactId, 1154, 'normal');
                        }
                        if($utah_talks_outdoors) {
                                $oiContact->subscribeContactToList($contact->contactId, 38935, 'normal');
                        }
                        if($ptac_newsletter) {
                                $oiContact->subscribeContactToList($contact->contactId, 50077, 'normal');
                        }
                        if($stem_ac_newsletter) {
                                $oiContact->subscribeContactToList($contact->contactId, 44270, 'normal');
                        }
                        if($broadband_newsletter) {
                                $oiContact->subscribeContactToList($contact->contactId, 45572, 'normal');
                        }
                } catch (Exception $oException) {
                        var_dump($oiContact->getErrors());
                        var_dump($oiContact->getLastRequest());
                        var_dump($oiContact->getLastResponse());
                }
                */
        }
}
add_action('wpcf7_before_send_mail', 'ekr_submit_email_to_list_manager');


// Imported from original website.
if(function_exists("register_field_group")) {
        register_field_group(array (
                'id' => 'acf_incented-companies-posts',
                'title' => 'Incented Companies (Posts)',
                'fields' => array (
                        array (
                                'key' => 'field_5238ce83f6b9f',
                                'label' => 'Project Summary',
                                'name' => '',
                                'type' => 'tab',
                        ),
                        array (
                                'key' => 'field_5238d12bf6ba0',
                                'label' => 'Project',
                                'name' => 'project',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_524490e691ff2',
                                'label' => 'Board Approved Date',
                                'name' => 'board_approved_date',
                                'type' => 'repeater',
                                'sub_fields' => array (
                                        array (
                                                'key' => 'field_5244912a91ff3',
                                                'label' => 'Month',
                                                'name' => 'month',
                                                'type' => 'select',
                                                'column_width' => '',
                                                'choices' => array (
                                                        '01' => 'January',
                                                        '02' => 'February',
                                                        '03' => 'March',
                                                        '04' => 'April',
                                                        '05' => 'May',
                                                        '06' => 'June',
                                                        '07' => 'July',
                                                        '08' => 'August',
                                                        '09' => 'September',
                                                        10 => 'October',
                                                        11 => 'November',
                                                        12 => 'December',
                                                ),
                                                'default_value' => '',
                                                'allow_null' => 0,
                                                'multiple' => 0,
                                        ),
                                        array (
                                                'key' => 'field_524491aa91ff4',
                                                'label' => 'Day',
                                                'name' => 'day',
                                                'type' => 'select',
                                                'column_width' => '',
                                                'choices' => array (
                                                        '01' => 1,
                                                        '02' => 2,
                                                        '03' => 3,
                                                        '04' => 4,
                                                        '05' => 5,
                                                        '06' => 6,
                                                        '07' => 7,
                                                        '08' => 8,
                                                        '09' => 9,
                                                        10 => 10,
                                                        11 => 11,
                                                        12 => 12,
                                                        13 => 13,
                                                        14 => 14,
                                                        15 => 15,
                                                        16 => 16,
                                                        17 => 17,
                                                        18 => 18,
                                                        19 => 19,
                                                        20 => 20,
                                                        21 => 21,
                                                        22 => 22,
                                                        23 => 23,
                                                        24 => 24,
                                                        25 => 25,
                                                        26 => 26,
                                                        27 => 27,
                                                        28 => 28,
                                                        29 => 29,
                                                        30 => 30,
                                                        31 => 31,
                                                ),
                                                'default_value' => '',
                                                'allow_null' => 0,
                                                'multiple' => 0,
                                        ),
                                        array (
                                                'key' => 'field_524491b891ff5',
                                                'label' => 'Year',
                                                'name' => 'year',
                                                'type' => 'select',
                                                'column_width' => '',
                                                'choices' => array (
                                                        2004 => 2004,
                                                        2005 => 2005,
                                                        2006 => 2006,
                                                        2007 => 2007,
                                                        2008 => 2008,
                                                        2009 => 2009,
                                                        2010 => 2010,
                                                        2011 => 2011,
                                                        2012 => 2012,
                                                        2013 => 2013,
                                                        2014 => 2014,
                                                        2015 => 2015,
                                                        2016 => 2016,
                                                        2017 => 2017,
                                                        2018 => 2018,
                                                        2019 => 2019,
                                                        2020 => 2020,
                                                        2021 => 2021,
                                                        2022 => 2022,
                                                        2023 => 2023,
                                                        2024 => 2024,
                                                        2025 => 2025,
                                                        2026 => 2026,
                                                        2027 => 2027,
                                                        2028 => 2028,
                                                        2029 => 2029,
                                                        2030 => 2030,
                                                ),
                                                'default_value' => 2013,
                                                'allow_null' => 0,
                                                'multiple' => 0,
                                        ),
                                ),
                                'row_min' => 1,
                                'row_limit' => 1,
                                'layout' => 'table',
                                'button_label' => 'Add Row',
                        ),
                        array (
                                'key' => 'field_5245c9d1c2cf9',
                                'label' => 'Address',
                                'name' => 'address',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5245c9e2c2cfa',
                                'label' => 'City',
                                'name' => 'city',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5245c9f2c2cfb',
                                'label' => 'State',
                                'name' => 'state',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5245c9fdc2cfc',
                                'label' => 'Zip Code',
                                'name' => 'zip_code',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d19cf6ba3',
                                'label' => 'Type',
                                'name' => 'type',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d1a6f6ba4',
                                'label' => 'Term',
                                'name' => 'term',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d1aef6ba5',
                                'label' => 'Number of Jobs',
                                'name' => 'number_of_jobs',
                                'type' => 'number',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'min' => '',
                                'max' => '',
                                'step' => '',
                        ),
                        array (
                                'key' => 'field_5238d1e8f6ba6',
                                'label' => 'New State Wages',
                                'name' => 'new_state_wages',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '$',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d20cf6ba7',
                                'label' => 'New State Revenue',
                                'name' => 'new_state_revenue',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '$',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d227f6ba8',
                                'label' => 'Capital Investment',
                                'name' => 'capital_investment',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '$',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d245f6ba9',
                                'label' => 'Maximum Cap. Incentive',
                                'name' => 'maximum_cap_incentive',
                                'type' => 'text',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '$',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d290c09a1',
                                'label' => 'Logo',
                                'name' => 'logo',
                                'type' => 'image',
                                'instructions' => 'Logo dimensions: 200 pixels wide by 100 pixels tall. Will scale to fit.',
                                'save_format' => 'id',
                                'preview_size' => 'incented_logo',
                                'library' => 'all',
                        ),
                        array (
                                'key' => 'field_524490c591ff1',
                                'label' => 'Web Address (URL)',
                                'name' => 'web_address',
                                'type' => 'text',
                                'instructions' => 'Enter a url to the companies website.',
                                'default_value' => '',
                                'placeholder' => '',
                                'prepend' => '',
                                'append' => '',
                                'formatting' => 'html',
                                'maxlength' => '',
                        ),
                        array (
                                'key' => 'field_5238d260c09a0',
                                'label' => 'Board Motion',
                                'name' => '',
                                'type' => 'tab',
                        ),
                        array (
                                'key' => 'field_5238d35f6be8f',
                                'label' => 'Board Motion Text',
                                'name' => 'board_motion_text',
                                'type' => 'wysiwyg',
                                'default_value' => '',
                                'toolbar' => 'full',
                                'media_upload' => 'yes',
                        ),
                        array (
                                'key' => 'field_5238d37a6be90',
                                'label' => 'Map of Location',
                                'name' => '',
                                'type' => 'tab',
                        ),
                        array (
                                'key' => 'field_5238d3936be91',
                                'label' => 'Map',
                                'name' => 'map',
                                'type' => 'wysiwyg',
                                'default_value' => '',
                                'toolbar' => 'full',
                                'media_upload' => 'yes',
                        ),
                        array (
                                'key' => 'field_5238d39f6be92',
                                'label' => 'Press Release',
                                'name' => '',
                                'type' => 'tab',
                        ),
                        array (
                                'key' => 'press_release_link',
                                'label' => 'Press Release Link',
                                'name' => 'press_release_link',
                                'instructions' => 'If included, it will display a button rather than the text below',
                                'type' => 'text',
                        ),
                        array (
                                'key' => 'field_5238d3ba6be93',
                                'label' => 'Press Release Text',
                                'name' => 'press_release_text',
                                'type' => 'wysiwyg',
                                'default_value' => '',
                                'toolbar' => 'full',
                                'media_upload' => 'yes',
                        ),
                ),
                'location' => array (
                        array (
                                array (
                                        'param' => 'post_type',
                                        'operator' => '==',
                                        'value' => 'incented-companies',
                                        'order_no' => 0,
                                        'group_no' => 0,
                                ),
                        ),
                ),
                'options' => array (
                        'position' => 'normal',
                        'layout' => 'no_box',
                        'hide_on_screen' => array (
                                0 => 'the_content',
                                1 => 'featured_image',
                        ),
                ),
                'menu_order' => 0,
        ));
}

function ekr_get_featured_image($post_id = null, $size = 'full') {
        if($post_id == null) {
                global $post;
                $post_id = $post->ID;
        }
        if($url = get_the_post_thumbnail_url($post_id, $size)) {
                return $url;
        } else {
                $src = wp_get_attachment_image_src(29604, $size);
                return $src[0];
        }
}

// include('functions-social.php');

/***
 * The following code was used to restructure the content from the old site to
 * the new site. I'm putting it here for future reference only.
 *
 * /alter-content.php
 *
 * require('./wp-load.php');
 * wp();
 * $posts = new WP_Query(array(
 *      'post_type' => 'post',
 *      'posts_per_page' => -1
 * ));
 * echo '<ul>';
 * if($posts->have_posts()) {
 *      while($posts->have_posts()) {
 *              $posts->the_post();
 *              $post_title = get_the_title();
 *              $article_content = get_post_meta($post->ID, 'article_content', true);
 *              $content = get_the_content();
 *              if($article_content && !$content) {
 *                      $post_id = wp_update_post(array(
 *                              'ID' => $post->ID,
 *                              'post_title' => $post_title,
 *                              'post_content' => $article_content
 *                      ));
 *                      if(is_wp_error($post_id)) {
 *                              $errors = $post_id->get_error_messages();
 *                              echo '<li>'.$post_title.': <strong>ERROR:</strong>';
 *                              foreach($errors as $error) {
 *                                      echo $error;
 *                              }
 *                              echo '</li>';
 *                      } else {
 *                              echo '<li>'.$post_title.': UPDATED SUCCESSFULLY</li>';
 *                      }
 *              } else {
 *                      echo '<li>'.$post_title.': CONTENT ALREADY EXISTS</li>';
 *              }
 *      }
 * }
 * echo '</ul>';
 */

 // Remove categories added by wpml, but not removed for some reason.
 // This should only run one time
 function remove_uncategorized_taxonomies() {
        global $wpdb;
        $ekr_manual_db_changes = get_option('ekr_manual_db_changes');
        if($ekr_manual_db_changes != '1.0') {
                $sql = "DROP TABLE IF EXISTS wp_icl_content_status";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_core_status";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_flags";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_languages";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_languages_translations";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_locale_map";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_message_status";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_mo_files_domains";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_node";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_reminders";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_strings";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_string_pages";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_string_positions";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_string_status";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_string_translations";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_string_urls";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_translate";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_translate_job";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_translations";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_translation_batches";
                $wpdb->query($sql);
                $sql = "DROP TABLE IF EXISTS wp_icl_translation_status";
                $wpdb->query($sql);
                $sql = "DELETE FROM wp_terms WHERE term_id IN (22,23,24,25,26,27,28)";
                $wpdb->query($sql);
                $sql = "DELETE FROM wp_term_taxonomy WHERE term_id IN (22,23,24,25,26,27,28)";
                $wpdb->query($sql);
                update_option('ekr_manual_db_changes', '1.0');
        }
 }
 add_action('init', 'remove_uncategorized_taxonomies');

 add_filter('ekr_acf/module_locations', 'add_newsroom_to_modules');
 function add_newsroom_to_modules($locations) {
        $newsroom = get_page_by_title('Newsroom');
        $locations[] = array(
                array(
                        'param' => 'page',
                        'operator' => '==',
                        'value' => $newsroom->ID
                )
        );
        return $locations;
 }
