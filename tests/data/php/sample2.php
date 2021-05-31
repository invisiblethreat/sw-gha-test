<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Index extends CI_Controller {

	public function __construct()
	{
	        parent::__construct();
	        $this->load->model('event_model');
			#FCPATH   -> '/'
			#BASEPATH -> '/system/'
			#APPPATH  -> '/application/'
	}

	public function index()
	{
		$data['show_left_panel_cart'] 	= 'TRUE';
		$data['current_view'] 			= 'HOME';

		$data['home_page_event_list'] 	= $this->event_model->get_event_list ('home');
		
		$this->load->view('templates/header', $data);
		$this->load->view('home', $data);
		$this->load->view('templates/footer', $data);
	}

	public function viewcart() {


		$data['event'] 				= $cart_event = $this->session->userdata('cart_event');
		$data['event_seats'] 		= $this->event_model->get_event_seats($data['event']['id']);


		$data["cart_session"] = $this->session->userdata('cart_session');
		$data["cart_additional_session"] = $this->session->userdata('cart_additional_session');
		$data["cart_captcha_session"] = $this->session->userdata('cart_captcha_session'); 
		$data["cart_user_session"] =  $this->session->userdata('cart_user_session');

		$data["cart_captcha_time_difference"] = strtotime(date("Y-m-d H:i:s")) - strtotime($data["cart_captcha_session"]['g-recaptcha-date-time']);
		$data["cart_captcha_time_remaining"]  =	$this->config->item('cart_time_out') - $data["cart_captcha_time_difference"];

		//$data['event_additional_charity'] 	= intval($this->config->item('additional_charity')) > 0 ? $this->config->item('additional_charity') : 0;

		if ( intval($data["cart_captcha_time_remaining"]) < 0 ) {
			$this->session->unset_userdata('cart_session');
			$this->session->unset_userdata('cart_additional_session');
			$this->session->unset_userdata('cart_captcha_session');
			$this->session->unset_userdata('cart_user_session');
		}


		if ( sizeof($data["cart_session"]) > sizeof($data["cart_additional_session"]) ) {
			// todo
		}else{
			redirect(base_url());
		}


		$array = array();
		foreach($data['event_seats']  as $k=>$row) {
			$occupied_seat_numbers = $this->event_model->get_event_seats_booked ($row['event_id'], $row['ticket_class_id']);
			$data['event_seats'][$k]['occupied_seat_numbers'] = $occupied_seat_numbers;
			$missing_seat_numbers  = $this->event_model->get_event_missing_seats($row['event_id'], $row['ticket_class_id']);
			$data['event_seats'][$k]['missing_seat_numbers']  = $missing_seat_numbers;
		}


		$data["additional_charges_view"]	=	"R"; // Review Cart
		$data["order_review_view"]	=	$this->load->view('cart/order_review', $data, true);
		  
		$this->load->view('templates/header', $data);
		$this->load->view('cart/cart_details', $data);
		$this->load->view('templates/footer', $data);
	}

	public function billing() {

		$data["cart_session"] = $this->session->userdata('cart_session'); 
		$data["cart_additional_session"] = $this->session->userdata('cart_additional_session');
		$data["cart_captcha_session"] = $this->session->userdata('cart_captcha_session'); 


		$data["cart_captcha_time_difference"] = strtotime(date("Y-m-d H:i:s")) - strtotime($data["cart_captcha_session"]['g-recaptcha-date-time']);
		$data["cart_captcha_time_remaining"]  =	$this->config->item('cart_time_out') - $data["cart_captcha_time_difference"];

		if ( intval($data["cart_captcha_time_remaining"]) < 0 ) {
			$this->session->unset_userdata('cart_session');
			$this->session->unset_userdata('cart_additional_session');
			$this->session->unset_userdata('cart_captcha_session');
			$this->session->unset_userdata('cart_user_session');
		}


		if ( sizeof($data["cart_session"]) > sizeof($data["cart_additional_session"]) ) {
			// todo
		}else{
			redirect(base_url());
		}

		/* Set Additional Amount */
		$cart_user_session =  $this->session->userdata('cart_user_session');
		if (  $this->input->post('additional-charity')  ) {
			$cart_user_session["additonal_details"] = array(
					'charity_amount' =>  intval($this->config->item('additional_charity')) > 0 ? $this->config->item('additional_charity') : 0
				);
		}else{
			unset($cart_user_session["additonal_details"]);
		}
		$this->session->set_userdata('cart_user_session', $cart_user_session);


		$data["cart_user_session"] 	= $cart_user_session; 


		$data['event'] 				= $cart_event = $this->session->userdata('cart_event');
		$data['event_seats'] 		= $this->event_model->get_event_seats($data['event']['id']);

		$array = array();
		foreach($data['event_seats']  as $k=>$row) {
			$occupied_seat_numbers = $this->event_model->get_event_seats_booked ($row['event_id'], $row['ticket_class_id']);
			$data['event_seats'][$k]['occupied_seat_numbers'] = $occupied_seat_numbers;
			$missing_seat_numbers  = $this->event_model->get_event_missing_seats($row['event_id'], $row['ticket_class_id']);
			$data['event_seats'][$k]['missing_seat_numbers']  = $missing_seat_numbers;
		}	

		$data["additional_charges_view"]	=	"B"; // Billing
		$data["order_review_view"]	=	$this->load->view('cart/order_review', $data, true);	 


		$this->load->view('templates/header', $data);
		$this->load->view('cart/billing_info', $data);
		$this->load->view('templates/footer', $data);

	}

	public function order() {

		$temp_cart_session = $data["cart_session"] = $this->session->userdata('cart_session'); 
		$temp_cart_additional_session = $data["cart_additional_session"] = $this->session->userdata('cart_additional_session');

		$data["cart_captcha_session"] 	= $this->session->userdata('cart_captcha_session');
		

		$data["cart_captcha_time_difference"] = strtotime(date("Y-m-d H:i:s")) - strtotime($data["cart_captcha_session"]['g-recaptcha-date-time']);
		$data["cart_captcha_time_remaining"]  =	$this->config->item('cart_time_out') - $data["cart_captcha_time_difference"];

		if ( intval($data["cart_captcha_time_remaining"]) < 0 ) {
			$this->session->unset_userdata('cart_session');
			$this->session->unset_userdata('cart_additional_session');
			$this->session->unset_userdata('cart_captcha_session');
			$this->session->unset_userdata('cart_user_session');
		}



		if ( sizeof($data["cart_session"]) > sizeof($data["cart_additional_session"]) ) {
			// todo
		}else{
			redirect(base_url());
		}



		$data["form_action"]	=	(($this->config->item('b_bpdq_testmode')) ? $this->config->item('b_bpdq_testurl') : $this->config->item('b_bpdq_productionurl'));


		/* Coupon Details */
		$this->load->model('coupon_model');
		$coupon_details  = $this->coupon_model->get_coupon_by_code($this->input->post('customer_promo_code'));
		$coupon_type  = "";
		$coupon_value = "";

		if ( isset($coupon_details) && isset($coupon_details["coupon_type"])  ) {
			$data["coupon_details"]["coupon_type"] = $coupon_type  = $coupon_details["coupon_type"];
			$data["coupon_details"]["coupon_value"] = $coupon_value = $coupon_details["coupon_value"];
			$data["coupon_details"]["coupon_code"] = $coupon_code = $coupon_details["coupon_code"];
			if ( $coupon_type == "FREE" ) {
				$data["form_action"]	=	 base_url() . "index.php/index/handlePlaceOrder"; 
			}
		}
		/* Coupon Details */
		
		
		$cart_user_session 		=   $this->session->userdata('cart_user_session');


		$additonal_details_charity_amount = 0; 
		if( isset($cart_user_session) && isset($cart_user_session["additonal_details"]) ) { 
			 $additonal_details_charity_amount = $cart_user_session["additonal_details"]["charity_amount"];
		}
		

		$cart_user_session["billing_details"] = array(
													'first_name' => $this->input->post('first_name'),
													'last_name' => $this->input->post('last_name'),
													'email' => $this->input->post('email'),
													'address' => $this->input->post('address'),
													'contact_number' => $this->input->post('contact_number'),
													'area' => $this->input->post('area'),
													'city' => $this->input->post('city'),
													'post_code' => $this->input->post('post_code'),
													'mobile_number' => $this->input->post('mobile_number')
											); 

		$cart_user_session["user_details"] = array(
													'customer_first_name' => $this->input->post('customer_first_name'),
													'customer_last_name' => $this->input->post('customer_last_name'),
													'customer_email' => $this->input->post('customer_email'),
													'customer_promo_code' => $this->input->post('customer_promo_code'),
													'customer_add_donation' => $additonal_details_charity_amount
											); 


		$this->session->set_userdata('cart_user_session', $cart_user_session);
		$temp_cart_user_session = $data["cart_user_session"] = $this->session->userdata('cart_user_session');


		$total_price = 0;
		$cart_session = $data["cart_session"];
		foreach ($cart_session as $k=>$cart_session_item):
			$selected_tables = sizeof($cart_session_item["selected_tables"]);
			$table_count = 0;
			$seat_count  = 0;
			$unit_price  = 0;

			if ( $cart_session_item["ticket_section_name"] == "table" ) {
				$table_count = $selected_tables;
			}else{
				for ($I=0; $I<$selected_tables; $I++ ) {
					if ( $cart_session_item["selected_tables"][$I]["seat_quantity"] == $cart_session_item["table_seat_count"] && $cart_session_item["event_ticket"] == "Y"  ) {
						$table_count = $table_count + 1;
					}else{
						$seat_count = $seat_count + intval( $cart_session_item["selected_tables"][$I]["seat_quantity"] );
					}   
				}
			}

			if ( $table_count > 0) {
				$unit_price = $table_count * ($cart_session_item["table_price"]);   
			}
			if ( $seat_count > 0) {
				$unit_price = $unit_price + ($seat_count * ($cart_session_item["unit_min_purchase"] * $cart_session_item["unit_price"]));   
			}
		  	$total_price = $total_price + $unit_price;
		endforeach;

		

		$sub_total_price = $total_price + $additonal_details_charity_amount;   /* todo donations */


		$data['event'] 		= 	 $cart_event = $this->session->userdata('cart_event');


		// additional charge calculation
		$event_additional_charges = $data['event']["event_additional_charges"];
		$event_additional_charge_total = 0;
		$additional_percentage_arr = array();
		for ($I=0; $I<sizeof($event_additional_charges); $I++ ) { 
			if ( $event_additional_charges[$I]["additional_charge_type"] == 'F' ) {
				$event_additional_charge_total =  $event_additional_charge_total + $event_additional_charges[$I]["additional_charge"]; 
			}else if ( $event_additional_charges[$I]["additional_charge_type"] == 'P' ) {
				$additional_percentage_arr[sizeof($additional_percentage_arr)] = $event_additional_charges[$I];
			}
		}

		$sub_total_price = $sub_total_price + $event_additional_charge_total; /* todo additional flat charge */


		$percentage_charge_total = 0;
		for ($I=0; $I<sizeof($additional_percentage_arr); $I++ ) {
			$percentage_charges = round(($sub_total_price * $additional_percentage_arr[$I]["additional_charge"]) / 100,2);                               
			$percentage_charge_total = $percentage_charge_total + $percentage_charges;
		}

		$sub_total_price = $sub_total_price + $percentage_charge_total; /* todo additional percentage  charge */
		//



		// CART UNIQUE ID and session cart to tables 
		$this->load->model('cart_model');
		$cart_items = $this->cart_model->get_item();

		$cart_data = array(
			'cart_session' => serialize($temp_cart_session) ,
			'cart_additional_session' => serialize($temp_cart_additional_session),
			'cart_user_session' => serialize($temp_cart_user_session),
			'price' => $total_price,
			'total_price' => $sub_total_price
		);

	
		if ( $cart_items["item_count"] == 1 ) {
			$cart_data["id"]	=	$cart_items["id"];
			$UNIQ_CART_ID 			=   $this->cart_model->update_item($cart_data);
		}else{
			if ( $cart_items["item_count"] > 1 ) {
				$this->cart_model->delete_item();
			}
			$UNIQ_CART_ID = $this->cart_model->add_item($cart_data);
		}
		


		//- Customer/Order Details - //
		$data["order_post_details"]["UserTitle"]    		=	"";
		$data["order_post_details"]["UserFirstname"]       	=	$data["cart_user_session"]["billing_details"]["first_name"];
		$data["order_post_details"]["UserSurname"]   		=	$data["cart_user_session"]["billing_details"]["last_name"];
		$data["order_post_details"]["BillHouseNumber"]  	= 	$data["cart_user_session"]["billing_details"]["address"];
		$data["order_post_details"]["Ad1"] 					= 	$data["cart_user_session"]["billing_details"]["address"];
		$data["order_post_details"]["Ad2"] 					= 	$data["cart_user_session"]["billing_details"]["area"];
		$data["order_post_details"]["BillTown"] 			= 	$data["cart_user_session"]["billing_details"]["city"];
		$data["order_post_details"]["BillCountry"]   		= 	$this->config->item('b_bpdq_billing_country'); 
		$data["order_post_details"]["Pcde"]  				= 	$data["cart_user_session"]["billing_details"]["post_code"];
		$data["order_post_details"]["ContactTel"] 			= 	$data["cart_user_session"]["billing_details"]["contact_number"];
		$data["order_post_details"]["ShopperEmail"] 		= 	$data["cart_user_session"]["billing_details"]["email"];
		$data["order_post_details"]["ShopperLocale"] 		=	$this->config->item('b_bpdq_language');
		$data["order_post_details"]["CurrencyCode"] 		=	$this->config->item('b_bpdq_currency');

		$data["order_post_details"]["Addressline1n2"] 		=   $data["order_post_details"]["Ad1"] . " " . $data["order_post_details"]["Ad2"];
		$data["order_post_details"]["CustomerName"]  		=   $data["order_post_details"]["UserTitle"] . " " . $data["order_post_details"]["UserFirstname"]  . " " . $data["order_post_details"]["UserSurname"]; 


		$data['sub_total_price']							=	 $sub_total_price * 100; // this is 1 pound (100p)



		$data["order_post_details"]["PaymentAmount"] 	 	= 	$data['sub_total_price'];    
		$data["order_post_details"]["OrderDataRaw"]  		=  	$data['event']['title'];    // order description
		$data["order_post_details"]["OrderID"]  			= 	$this->config->item('b_bpdq_cart_order_key') . $UNIQ_CART_ID;  // Order - Cart Id - needs to be unique
        


        //- integration user details - //
        $data["order_post_details"]["PW"] 					=	$this->config->item('b_bpdq_sha_in_pass_phrase');
        $data["order_post_details"]["PSPID"]  				= 	$this->config->item('b_bpdq_PSPID');



        //- payment design options - //
        $data["order_post_details"]["TXTCOLOR"] 			=	"#005588";
        $data["order_post_details"]["TBLTXTCOLOR"] 			=	"#005588";
        $data["order_post_details"]["FONTTYPE"] 			=	"Helvetica, Arial";
        $data["order_post_details"]["BUTTONTXTCOLOR"]  		=	"#005588";
        $data["order_post_details"]["BGCOLOR"]  			= 	"#d1ecf3";
         $data["order_post_details"]["TBLBGCOLOR"]   		= 	"#ffffff"; 
        $data["order_post_details"]["BUTTONBGCOLOR"]    	= 	"#cccccc";
        $data["order_post_details"]["TITLE"]  				= 	"Merchant Shop - Secure Payment Page";
        $data["order_post_details"]["LOGO"]  				= 	base_url() . "assets/images/logo.png";
        $data["order_post_details"]["PMLISTTYPE"] 			=	$this->config->item('b_bpdq_PMLISTTYPE');;


        
        //= create string to hash (digest) using values of options/details above
        $data["order_post_details"]["DigestivePlain"]  =
        "AMOUNT=" . $data["order_post_details"]["PaymentAmount"] . $data["order_post_details"]["PW"] .
        "BGCOLOR=" . $data["order_post_details"]["BGCOLOR"] . $data["order_post_details"]["PW"] .
        "BUTTONBGCOLOR=" . $data["order_post_details"]["BUTTONBGCOLOR"] . $data["order_post_details"]["PW"] .
        "BUTTONTXTCOLOR=" . $data["order_post_details"]["BUTTONTXTCOLOR"] . $data["order_post_details"]["PW"] .
        "CN=" . $data["order_post_details"]["CustomerName"]  . $data["order_post_details"]["PW"] . 
        "COM=" . $data["order_post_details"]["OrderDataRaw"]  . $data["order_post_details"]["PW"] . 
        "CURRENCY=" . $data["order_post_details"]["CurrencyCode"] . $data["order_post_details"]["PW"] .
        "EMAIL=" . $data["order_post_details"]["ShopperEmail"] . $data["order_post_details"]["PW"] .
        "FONTTYPE=" . $data["order_post_details"]["FONTTYPE"] . $data["order_post_details"]["PW"] .
        "LANGUAGE=" . $data["order_post_details"]["ShopperLocale"] . $data["order_post_details"]["PW"] .
        "LOGO=" .$data["order_post_details"]["LOGO"] . $data["order_post_details"]["PW"] .
        "ORDERID=" . $data["order_post_details"]["OrderID"] . $data["order_post_details"]["PW"] .
        "OWNERADDRESS=" . $data["order_post_details"]["Addressline1n2"] . $data["order_post_details"]["PW"] .
        "OWNERCTY=" . $data["order_post_details"]["BillCountry"] . $data["order_post_details"]["PW"] .
        "OWNERTELNO=" . $data["order_post_details"]["ContactTel"] . $data["order_post_details"]["PW"] . 
        "OWNERTOWN=" . $data["order_post_details"]["BillTown"] . $data["order_post_details"]["PW"] .
        "OWNERZIP=" . $data["order_post_details"]["Pcde"] . $data["order_post_details"]["PW"] .
        "PMLISTTYPE=". $data["order_post_details"]["PMLISTTYPE"] . $data["order_post_details"]["PW"] .
        "PSPID=" . $data["order_post_details"]["PSPID"] . $data["order_post_details"]["PW"] .
        "TBLBGCOLOR=" . $data["order_post_details"]["TBLBGCOLOR"] . $data["order_post_details"]["PW"] .
        "TBLTXTCOLOR=" . $data["order_post_details"]["TBLTXTCOLOR"] . $data["order_post_details"]["PW"] .
        "TITLE=" . $data["order_post_details"]["TITLE"] . $data["order_post_details"]["PW"] .
        "TXTCOLOR=" . $data["order_post_details"]["TXTCOLOR"] . $data["order_post_details"]["PW"] .
        "";
        
        //=SHA encrypt the string=//
        $data["order_post_details"]["strHashedString_plain"] = strtoupper(sha1($data["order_post_details"]["DigestivePlain"]));
        
        //-Form to submit order details along with ecrypted string of order details 
		$data['event_seats'] 		= $this->event_model->get_event_seats($data['event']['id']);
		$array = array();
		foreach($data['event_seats']  as $k=>$row) {
			$occupied_seat_numbers = $this->event_model->get_event_seats_booked ($row['event_id'], $row['ticket_class_id']);
			$data['event_seats'][$k]['occupied_seat_numbers'] = $occupied_seat_numbers;
			$missing_seat_numbers  = $this->event_model->get_event_missing_seats($row['event_id'], $row['ticket_class_id']);
			$data['event_seats'][$k]['missing_seat_numbers']  = $missing_seat_numbers;
		}		

		$data["additional_charges_view"]	=	"P"; // Payment Order
		$data["order_review_view"]	=	$this->load->view('cart/order_review', $data, true);  


		$this->load->view('templates/header', $data);
		$this->load->view('cart/place_order', $data);
		$this->load->view('templates/footer', $data);

	}

	public function thankyou() {

		$this->session->unset_userdata('cart_session');
		$this->session->unset_userdata('cart_additional_session');
		$this->session->unset_userdata('cart_captcha_session');
		$this->session->unset_userdata('cart_user_session');

		$data['event'] 				= 	 array();
		$data['cart_session'] 		= 	 array();

		if ( $this->input->get('orderID') ) {
			$cart_id 		= explode("_",$this->input->get('orderID'));
			$query 			= $this->db->get_where('cart_master', array('id' => $cart_id[1]));
			$cart_results 	= $query->row_array();

			$data['cart_results']  = $cart_results;
			$data['cart_session']  = unserialize($cart_results["cart_session"]);

			foreach ($data['cart_session'] as $k=>$cart_session_item) {
				$data['event_id'] = $cart_session_item["event_id"];
			}

			if ($data["event_id"] > 0 ) {
				$this->load->model('event_model');
				$data['event'] = $this->event_model->get_event(FALSE,$data["event_id"]);
			}
		}else{
			redirect(base_url());	
		}

		$this->load->view('templates/header', $data);
		$this->load->view('cart/thank_you', $data);
		$this->load->view('templates/footer', $data);
	}



	public function ordercancel() {


		$this->session->unset_userdata('cart_session');
		$this->session->unset_userdata('cart_additional_session');
		$this->session->unset_userdata('cart_captcha_session');
		$this->session->unset_userdata('cart_user_session');


		$data['event'] 				= 	 array();
		$data['cart_session'] 		= 	 array();

		if ( $this->input->get('orderID') ) {
			$cart_id 		= explode("_",$this->input->get('orderID'));
			$query 			= $this->db->get_where('cart_master', array('id' => $cart_id[1]));
			$cart_results 	= $query->row_array();

			$data['cart_results']  = $cart_results;
			$data['cart_session']  = unserialize($cart_results["cart_session"]);

			foreach ($data['cart_session'] as $k=>$cart_session_item) {
			$data['event_id'] = $cart_session_item["event_id"];
			}

			if ($data["event_id"] > 0 ) {
			$this->load->model('event_model');
			$data['event'] = $this->event_model->get_event(FALSE,$data["event_id"]);
			}
		}else{
			redirect(base_url());	
		}

		$this->load->view('templates/header', $data);
		$this->load->view('cart/order_cancel', $data);
		$this->load->view('templates/footer', $data);
	}


	function handlePlaceOrder() {
		$response 	 = $this->input->post(); // $this->input->post();
		$updateOrder = true;

		if(!isset($response['ORDERID'])){
			return false;
		}

		$cartRef = $response['ORDERID'];
		$response['STATUS'] = "5";
		$payId   = "COUPON_" . $response['coupon_code'] . "_" . time();

		$this->paymentSuccess($cartRef, $payId, $response);

		redirect(base_url() . "index.php/index/thankyou?orderID=" . $cartRef);
	}


	/*
	Handles Barclaycard respose (GET or POST)
	If updateOrder is set to true, paymentSuccess and paymentFailed are called

	Response contains:
		ORDERID Your order reference
		AMOUNT Order amount (not multiplied by 100)
		CURRENCY Currency of the order
		PM Payment method
		ACCEPTANCE Acceptance code returned by acquirer
		STATUS Transaction status
		CARDNO Masked card number
		PAYID Payment reference in our system
		NCERROR Error code
		BRAND Card brand (our system derives it from the card number) or similar
		information for other payment methods.
		SHASIGN SHA signature composed by our system, if SHA-1-OUT is configured by you.
	*/
	function handleResponse(){

		$response 	 = $this->input->post(); // $this->input->post();
		$updateOrder = true;

		if(!isset($response['orderID'])){
			return false;
		}

		if(!isset($response['STATUS'])){
			return false;
		}
		
		$cartRef = $response['orderID'];
		$status  = $response['STATUS'];
		$payId   = $response['PAYID'];
		
		if($status == '5' || $status == '9'){			
			if($updateOrder){
				$this->paymentSuccess($cartRef, $payId, $response);
			}
			return true;
		}
		
		$this->mFailReason = "Unknown payment error occurred";
		$this->mWarning = false;

		switch($status){
			case "0":
				"Some required details were missing - " . $response['NCERROR'];
			break;
			case "1":
			case "6":
			case "64":
				"You cancelled the transaction";
			break;
			case "84":
			case "93":
				$this->mFailReason = "Payment refused";
			break;
			case "2":
			case "52":
				$this->mFailReason = "Unable to authorise";
			break;
			case "4":
			case "9":
			case "40":
			case "91":
			case "50":
			case "51":
			case "52":
			case "59":
			case "92":
			case "95":
			case "99":
				$this->mWarning = true;
				$this->mFailReason = "There was a delay processing this transaction. We'll update you when your order is successful, or be in contact if there is an issue with the payment";
				//$this->sendPendingPaymentEmail($cartRef);
			break;
			case "93":
				$this->mFailReason = "Barclaycard technical issue - please retry your payment at a later date";
			break;
		}
		
		if($updateOrder){
			$this->paymentSuccess($cartRef,$payId,$response);
		}
		
		return false;
		
	}


	/*
		Payment success, overide with your code to handle success
		This is only called if the handleResponse method is called with updateOrder set to true
	*/
	public function paymentSuccess($cartRef, $payID,$response){

		/* Check if duplicate notification */
		$this->load->model('cart_model');
		$notify_exist = $this->cart_model->checkDuplicateNotification($payID,$cartRef);

		if( $notify_exist > 0 ) {
			return;	
		}

		$data = array(
			'order_id' => $cartRef,
			'pay_id' => $payID ,
			'pay_status' => $response['STATUS'],
			'pay_date' => date("Y-m-d H:i:s"),
			'pay_response' => serialize($response)
		);

		$this->db->insert('test_notify', $data); 
		

		if ( $response['STATUS'] == "5" || $response['STATUS'] == "9") {
			// good for order placement
		}else{
			return;
		}

		/* Get Records from Cart Master */

		$cart_id = explode("_",$cartRef);

		$query 			= $this->db->get_where('cart_master', array('id' => $cart_id[1]));
		$cart_results 	= $query->row_array();

		$cart_session 				= unserialize($cart_results["cart_session"]);
		$cart_additional_session 	= unserialize($cart_results["cart_additional_session"]);
		$cart_user_session 			= unserialize($cart_results["cart_user_session"]);


		/* Update Order master table */
		$data = array(
			'cart_id' => $cart_id[1],
			'pay_id' => $payID ,
			'pay_status' => $response['STATUS'],
			'first_name' => $cart_user_session["billing_details"]["first_name"],
			'last_name' => $cart_user_session["billing_details"]["last_name"],
			'email' => $cart_user_session["billing_details"]["email"],
			'contact_number' => $cart_user_session["billing_details"]["contact_number"],
			'address' => $cart_user_session["billing_details"]["address"],
			'area' => $cart_user_session["billing_details"]["area"],
			'city' => $cart_user_session["billing_details"]["city"],
			'post_code' => $cart_user_session["billing_details"]["post_code"],
			'mobile_number' => $cart_user_session["billing_details"]["mobile_number"],
			'total_amount' => $cart_results["total_price"],
			'date' => date("Y-m-d H:i:s"),
			'pay_response' =>serialize($response),
			'customer_first_name' => $cart_user_session["user_details"]["customer_first_name"],
			'customer_last_name' => $cart_user_session["user_details"]["customer_last_name"],
			'customer_email' => $cart_user_session["user_details"]["customer_email"],
			'customer_promo_code' => $cart_user_session["user_details"]["customer_promo_code"],
			'customer_add_donation' => $cart_user_session["user_details"]["customer_add_donation"]
		);

		$this->db->insert('order_master', $data); 

		$ORDER_ID = $this->db->insert_id();


		foreach ($cart_session as $k=>$cart_session_item) {
			$data = array(
				'order_id' => $ORDER_ID,
				'event_id' => $cart_session_item["event_id"],
				'ticket_section_id' => $cart_session_item["ticket_section_section_id"],
				'ticket_class_id' => $cart_session_item["ticket_class_id"]
			);
			$this->db->insert('order_event_details', $data);
	
			$unit_qty  = 0;
			$table_qty = sizeof($cart_session_item["selected_tables"]);
			if ( $cart_session_item["ticket_section_name"] == "table" ) {
					for ($I=0; $I<$table_qty; $I++ ) {
							for ( $J=1; $J<=10; $J++ ) {
							$data = array(
								'order_id' => $ORDER_ID,
								'event_id' => $cart_session_item["event_id"],
								'ticket_class_id' => $cart_session_item["ticket_class_id"],
								'table_number' => $cart_session_item["selected_tables"][$I]["table_number"],
								'seat_number' => $J
							);
							$this->db->insert('order_seat_details', $data);
							}
					}

			}else{
				for ($I=0; $I<$table_qty; $I++ ) {
							$seat_qty = $cart_session_item["selected_tables"][$I]["seat_quantity"];

							$this->db->select('max(seat_number) as current_seat_number');
							$this->db->from('order_seat_details');
							$this->db->where('event_id', $cart_session_item["event_id"]);
							$this->db->where('ticket_class_id', $cart_session_item["ticket_class_id"]);
							$this->db->where('table_number', $cart_session_item["selected_tables"][$I]["table_number"]);
							$query = $this->db->get();
							$row_array = $query->row_array();
							$starting_seat = $row_array["current_seat_number"] + 1;

							for ( $J=0; $J<$seat_qty; $J++ ) {
								$data = array(
									'order_id' => $ORDER_ID,
									'event_id' => $cart_session_item["event_id"],
									'ticket_class_id' => $cart_session_item["ticket_class_id"],
									'table_number' => $cart_session_item["selected_tables"][$I]["table_number"],
									'seat_number' => ($starting_seat + $J)
								);
								$this->db->insert('order_seat_details', $data);
							}
				}
			}

		}

		/* ORDER Confirmation Email */
		$this->load->model('event_model');
		$event_details = $this->event_model->get_event(FALSE,$data["event_id"]);
		$email_content = $this->load->view('cart/order_confirmation', array('cart_session' => $cart_session,'cart_additional_session' => $cart_additional_session, 'cart_user_session' => $cart_user_session, 'event' => $event_details), true);
		$this->orderConfirmation (array('email_content'=>$email_content,'cart_user_session' => $cart_user_session));
	}


	/*
		Sends email to notification list if authorisation delay
	*/
	public function sendPendingPaymentEmail($cartRef){
		$msg = "A payment was unable to be processed and is waiting for feedback from Barclaycard.

Please check your Barclaycard account for payment for the order. If payment has been taken, please move the order to approved from your order retrieval area.

Order cart ref: {$cartRef}
";
		$mNotificationEmails = array($this->config->item('site_admin_email'));
		foreach($mNotificationEmails as $to){
			mail($to, 'Barclaycard - pending transaction', $msg);
		}	
	}


	public function orderConfirmation($data) {
		if ($data) {
			$to_email = trim($data["cart_user_session"]["billing_details"]["email"]);
			$cc_email = trim($data["cart_user_session"]["user_details"]["customer_email"]);
			$this->load->library('email');
			$this->email->clear();
			$config['mailtype'] = 'html';
			$this->email->initialize($config);

			$this->email->from($this->config->item('site_admin_email'), $this->config->item('site_admin_title'));
			if ( $to_email == $cc_email) {
				$this->email->to($to_email); 
			}else{
				$this->email->to(array($to_email,$cc_email)); 	
			}
			
			//$this->email->cc($cc_email); 
			$this->email->reply_to($this->config->item('site_admin_email'), $this->config->item('site_admin_title'));
			//$this->email->bcc($this->config->item('site_admin_email')); 
			$this->email->bcc(array('retheesh4u@gmail.com','dean@vtelevision.co.uk')); /* todo need to remove once development finished */

			$this->email->subject($this->config->item('site_order_email_title'));
			$this->email->message( $data["email_content"] );	
			$this->email->send();
			//echo $this->email->print_debugger();	
		}
		
    }




	public function cartDetailsDebug($cart_id = 0) {

		$cart_id    = ($this->input->get('cart_id')) ? $this->input->get('cart_id') : 0;

		if ( $cart_id < 1 ) {
			exit;
		}

		$query 			= $this->db->get_where('cart_master', array('id' => $cart_id));
		$cart_results 	= $query->row_array();

		$cart_session 				= unserialize($cart_results["cart_session"]);
		$cart_additional_session 	= unserialize($cart_results["cart_additional_session"]);
		$cart_user_session 			= unserialize($cart_results["cart_user_session"]);

		echo "<strong>CART SESSION</strong> <br/><br/>";
		echo "<pre>";
		print_r($cart_session);
		echo "</pre>";
		echo "<strong>CART ADDITIONAL SESSION</strong> <br/><br/>";
		echo "<pre>";
		print_r($cart_additional_session);
		echo "</pre>";
		echo "<strong>CART USER SESSION</strong> <br/><br/>";
		echo "<pre>";
		print_r($cart_user_session );
		echo "</pre>";

		exit;
	}


}