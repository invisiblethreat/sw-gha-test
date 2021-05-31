
<?php
/*
 * Requires Facebook SDK and twitter0auth installed in lib directory in theme folder
 * Requires creation of Facebook developer app and Twitter developer app
 */
use Facebook\Facebook;
use Facebook\FacebookSession;
use Facebook\FacebookRequest;
use Facebook\GraphUser;
use Facebook\FacebookRequestException;

use Abraham\TwitterOAuth\TwitterOAuth;
use Abraham\TwitterOAuth\TwitterOAuthException;

use LinkedIn\LinkedIn;

function ekr_fetch_social() {
        $lib_dir = get_template_directory().'/lib';

        if(!file_exists(EKR_ACF_UPLOADS_DIR)) {
                mkdir(EKR_ACF_UPLOADS_DIR);
        }
    $cache_file = EKR_ACF_UPLOADS_DIR.'social.php';

        $error = false;

    // Check to see if cache file exits and is older than one day
    // if(false) {
    if(file_exists($cache_file) && ((time() - filemtime($cache_file)) <= 60*60*24)) {
        $social_posts = unserialize(file_get_contents($cache_file));
    } else {
        define('FACEBOOK_SDK_V4_SRC_DIR', $lib_dir.'/php-graph-sdk-5.0.0/src/Facebook/');
        require_once($lib_dir.'/php-graph-sdk-5.0.0/src/Facebook/autoload.php');
        require_once($lib_dir.'/twitteroauth/autoloader.php');
                require_once($lib_dir.'/LinkedIn/LinkedIn.php');

        $facebook_app_id = '267655880386087';
        $facebook_app_secret = 'fad69f027c6fc74a1b7e5b7ec6dd35a6';
        $facebook_access_token = $facebook_app_id.'|'.$facebook_app_secret;
        $facebook_feed_id = '115485045141584';
        $facebook_feed_name = 'businessutah';

        $twitter_consumer_key = 'fDENjxGACzLTWfSmxZEhpQB1l';
        $twitter_consumer_secret = '5NlIBypgSCf28dCkCdwRoIy50EOvcbr4iTb7g2MwYtoKEtRmTC';
        $twitter_access_token = '2485597574-OuwAhSFHbnRCh2MEHyx5JI29sJtDwhmW245Euqx';
        $twitter_access_secret = 'x0QHeMoSgCpHYZALPbvlWxcPV4cARFSQ2DAEUTgtMr6k8';
        $twitter_feed_name = 'businessutah';

                $linkedin_api_key = '860c086brhem15';
                $linkedin_api_secret = 'IBhuBgWfvF8ZmZJW';
                $linkedin_callback = 'https://business.utah.gov';
                $linkedin_company_id = '3357569';


        $social_posts = array();

        try {
                        // Facebook API
            $fb = new Facebook(array(
                'app_id' => $facebook_app_id,
                'app_secret' => $facebook_app_secret,
                'default_graph_version' => 'v2.5'
            ));
            $fb->setDefaultAccessToken($facebook_access_token);
            $response = $fb->get("/{$facebook_feed_id}/posts?fields=picture,message,created_time,likes,shares");
            $graph_edge = $response->getGraphEdge();
            foreach($graph_edge as $graph_node) {
                $created_time = $graph_node->getField('created_time');
                $timestamp = $created_time->getTimestamp();
                $date = date('F j, Y', $timestamp);
                $id = substr($graph_node->getField('id'), strpos($graph_node->getField('id'), '_') + 0);
                $picture = ($graph_node->getField('picture')) ?
                    $graph_node->getField('picture') : '';
                $message = ($graph_node->getField('message')) ?
                    $graph_node->getField('message') : '';
                // Replace urls with links
                $message = preg_replace(
                    '/(http[s]{0,1}\:\/\/\S{4,})\s{0,}/ims',
                    '<a href="$1" target="_blank">$1</a> ',
                    $message
                );
                $likes = count($graph_node->getField('likes'));
                $shares = ($graph_node->getField('shares')) ?
                    $graph_node->getField('shares')->getField('count') : 0;
                $link = 'https://www.facebook.com/'.$facebook_feed_name.'/posts/'.$id;
                $social_posts[$timestamp] = array(
                    'type' => 'facebook',
                    'date' => $date,
                    'image' => $picture,
                    'text' => $message,
                    'link' => $link,
                    'shares' => $shares,
                    'likes' => $likes
                );
            }

                        /*
            // Twitter API
            $connection = new TwitterOAuth(
                $twitter_consumer_key,
                $twitter_consumer_secret,
                $twitter_access_token,
                $twitter_access_secret
            );
            $tweets = $connection->get('statuses/user_timeline', array(
                'screen_name' => $twitter_feed_name,
                'count' => 25
            ));
            foreach($tweets as $tweet) {
                $timestamp = strtotime($tweet->created_at);
                $date = date('F j, Y', $timestamp);
                $message = $tweet->text;
                // Replace urls with links
                $message = preg_replace(
                    '/(http[s]{0,1}\:\/\/\S{4,})\s{0,}/ims',
                    '<a href="$1" target="_blank">$1</a> ',
                    $message
                );
                $social_posts[$timestamp] = array(
                    'type' => 'twitter',
                    'date' => $date,
                    'image' => false,
                    'text' => $message,
                    'link' => 'https://twitter.com/'.$twitter_feed_name.'/status/'.$tweet->id,
                    'shares' => $tweet->retweeted,
                    'likes' => $tweet->favorited
                );
            }
                        */

            krsort($social_posts);
            $fp = fopen($cache_file, 'w');
            fwrite($fp, serialize($social_posts));
            fclose($fp);
        } catch (TwitterOAuthException $e) {
            $error = 'Error in fetching content, please try again later: '. $e->getMessage();
        } catch (FacebookRequestException $e) {
            $error = 'Error in fetching content, please try again later: '. $e->getMessage();
        } catch (\Exception $e) {
            $error = 'Error in fetching content, please try again later: '. $e->getMessage();
        }
    }
    if($error) {
        throw new Exception($error);
    } else {
        return $social_posts;
    }
}
