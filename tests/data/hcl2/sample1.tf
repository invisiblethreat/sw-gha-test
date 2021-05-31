variable "env" {
  type        = string
  description = "The environment to run the service in (e.g. master/staging/production)"
}

variable "business_unit" {
  type        = string
  description = "The business unit of the project (e.g. asdf/be/cir.)"
  default     = "asdf"
}

variable "namespace" {
  type        = string
  description = "The namspace of the project (e.g. cs/distribution.)"
  default     = "cs"
}

variable "name" {
  type        = string
  description = "The name of the service"
  default     = "whoisapi"
}

variable "short_name" {
  type        = string
  description = "The short name of the service"
  default     = "whois-api"
}

variable "region" {
  type    = string
  description = "Default Region for services"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID of ECS cluster hosting service"
}

variable "cluster_name" {
  type        = string
  description = "Name of ECS Cluster"
  default     = ""
}

variable "cluster_id" {
  type        = string
  description = "Id of ECS Cluster"
  default     = ""
}

variable "lb_listener_arn" {
  type        = string
  description = "The ARN of the AWS ALB Listener to attach to."
  default     = ""
}

variable "public_domain_name" {
  type        = string
  description = "The Public Domain Name to use."
  default     = ""
}

variable "route53_zone_id" {
  type        = string
  description = "The AWS Route53 Zone ID in which to create the DNS record, if a lb_listener_arn is provided."
  default     = ""
}

variable "service_discovery_namespace_id" {
  type        = string
  description = "The AWS Service Discovery Namespace ID to use for local service discovery."
  default     = ""
}

variable "public_subnet_ids" {
  type        = list
  description = "Public subnets of VPC"
  default     = []
}

variable "private_subnet_ids" {
  type        = list
  description = "Private subnets of VPC"
  default     = []
}

variable "memory_usage" {
  type =    map
  default = {
    "low" =    "256"
    "medium" = "512"
    "high" =   "1024"
  }
}

variable "whoisapi_service" {
  description = "whois API Service"
  type = object({
    security_groups = list(string)
    memory          = number
    cpu             = number
    ports           = list(number)
    desired_count   = number
    autoscaling     = bool
    depends_on      = list(any)
    containers = list(object({
      image_uri          = string
      image_tag          = string
      memory             = number
      cpu                = number
      ports              = list(number)
      ulimit_nofile_soft = number
      ulimit_nofile_hard = number
    }))
  })

  default = {
    security_groups = []
    memory          = 256
    cpu             = 0
    ports           = [8080]
    desired_count   = 1
    autoscaling     = false
    depends_on      = []
    containers = [
      {
        image_uri          = "" # Ideally we would not provide a default for this, as it's not optional, but we have to.
        image_tag          = "" # If omitted, will use the value for 'env'
        memory             = 256
        cpu                = 0    # The default, 0, means no reservation
        ports              = [8080] # Use port 0 to not map a port on this container.
        ulimit_nofile_soft = 102400
        ulimit_nofile_hard = 102400
      }
    ]
  }
}

variable "container_secrets" {
  type    = map
  default = {}
}

variable "errbit_host" {
  type = string
  default = "https://errbit.core.asdfasdf.io"
}

variable "api_url" {
  type = string
  default = "https://vapi.dev.asdfasdf.io"
}

variable "log_format" {
  type = string
  default = "json"
}