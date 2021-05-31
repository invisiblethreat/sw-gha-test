//Shamelessly ripped off from - https://riptutorial.com/rust/example/4404/a-simple-tcp-client-and-server-application--echo
use std::net::{TcpStream};
use std::io::{Read, Write};
use std::str::from_utf8;

#[derive(Debug)]
pub struct Payload{
    action: String,
    argument: String
}

impl Payload{
    pub fn convert_to_bytes(&self) -> Vec<u8> {
        let mut buf: Vec<u8> = Vec::new();
        let action_byte = &self.action.clone().into_bytes();
        let argument_byte = &self.argument.clone().into_bytes();
        buf.append(&mut action_byte.clone());
        buf.append(&mut argument_byte.clone());
        return buf;
    }
}



fn main() {
    //match TcpStream::connect("10.16.186.25:9999") {
    let payload = Payload{
        action: "IIS".to_string(),
        argument: "STOP".to_string()
    };

    match TcpStream::connect("localhost:9999") {
        Ok(mut stream) => {
            println!("Successfully connected to server in port 9999");
            
            let vec_array:Vec<u8> = payload.convert_to_bytes();
            
            stream.write(&vec_array.clone()).unwrap();
            println!("Sent Message, awaiting reply...");

            let mut data = [0 as u8; 6]; // using 6 byte buffer
            match stream.read_exact(&mut data) {
                Ok(_) => {
                    
                        let text = from_utf8(&data).unwrap();
                        println!("Unexpected reply: {}", text);
                    },
                Err(e) => {
                    println!("Failed to receive data: {}", e);
                }
            }
        },
        Err(e) => {
            println!("Failed to connect: {}", e);
        }
    }
    println!("Terminated.");
}