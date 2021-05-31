<?php
/* Built using tutorial at
 * https://code.tutsplus.com/tutorials/a-guide-to-the-wordpress-http-api-automatic-plugin-updates--wp-25181
 */

class EKR_Plugin_Updater {
        private $gitlab_project_id;
        private $plugin_slug;
        private $plugin_basename;
        private $plugin_download_link;
        private $current_version;
        private $token = '11fzYzJL4yxCVhJHVZkn';
        private $gitlab_baseurl = 'https://gitlab.elikirk.com/api/v4/projects/';

        public function __construct($plugin_slug, $gitlab_project_id, $current_version) {
                $this->current_version = $current_version;
                $this->plugin_slug = $plugin_slug;
                list($t1, $t2) = explode('/', $plugin_slug);
                $this->plugin_basename = str_replace('.php', '', $t2);
                $this->plugin_directory = $t1;
                $this->gitlab_project_id = $gitlab_project_id;
                $this->plugin_download_link = $this->gitlab_baseurl.
                        $this->gitlab_project_id.
                        '/repository/archive.zip?private_token='.
                        $this->token;

                add_filter('pre_set_site_transient_update_plugins', array($this, 'check_update'));
                add_filter('plugins_api', array($this, 'check_info'), 10, 3);
                add_action('upgrader_process_complete', array($this, 'cleanup'), 10, 2);

                // Our gitlab server is technically local if you're in the office. WP
                // rejects local IPs for some reason, so we have to specifically allow
                // for this.
                add_filter('http_request_host_is_external', array($this, 'allow_local_ips'), 10, 3);
        }

        // Rename folder to match old plugin directory name.
        public function cleanup($upgrader_object, $options) {
                if($options['action'] == 'update' && $options['type'] == 'plugin' ) {
                        foreach($options['plugins'] as $plugin) {
                                if($plugin == $this->plugin_slug) {
                                        $installed_plugins = scandir(WP_PLUGIN_DIR);
                                        $upgrader_object->custom = serialize($installed_plugins);
                                        foreach($installed_plugins as $installed_plugin) {
                                                if(
                                                        is_dir(WP_PLUGIN_DIR.'/'.$installed_plugin) &&
                                                        strstr($installed_plugin, $this->plugin_directory) &&
                                                        $installed_plugin !== $this->plugin_directory
                                                ) {
                                                        rename(
                                                                WP_PLUGIN_DIR.'/'.$installed_plugin,
                                                                WP_PLUGIN_DIR.'/'.$this->plugin_directory
                                                        );
                                                }
                                        }
                                }
                        }
                }
        }

        public function check_update($transient) {
                if(empty($transient->checked)) {
                        return $transient;
                }

                $remote_version = $this->get_remote_version();

                if(version_compare($this->current_version, $remote_version, '<')) {
                        $transient_obj = new stdClass();
                        $transient_obj->slug = $this->plugin_basename;
                        $transient_obj->new_version = $remote_version;
                        $transient_obj->url = $this->gitlab_baseurl.$this->gitlab_project_id;
                        $transient_obj->package = $this->plugin_download_link;
                        $transient->response[$this->plugin_slug] = $transient_obj;
                }
                return $transient;
        }

        public function check_info($flase, $action, $arg) {
                if($arg->slug === $this->plugin_slug) {
                        $plugin_obj = new stdClass();
                        $plugin_obj->slug = $this->plugin_basename;
                        $plugin_obj->plugin_name = $this->plugin_slug;
                        $plugin_obj->download_link = $this->plugin_download_link;
                        $plugin_obj->new_version = $this->get_remote_version();
                        return $plugin_obj;
                }
                return false;
        }

        public function get_remote_version() {
                $version_check_url = $this->gitlab_baseurl.
                        $this->gitlab_project_id.
                        '/repository/tags?private_token='.
                        $this->token;
                if($result = $this->fetch_from_gitlab($version_check_url)) {
                        if(empty($result) || !is_object($result[0]) || !isset($result[0]->name)) {
                                return false;
                        }
                        $version = $result[0]->name;
                        // Version must have format "v2.31"
                        if(substr($version, 0, 1) !== 'v') {
                                return false;
                        }
                        $version = str_replace('v', '', $version);
                        return $version;
                }
        }

        public function fetch_from_gitlab($url) {
                $json = wp_remote_get($url);
                if(!is_wp_error($json) || wp_remote_retrive_response_code($json) === 200) {
                        $result = json_decode($json['body']);
                        return $result;
                } else {
                        return false;
                }
        }

        public function allow_local_ips($allow, $host, $url) {
                if($host == 'gitlab.elikirk.com' ) {
                        $allow = true;
                        return $allow;
                }
        }
}