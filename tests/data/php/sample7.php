<?php
namespace EKR_ACF\Module;

class Map extends Module {
	public $name = 'Map';
	public $slug = 'map';
	public $module_name = 'module_map';

	public function __construct() {
		add_action('acf/init', array($this, 'register_custom_post_type_office'));
		add_action('wp_enqueue_scripts', array($this, 'enqueue_google_maps_api'));
	}

	public function register_custom_post_type_office() {
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

		// Add fields to Bio
		acf_add_local_field_group(array(
			'key' => 'office_fields',
			'title' => 'Office Fields',
			'fields' => array(
				array(
					'key' => 'office_photo',
					'name' => 'office_photo',
					'label' => 'Photo',
					'type' => 'tab'
				),
				array(
					'key' => 'office_image',
					'name' => 'office_image',
					'type' => 'image',
					'label' => 'Image'
				),
				array(
					'key' => 'office_contact_info',
					'name' => 'office_contact_info',
					'label' => 'Contact Info',
					'type' => 'tab'
				),
				array(
					'key' => 'office_address_1',
					'name' => 'office_address_1',
					'label' => 'Address 1',
					'type' => 'text'
				),
				array(
					'key' => 'office_address_2',
					'name' => 'office_address_2',
					'label' => 'Address 2',
					'type' => 'text'
				),
				array(
					'key' => 'office_phone',
					'name' => 'office_phone',
					'label' => 'Phone',
					'type' => 'text'
				),
				array(
					'key' => 'office_website_url',
					'name' => 'office_website_url',
					'label' => 'Website URL',
					'type' => 'text'
				),
				array(
					'key' => 'office_coordinates',
					'name' => 'office_coordinates',
					'label' => 'Coordinates',
					'type' => 'tab'
				),
				array(
					'key' => 'office_latitude',
					'name' => 'office_latitude',
					'label' => 'Latitude',
					'type' => 'text'
				),
				array(
					'key' => 'office_longitude',
					'name' => 'office_longitude',
					'label' => 'Longitude',
					'type' => 'text'
				)
			),
			'location' => array(
				array(
					array(
						'param' => 'post_type',
						'operator' => '==',
						'value' => 'office'
					)
				)
			),
			'hide_on_screen' => array(
				'the_content'
			)
		));
	}

	/**
	* enqueue_google_maps_api
	*
	* Used to load Google Maps API in Map module.
	* Placed here to avoid loading more than once.
	* The script's 'defer' and 'async' attributes are set via filters in theme's functions.php.
	* The ekrModules.mapData.init method is found in the Map module's scripts.js file.
	*/
	public function enqueue_google_maps_api() {
		$google_map_api = 'AIzaSyAUpCf0tw638uowKK7Gf-y3u27WCBHa31A';
		wp_enqueue_script(
			'googleapis',
			esc_url(add_query_arg(
				'key',
				$google_map_api.'&callback=ekrModules.mapData.init',
				'//maps.googleapis.com/maps/api/js'
			)),
			array(),
			null,
			true
		);
	}

	public function acf_definition() {
		return array(
			'key' => $this->module_name,
			'name' => $this->module_name,
			'label' => $this->name,
			'sub_fields' => array(
				array(
					'key' => 'module_map_heading',
					'name' => 'module_map_heading',
					'label' => 'Heading',
					'instructions' => 'Default is "Offices"',
					'type' => 'text'
				),
				array(
					'key' => 'module_map_locations',
					'name' => 'module_map_locations',
					'label' => 'Office Locations',
					'type' => 'relationship',
					'button_label' => 'Add office',
					'post_type' => 'office',
					'min' => 1
				)
			)
		);
	}
}
